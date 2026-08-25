---
title: TechForge — Fase 7
category: fases
domain: [fases]
---

# TechForge — Fase 7
## Documentation Compliance Checker

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Implementar a governança automática de documentação dos módulos, validando se cada módulo possui documentação, contratos e exemplos compatíveis com seu tipo e expondo o resultado na API, CLI e interface.
>
> **Nota:** Esta fase consolida a implementação já definida para o `DocCompletenessChecker`, incluindo os requisitos específicos de Application Modules e Service Modules.

---

# 1. Contexto

A Fase 5 estabeleceu o Developer Center e a Documentation Engine.

O TechForge adota o princípio:

> Documentation First.

A documentação deve ser parte do Definition of Done de um módulo.

Um módulo não deve ser considerado documentalmente completo apenas porque possui um README.

É necessário verificar automaticamente:

- implementação;
- contratos;
- documentação;
- exemplos.

O objetivo desta fase é transformar essas regras em validação automatizada.

---

# 2. Definition of Done documental

Definir o modelo:

```text
Module Completeness
=
Implementation
+
Contract
+
Documentation
+
Examples
```

Cada módulo deverá receber um relatório claro.

Exemplo conceitual:

```text
Implementation: PASS
Contract: PASS
Documentation: PASS
Examples: PASS

Completeness: 100%
Status: COMPLETE
```

A ausência de qualquer requisito obrigatório deve aparecer explicitamente.

---

# 3. Requisitos por tipo de módulo

## Application Module

Exigir pelo menos:

```text
docs/
├── overview.md
└── examples/
    └── basic.md
```

O `overview.md` deve explicar:

- finalidade;
- funcionalidades;
- como usar;
- limitações quando aplicável.

O `basic.md` deve fornecer um exemplo inicial coerente.

---

## Service Module

Exigir:

```text
docs/
├── overview.md
└── examples/
    ├── basic.md
    ├── advanced.md
    └── integration.md
```

Além disso, exigir contrato completo.

Cada export público deve possuir:

- name;
- description;
- parameters;
- tipo dos parâmetros;
- required;
- returns;
- exemplos.

O Service Module é uma capacidade reutilizável. Sua interface pública precisa ser suficientemente explícita para consumo por outros módulos.

---

# 4. DocCompletenessChecker

Implementar o componente principal:

```text
core/backend/app/doc_engine/completeness.py
```

Responsabilidades:

- localizar o módulo;
- identificar `module_type`;
- verificar documentação obrigatória;
- verificar contrato quando necessário;
- verificar exemplos;
- calcular completude;
- retornar relatório estruturado.

O Checker deve reutilizar parsers e modelos existentes sempre que possível.

Não duplicar a lógica de parsing do manifest ou do contrato.

---

# 5. Modelo de validação

O resultado deve distinguir:

```text
PASS
FAIL
WARNING
NOT_APPLICABLE
```

Cada item deve possuir:

- identificador;
- descrição;
- resultado;
- motivo;
- caminho ou referência quando aplicável.

Exemplo conceitual:

```json
{
  "module_id": "aws_cost_service",
  "status": "incomplete",
  "checks": [
    {
      "id": "16.1",
      "name": "overview.md",
      "status": "PASS"
    },
    {
      "id": "16.4",
      "name": "integration example",
      "status": "FAIL",
      "reason": "docs/examples/integration.md not found"
    }
  ]
}
```

---

# 6. Checks oficiais

Adicionar uma seção específica de checks.

Utilizar prefixo:

```text
§16
```

A seção deve representar a governança documental.

Os checks devem cobrir:

## Para todos os módulos

- presença de `docs/overview.md`;
- qualidade estrutural mínima do overview;
- presença de `docs/examples/basic.md`;
- qualidade mínima do exemplo básico.

## Exclusivamente para Service Modules

- contrato presente;
- exports documentados;
- name;
- description;
- parameters;
- tipos;
- required;
- returns;
- exemplos;
- `basic.md`;
- `advanced.md`;
- `integration.md`.

A numeração pode ser refinada, mas deve permanecer estável e documentada.

---

# 7. Contrato de Service Module

Utilizar o formato oficial de especificação.

Exemplo:

```yaml
service:
  id: aws_cost_service

exports:
  - name: get_costs
    description: Returns cloud costs.
    parameters:
      - name: start_date
        type: string
        required: true
      - name: end_date
        type: string
        required: true
    returns:
      type: CostSummary[]
```

O Checker deve validar o formato estruturado.

Também manter compatibilidade quando necessário com retorno simples:

```yaml
returns: str
```

Normalizar internamente.

---

# 8. APIYamlParser

Estender ou consolidar o parser responsável pelos contratos.

Criar suporte para:

```yaml
returns: str
```

e:

```yaml
returns:
  type: CostSummary[]
```

Normalizar ambos para um modelo interno consistente.

Não criar formatos concorrentes.

---

# 9. Verificação de qualidade

Não limitar a validação à existência de arquivos.

Verificar qualidade estrutural mínima.

Exemplos:

- arquivo vazio → FAIL;
- somente título sem conteúdo → FAIL/WARNING conforme regra;
- TODO não resolvido em módulo publicado → FAIL/WARNING;
- contrato sem descrição → FAIL;
- parâmetro sem tipo → FAIL;
- exemplo inexistente → FAIL.

Evitar tentar criar uma IA avaliadora de qualidade nesta fase.

As regras devem ser determinísticas e auditáveis.

---

# 10. Exemplos coerentes com implementação

Quando tecnicamente possível, exemplos devem corresponder ao comportamento real.

Para exemplos verificáveis:

```text
Implementation
      ↓
Execute/Test
      ↓
Expected documented result
      ↓
Compare
```

Exemplo conceitual:

```text
users=500
mailbox_quota_gb=50

Expected:
total_gb=25000
recommended_repo_gb=27500
growth_factor=1.1
```

Se o módulo possuir comportamento simples e determinístico, criar testes que garantam que o exemplo documentado corresponde ao código real.

Não inventar mecanismos complexos de execução genérica de Markdown.

---

# 11. Templates compliant

Atualizar o gerador de templates.

O `TemplateGenerator` deve gerar módulos já compatíveis com a governança básica.

Para novos módulos:

```text
docs/overview.md
docs/examples/basic.md
```

Para Service Modules, gerar também:

```text
docs/examples/advanced.md
docs/examples/integration.md
```

e o scaffold de contrato.

Os arquivos podem conter placeholders claramente identificados.

Entretanto, a política de publicação deve diferenciar:

```text
development scaffold
```

de:

```text
production-ready documentation
```

Um módulo recém-criado pode estar estruturalmente completo, mas ainda possuir pendências de conteúdo claramente reportadas.

Não mascarar documentação incompleta como conteúdo finalizado.

---

# 12. CLI

Estender:

```bash
techforge validate-module
```

Ou a convenção equivalente existente.

A validação deve incluir os checks §16.

Exemplo:

```text
§16 Documentation Compliance

16.1 overview.md ........ PASS
16.2 overview quality ... PASS
16.3 basic example ...... PASS
16.4 contract ........... PASS
16.5 advanced example ... PASS
16.6 integration example  PASS

Result: COMPLETE
```

A CLI deve reutilizar o `DocCompletenessChecker`.

---

# 13. APIs

Criar:

```text
GET /api/v1/docs/completeness
GET /api/v1/docs/completeness/{module_id}
```

A primeira rota deve retornar relatórios dos módulos instalados sem criar consultas N+1 desnecessárias.

A segunda deve retornar o relatório detalhado de um módulo.

O formato deve ser estável para consumo pelo Frontend.

---

# 14. Frontend

Adicionar um componente:

```text
CompletenessBadge
```

Exibir nos cards da Modules Page.

Exemplos conceituais:

```text
Complete
85%
Incomplete
Missing Docs
```

A interface não deve executar uma chamada por módulo.

Buscar os relatórios em lote:

```text
completenessApi.all()
```

Mapear os resultados localmente.

---

# 15. Notificações

Integrar com a Notification Foundation.

Exemplos:

- documentação incompleta;
- contrato inválido;
- módulo perdeu conformidade após atualização;
- exemplo obrigatório ausente.

Não criar notificações excessivas para cada pequena observação.

Priorizar problemas que impactam:

- publicação;
- consumo por outros módulos;
- manutenção.

---

# 16. Integração com Developer Center

O Developer Center deve documentar a própria regra.

Criar:

```text
docs/developer-center/governance/documentation-first-principle.md
```

Explicar:

- por que documentação é parte do módulo;
- Definition of Done;
- requisitos por tipo;
- checks;
- exemplos;
- contratos;
- como corrigir falhas.

Incluir essa governança no `AIContextExporter`.

---

# 17. Contexto para IA

O contexto exportado para IA deve incluir:

- Documentation First;
- estrutura do módulo;
- manifest;
- requisitos documentais;
- contrato de Service Modules;
- exemplos;
- checks §16.

Objetivo:

> Uma IA que receba o contexto oficial deve conseguir criar um módulo compatível e saber quais requisitos precisa cumprir.

---

# 18. Compatibilidade com módulos existentes

Não quebrar módulos existentes silenciosamente.

Ao introduzir o Checker:

1. analisar módulos existentes;
2. identificar lacunas;
3. atualizar documentação quando necessário;
4. validar novamente.

Evitar criar exceções permanentes apenas para preservar módulos antigos.

Se um módulo de referência estiver fora do padrão, corrigir o módulo.

---

# 19. Testes

Criar testes para:

- Application Module completo;
- Application Module sem overview;
- Application Module sem basic example;
- Service Module completo;
- Service Module sem contrato;
- export sem descrição;
- parâmetro sem tipo;
- parâmetro sem required;
- returns ausente;
- returns simples;
- returns estruturado;
- basic ausente;
- advanced ausente;
- integration ausente;
- arquivo vazio;
- múltiplos módulos;
- API de todos os módulos;
- API individual;
- CLI;
- TemplateGenerator.

Criar smoke test completo.

A implementação deve validar a cadeia:

```text
Module
↓
Manifest
↓
Type
↓
Documentation
↓
Contract
↓
Examples
↓
Completeness Report
↓
API
↓
Frontend Badge
```

---

# 20. O que não implementar

Não implementar nesta fase:

- IA avaliando semântica profunda da documentação;
- geração automática de documentação por IA;
- Service Registry;
- Dependency Governance;
- assinatura digital;
- Marketplace remoto;
- sistema de permissões.

---

# 21. Critérios de aceitação

A fase estará concluída quando:

1. `DocCompletenessChecker` existir.
2. Application Modules tiverem requisitos documentais claros.
3. Service Modules tiverem requisitos adicionais.
4. Contratos forem validados.
5. Todos os exports públicos forem avaliados.
6. Exemplos obrigatórios forem verificados.
7. `returns` simples e estruturado forem suportados.
8. O CLI mostrar os checks §16.
9. A API retornar relatórios em lote.
10. A API retornar relatório individual.
11. O Frontend exibir badge de completude.
12. Não houver N+1 desnecessário.
13. Templates nascerem estruturalmente compatíveis.
14. A governança estiver documentada.
15. O `AIContextExporter` incluir as regras.
16. Exemplos verificáveis forem testados contra implementação quando aplicável.
17. Módulos existentes forem revisados.
18. Todos os testes passarem.

---

# 22. Resultado esperado

Ao final, apresentar:

```text
DocCompletenessChecker:
Application Requirements:
Service Requirements:
§16 Checks:
API:
CLI:
Frontend Badge:
TemplateGenerator:
AI Context:
Documentation Governance:
Tests:
Build:
Known Issues:
```

Não avançar para Service Registry ou Dependency Governance nesta fase.
