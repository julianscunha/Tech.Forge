# TechForge — Fase 5
## Developer Center & Documentation Engine

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Transformar a documentação em parte central da plataforma e criar um Developer Center que permita a qualquer desenvolvedor — humano ou IA — entender, criar, validar e evoluir módulos seguindo contratos oficiais.

---

# 1. Contexto

O TechForge será uma plataforma extensível.

O crescimento da plataforma dependerá da capacidade de terceiros criarem módulos corretos sem precisar entender internamente todo o Core.

A documentação não deve ser apenas um conjunto de arquivos Markdown soltos.

Ela deve funcionar como:

- referência oficial;
- guia de desenvolvimento;
- especificação de contratos;
- base para IA;
- ajuda contextual;
- documentação de APIs e serviços;
- referência de compatibilidade.

Princípio:

> Se um desenvolvedor ou uma IA não consegue entender claramente como criar um módulo, a documentação está incompleta.

---

# 2. Objetivo principal

Criar um Developer Center integrado à interface web.

Ele deverá concentrar:

```text
Getting Started
Architecture
Module Development
Module Types
Manifest Reference
Packaging
Lifecycle
Compatibility
Service Contracts
Examples
CLI
Governance
AI Context
```

Não criar um Marketplace de desenvolvimento separado.

O Developer Center é a fonte central de conhecimento.

---

# 3. Documentation as a platform capability

Criar uma camada de documentação no Core.

Responsabilidades:

- localizar documentação;
- organizar;
- renderizar;
- pesquisar;
- fornecer contexto;
- expor referências de módulos;
- permitir documentação contextual.

A documentação deve continuar baseada em arquivos simples e versionáveis.

Preferir:

```text
Markdown
YAML
OpenAPI-like specifications
```

Evitar dependência de banco para armazenar todo o conteúdo documental.

---

# 4. Estrutura documental oficial

Organizar a documentação de forma previsível.

Exemplo:

```text
docs/
├── architecture/
│   ├── overview.md
│   ├── core.md
│   ├── module-boundaries.md
│   └── runtime.md
│
├── developer-center/
│   ├── getting-started/
│   ├── modules/
│   ├── services/
│   ├── contracts/
│   ├── examples/
│   ├── governance/
│   └── ai/
│
├── reference/
│   ├── manifest.md
│   ├── module-sdk.md
│   └── cli.md
│
└── operations/
```

A estrutura pode ser refinada, mas deve ser estável.

---

# 5. Developer Center UI

Criar uma interface web moderna e limpa.

Estrutura sugerida:

```text
┌─────────────────────────────────────────────────────┐
│ Developer Center                                    │
├───────────────┬─────────────────────────────────────┤
│ Navigation    │ Documentation Content               │
│               │                                     │
│ Getting Start │ Title                               │
│ Architecture  │                                     │
│ Modules       │ Content                             │
│ Services      │                                     │
│ Reference     │                                     │
│ Examples      │                                     │
└───────────────┴─────────────────────────────────────┘
```

A navegação deve:

- ser clara;
- permitir hierarquia;
- possuir busca;
- poder ser recolhida quando necessário.

---

# 6. Getting Started

Criar uma sequência objetiva para novos desenvolvedores.

Fluxo:

```text
1. Understand TechForge
2. Choose module type
3. Create module
4. Define manifest
5. Implement
6. Document
7. Test
8. Validate
9. Package
10. Install
```

Cada etapa deve conter:

- objetivo;
- requisitos;
- exemplo;
- erros comuns;
- links para referência.

---

# 7. Module development guide

Documentar o processo completo de criação de módulos.

Cobrir:

- estrutura;
- manifest;
- backend;
- frontend;
- rotas;
- navegação;
- testes;
- documentação;
- empacotamento;
- compatibilidade.

A documentação deve refletir a implementação real.

Não criar documentação baseada apenas em intenção futura.

---

# 8. Application Modules

Documentar:

- finalidade;
- estrutura;
- integração visual;
- navegação;
- limites;
- acesso a serviços;
- ciclo de vida.

Regra importante:

> Application Modules são componentes de negócio utilizados pelo usuário.

Eles podem consumir Service Modules.

Não devem ser tratados como APIs internas arbitrárias para outros módulos.

---

# 9. Service Modules

Documentar:

- finalidade;
- contratos;
- exports;
- argumentos;
- tipos;
- retornos;
- exemplos;
- integração.

Regra arquitetural:

> Service Modules fornecem capacidades reutilizáveis.

Eles devem declarar claramente como outros módulos podem consumi-los.

Um Service Module deve documentar seus contratos de forma suficiente para que outro desenvolvedor ou IA consiga utilizá-lo corretamente.

---

# 10. Service contracts

Preparar uma especificação oficial para contratos.

Exemplo conceitual:

```yaml
service:
  id: aws_cost_service

exports:
  - name: get_costs
    description: Returns cloud costs
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

Os contratos devem ser:

- explícitos;
- tipados;
- documentados;
- versionáveis.

Não exigir que consumidores dependam de código privado do módulo.

---

# 11. Exemplos

Criar padrão de exemplos.

Para Application Modules:

```text
docs/examples/basic.md
```

Para Service Modules, preparar estrutura mais completa:

```text
docs/examples/
├── basic.md
├── advanced.md
└── integration.md
```

Os exemplos devem ser executáveis ou verificáveis sempre que possível.

A documentação não deve conter exemplos que contradizem a implementação.

---

# 12. Documentation Engine

Implementar um serviço responsável por:

- localizar documentação do Core;
- localizar documentação dos módulos;
- montar árvore documental;
- fornecer conteúdo ao Frontend;
- identificar páginas inexistentes;
- resolver links internos.

A documentação de módulos deve poder ser descoberta automaticamente.

Exemplo:

```text
Module
└── docs/
    ├── overview.md
    └── examples/
```

O Core não deve precisar cadastrar manualmente cada página.

---

# 13. Help contextual

Preparar uma forma de ajuda contextual.

Exemplos futuros:

- módulo aberto → botão Help;
- página de configuração → documentação correspondente;
- serviço → contratos e exemplos.

A primeira implementação pode ser simples.

A arquitetura deve permitir:

```text
context_id
→
documentation route
```

---

# 14. Busca

Implementar busca documental.

Inicialmente pode ser local e simples.

Priorizar:

- título;
- conteúdo;
- módulos;
- contratos;
- exemplos.

Não introduzir mecanismos pesados de indexação sem necessidade.

A plataforma inicialmente roda em desktops.

---

# 15. AI Context

Criar uma forma oficial de exportar contexto técnico do TechForge para IA.

Objetivo:

> Uma IA deve conseguir receber documentação suficiente para gerar um módulo compatível.

Criar um `AIContextExporter`.

Ele deve consolidar documentação relevante como:

- arquitetura;
- regras do Core;
- tipos de módulos;
- manifest;
- contratos;
- exemplos;
- governança.

O contexto deve ser:

- estruturado;
- previsível;
- versionado;
- rastreável.

Não criar um modelo de IA interno nesta fase.

Apenas fornecer contexto adequado.

---

# 16. Contextos específicos

Permitir geração de contexto por assunto.

Exemplos:

```text
Architecture Context
Module Development Context
Service Development Context
Manifest Context
Full Developer Context
```

Evitar enviar toda a documentação quando apenas uma parte é necessária.

---

# 17. Versionamento da documentação

A documentação deve acompanhar a versão da plataforma.

Preparar metadados como:

```yaml
documentation:
  version: 1.0.0
  applies_to:
    techforge: ">=1.0.0,<2.0.0"
```

Evitar documentação sem contexto de versão quando houver mudanças incompatíveis.

---

# 18. Documentação de módulos instalados

Cada módulo deverá poder fornecer sua própria documentação.

O Developer Center deve conseguir apresentar:

```text
Core Documentation
+
Installed Module Documentation
```

Exemplo:

```text
Developer Center
└── Modules
    ├── Veeam M365
    ├── VMware Health Check
    └── AWS Cost Service
```

Módulos desativados podem permanecer documentados, desde que claramente identificados.

Módulos removidos fisicamente não devem continuar aparecendo como documentação instalada.

---

# 19. API

Criar APIs de documentação coerentes.

Exemplos:

```text
GET /api/v1/docs/tree
GET /api/v1/docs/page/{path}
GET /api/v1/docs/search?q=
GET /api/v1/docs/context/{context_id}
```

Os nomes podem ser ajustados à arquitetura existente.

O Frontend não deve precisar acessar diretamente o filesystem.

---

# 20. CLI

Adicionar comandos úteis.

Exemplo:

```bash
techforge docs list
techforge docs search <query>
techforge docs export-context
techforge docs export-context --scope module-development
```

Reutilizar o Documentation Engine.

---

# 21. Documentação como contrato

Estabelecer uma regra arquitetural:

> APIs e serviços públicos devem ser documentados como parte da implementação.

Nesta fase, estabelecer a estrutura e a convenção.

A validação automática completa de conformidade documental será aprofundada na Fase 7.

Não duplicar antecipadamente toda a lógica da Fase 7.

---

# 22. Templates documentais

Criar templates oficiais.

Exemplo:

```text
Module Overview Template
Service Contract Template
Basic Example Template
Advanced Example Template
Integration Example Template
Architecture Decision Template
```

Os templates devem reduzir inconsistências.

---

# 23. Developer Center e Marketplace

Manter responsabilidades separadas.

```text
Marketplace
→ instalar e gerenciar módulos

Developer Center
→ aprender e desenvolver módulos
```

Não transformar o Marketplace em uma IDE.

Não criar uma área separada de desenvolvimento sem necessidade.

---

# 24. Testes

Criar testes para:

- descoberta de documentação;
- árvore documental;
- documentação de módulos;
- busca;
- links internos;
- página inexistente;
- exportação de contexto;
- contextos específicos;
- documentação removida;
- integração Frontend.

Criar teste de fluxo:

```text
Module Installed
      ↓
Docs discovered
      ↓
Docs appear in Developer Center
      ↓
Context export
```

---

# 25. O que não implementar

Não implementar nesta fase:

- IA generativa integrada;
- editor completo de código;
- Marketplace de desenvolvimento;
- assinatura digital;
- Documentation Compliance Checker completo;
- Service Registry;
- Dependency Governance;
- geração automática completa de módulos.

---

# 26. Critérios de aceitação

A fase estará concluída quando:

1. O Developer Center existir.
2. A documentação estiver organizada e navegável.
3. Houver Getting Started.
4. Houver documentação de módulos.
5. Houver documentação de Application Modules.
6. Houver documentação de Service Modules.
7. Contratos puderem ser documentados.
8. Exemplos seguirem padrão.
9. A documentação de módulos instalados puder ser descoberta.
10. Busca funcionar.
11. Ajuda contextual estiver preparada.
12. O AIContextExporter funcionar.
13. Contextos específicos puderem ser exportados.
14. APIs e CLI funcionarem.
15. Documentação estiver desacoplada do Frontend.
16. A estrutura estiver preparada para validação documental da Fase 7.
17. Nenhuma funcionalidade anterior for quebrada.

---

# Regra final

Antes de finalizar:

- revisar toda a documentação;
- validar links;
- testar busca;
- instalar módulo de exemplo;
- confirmar descoberta automática da documentação;
- testar remoção do módulo;
- confirmar remoção da documentação instalada;
- testar exportação de contexto;
- validar contexto específico;
- executar testes;
- executar build do Frontend.

Apresentar:

```text
Developer Center:
Documentation Tree:
Search:
Module Documentation:
Service Contracts:
Examples:
Contextual Help:
AI Context Export:
API:
CLI:
Tests:
Build:
Known Issues:
```

Não implementar ainda o Documentation Compliance Checker completo. Essa responsabilidade pertence à Fase 7.
