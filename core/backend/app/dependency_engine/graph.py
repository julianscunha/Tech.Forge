"""
DependencyGraph — Fase 8.1 §6/§10/§22/§27
=============================================
Grafo módulo→módulo construído a partir das dependências declaradas em cada
manifest. Dependência de capability resolve para o(s) módulo(s) provider via
ServiceRegistry.find_capability() — não duplica a discovery da Fase 8.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.dependency_engine.models import TargetType
from app.dependency_engine.parser import DependencyParseError, DependencyParser


@dataclass
class Edge:
    source: str
    target: str
    kind:   str  # "module" | "capability"


@dataclass
class DependencyGraph:
    edges: list[Edge] = field(default_factory=list)

    @staticmethod
    def build(module_registry, service_registry) -> "DependencyGraph":
        edges: list[Edge] = []
        for entry in module_registry.all():
            raw = entry.manifest_raw.get("dependencies") or []
            try:
                deps = DependencyParser.parse(raw)
            except DependencyParseError:
                continue

            for dep in deps:
                if dep.target_type == TargetType.MODULE:
                    edges.append(Edge(entry.module_id, dep.target_id, "module"))
                else:
                    for provider in service_registry.find_capability(dep.target_id):
                        edges.append(Edge(entry.module_id, provider.module_id, "capability"))

        return DependencyGraph(edges=edges)

    def _adjacency(self) -> dict[str, list[str]]:
        adj: dict[str, list[str]] = {}
        for edge in self.edges:
            adj.setdefault(edge.source, []).append(edge.target)
            adj.setdefault(edge.target, [])
        return adj

    def detect_cycles(self) -> list[list[str]]:
        """DFS — retorna um ciclo (caminho completo, inclui o nó repetido no fim) por ciclo achado."""
        adj = self._adjacency()
        cycles: list[list[str]] = []
        visited: set[str] = set()

        def dfs(node: str, path: list[str], on_path: set[str]) -> None:
            path.append(node)
            on_path.add(node)
            for neighbor in adj.get(node, []):
                if neighbor in on_path:
                    start = path.index(neighbor)
                    cycles.append(path[start:] + [neighbor])
                elif neighbor not in visited:
                    dfs(neighbor, path, on_path)
            path.pop()
            on_path.discard(node)
            visited.add(node)

        for node in adj:
            if node not in visited:
                dfs(node, [], set())

        return cycles

    def topological_order(self) -> list[str]:
        """
        Ordem de ativação (§10): dependências antes de quem depende delas.
        Kahn sobre out-degree — aresta a->b significa "a depende de b", então
        b (sem dependências pendentes) deve ativar primeiro.
        """
        adj = self._adjacency()
        reverse: dict[str, list[str]] = {node: [] for node in adj}
        for node, targets in adj.items():
            for target in targets:
                reverse[target].append(node)

        out_degree = {node: len(targets) for node, targets in adj.items()}
        queue = [node for node, deg in out_degree.items() if deg == 0]
        order: list[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for dependent in reverse.get(node, []):
                out_degree[dependent] -= 1
                if out_degree[dependent] == 0:
                    queue.append(dependent)

        return order

    def export_mermaid(self) -> str:
        """flowchart TD — aresta rotulada module/capability, nós em ciclo destacados."""
        lines = ["flowchart TD"]
        for edge in self.edges:
            arrow = "-->" if edge.kind == "module" else "-.->"
            lines.append(f"    {edge.source} {arrow}|{edge.kind}| {edge.target}")

        cycle_nodes: set[str] = set()
        for cycle in self.detect_cycles():
            cycle_nodes.update(cycle)

        if cycle_nodes:
            lines.append("    classDef cycle stroke:#f00,stroke-width:2px")
            lines.append(f"    class {','.join(sorted(cycle_nodes))} cycle")

        return "\n".join(lines)
