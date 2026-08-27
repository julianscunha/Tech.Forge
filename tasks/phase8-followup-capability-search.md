# Follow-up da Fase 8 — Busca por capability/export (discovery em escala)

> **Status: implementado.** `ServiceRegistry.search()` +
> `GET /api/v1/services?q=` + `techforge services search` — ver
> `tasks/phase-08-report.md`. Não é uma fase nova nem parte da Fase 8.1
> (Dependency Governance, já reservada pela spec).

## Problema

Hoje (`GET /api/v1/services`, `techforge services list`) só existe
**listagem completa** — sem filtro. Com poucos módulos isso é ok; com
dezenas/centenas, vira "leia tudo pra saber se já existe".

Categoria de módulo (`ModuleEntry.category`, ex: `Backup`) **não resolve**
o problema real: uma capability de custo pode estar dentro de um módulo
categorizado como `Finance`, `Backup` ou qualquer rótulo — filtrar por
categoria exige que quem busca já acerte onde a capability "deveria" estar,
o que não evita duplicação de trabalho (motivação original desta nota).

O que resolve de fato: busca por **palavra-chave atravessando todas as
categorias**, batendo contra o que a capability/export realmente descreve
— não onde ela foi classificada.

## Proposta

- `ServiceRegistry` ganha `search(query: str) -> list[ServiceDescriptor]`:
  casa `query` (case-insensitive, substring) contra `service_id`,
  `capabilities`, e para cada export do contrato: `name` + `description`.
- `GET /api/v1/services?q=<termo>` (query param opcional; sem `q` continua
  listando tudo — compatível com o comportamento atual).
- `techforge services search <termo>` (novo subcomando CLI, mesmo padrão de
  `docs search`).
- Resultado deve trazer `status` visível (ACTIVE/DISABLED/FAILED) — achar
  algo que existe mas está `FAILED`/`DISABLED` é tão importante quanto achar
  algo `ACTIVE`, para a pessoa saber que precisa investigar antes de reusar.

## Fora de escopo desta correção

- Busca semântica/fuzzy (é substring simples, determinística — mesmo
  princípio de "regras determinísticas e auditáveis" da Fase 7).
- Filtro por categoria de módulo (avaliado e descartado como solução do
  problema real — ver seção Problema acima).
- Ranking por relevância — resultado é lista simples, sem score.

## Escopo estimado

Pequeno — 1 método novo em `ServiceRegistry`, 1 query param na rota
existente, 1 subcomando CLI. TDD, sem necessidade de slice separado por
camada (cabe numa sessão única).
