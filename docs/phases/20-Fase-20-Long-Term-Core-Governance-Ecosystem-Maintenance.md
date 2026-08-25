# TechForge — Fase 20
## Long-Term Core Governance & Ecosystem Maintenance

> **Objetivo:** Definir como o TechForge Core evolui após a publicação pública sem perder estabilidade, compatibilidade, leveza e qualidade do ecossistema de módulos.

---

# 1. Contexto

Após a Fase 19, o TechForge pode estar pronto para publicação pública.

Isso não significa que o Core deve continuar crescendo sem controle.

O principal risco após a abertura do ecossistema é:

```text
New Feature Requests
        ↓
Core Growth
        ↓
More Dependencies
        ↓
More Startup Cost
        ↓
More Complexity
        ↓
Core Becomes Heavy
```

O objetivo desta fase é impedir isso.

---

# 2. Princípio principal

```text
The Core is a Platform, not a collection of features.
```

Funcionalidades específicas devem preferencialmente existir como:

```text
Independent Modules
```

O Core deve crescer somente quando a mudança beneficia:

```text
Module lifecycle
Platform infrastructure
Security
Runtime
SDK
Compatibility
Developer experience
```

---

# 3. Core inclusion rule

Antes de adicionar uma funcionalidade ao Core, responder:

```text
Can this be an independent module?
```

Se:

```text
Yes
```

não adicionar ao Core sem justificativa arquitetural.

---

# 4. Core budget

Manter métricas de saúde do Core:

```text
Startup time
Memory usage
Binary/package size
Dependency count
Idle CPU
Module discovery time
Dashboard load time
```

Mudanças relevantes devem comparar:

```text
Before
After
Impact
```

---

# 5. Dependency governance

Toda nova dependência do Core deve justificar:

```text
Why needed?
Can existing dependency solve it?
Impact on package size?
Security maintenance?
License?
Cross-platform impact?
```

Não adicionar bibliotecas apenas por conveniência.

---

# 6. Module API stability

Definir contratos públicos.

Exemplo:

```text
Stable
Deprecated
Experimental
Internal
```

Módulos externos não devem depender de:

```text
Internal Core implementation details
```

---

# 7. API lifecycle

Para breaking changes:

```text
Introduce replacement
↓
Mark old API deprecated
↓
Document migration
↓
Maintain compatibility period
↓
Remove only in major release
```

---

# 8. SDK compatibility

O SDK deve declarar:

```text
SDK Version
Minimum TechForge Version
Supported TechForge Versions
```

Criar testes de compatibilidade quando necessário.

---

# 9. Module contract governance

Toda alteração em:

```text
Manifest schema
Dependency schema
Service contracts
Package format
Runtime lifecycle
```

deve passar por revisão de compatibilidade.

---

# 10. Architecture Decision Records

Usar ADR para decisões estruturais.

Formato:

```text
Context
Decision
Alternatives
Consequences
Status
```

Decisões que exigem ADR:

```text
Core architecture
Module contracts
Security model
Package format
Breaking changes
Runtime changes
Dependency model
```

---

# 11. Experimental features

Evitar adicionar APIs imaturas diretamente como estáveis.

Usar:

```text
Experimental API
```

com:

```text
Explicit warning
Version scope
Exit criteria
```

---

# 12. Deprecation policy

Toda funcionalidade removida deve possuir:

```text
Reason
Replacement
Deprecation version
Removal target
Migration guide
```

Não remover contratos públicos silenciosamente.

---

# 13. Ecosystem compatibility testing

Manter conjunto de módulos de referência:

```text
Reference Application
Reference Passive Service
Reference Active Service
Reference Dependent Application
```

Antes de releases importantes:

```text
Build Core
↓
Install references
↓
Run tests
↓
Validate lifecycle
↓
Validate updates
```

---

# 14. Independent repository validation

Os módulos de referência devem continuar independentes.

Não modificar o Core para fazê-los funcionar artificialmente.

O teste deve reproduzir:

```text
Real external developer conditions
```

---

# 15. Marketplace evolution rule

O Marketplace deve continuar sendo:

```text
Discovery
Import
Install
Update
Manage
```

Evitar transformá-lo inicialmente em:

```text
Social network
Complex recommendation engine
Centralized commercial platform
```

---

# 16. Source compatibility evolution

A arquitetura pode futuramente suportar:

```text
GitHub
GitLab
Private Git
HTTP
Internal repositories
```

Mas novos providers devem implementar a abstração existente.

Não alterar o Install Pipeline para cada provider.

---

# 17. Security maintenance

Manter processo periódico:

```text
Dependency updates
Vulnerability review
Secret scanning
Package validation review
Trust policy review
```

---

# 18. Module ecosystem security

Separar:

```text
Platform security
```

de:

```text
Module trust
```

Um módulo válido tecnicamente não é automaticamente confiável.

Estados possíveis:

```text
Unknown
Unverified
Verified
Trusted
Blocked
```

A implementação inicial pode ser simples, mas o modelo deve existir.

---

# 19. Performance regression testing

Definir baseline:

```text
Core startup
Idle memory
Dashboard load
Module discovery
Install
Update
```

Antes de releases:

```text
Current Result
vs
Baseline
```

Investigar regressões significativas.

---

# 20. Documentation governance

Alteração em contrato público exige atualização de:

```text
Developer Center
Examples
SDK documentation
AI Context
Migration guides
```

Documentação não é atividade posterior.

---

# 21. AI Context governance

Toda mudança estrutural deve avaliar:

```text
Does the AI Context remain accurate?
```

O AI Context deve:

```text
Reference current standards
Avoid stale examples
Reflect public contracts
```

---

# 22. Issue triage

Classificar:

```text
Bug
Security
Documentation
Module compatibility
Feature request
Core architecture
```

Não tratar todos os pedidos de funcionalidade como candidatos ao Core.

---

# 23. Feature request decision flow

```text
Feature Request
↓
Is platform infrastructure required?
├── Yes → Core evaluation
└── No
      ↓
Can it be a module?
├── Yes → Module recommendation
└── No → Architecture review
```

---

# 24. Release cadence

Não definir frequência artificial obrigatória.

Publicar quando houver:

```text
Validated changes
Security fixes
Compatible improvements
Meaningful release
```

Priorizar qualidade.

---

# 25. Maintenance branches

Para versões públicas relevantes, definir política de:

```text
Current
Supported
Deprecated
End of life
```

Documentar claramente.

---

# 26. Community governance

Definir futuramente, conforme crescimento:

```text
Maintainers
Review process
Contribution requirements
Module quality expectations
```

Não criar burocracia excessiva antes da necessidade.

---

# 27. Public module quality baseline

Um módulo recomendado como exemplo deve possuir:

```text
Valid manifest
Version compatibility
Documentation
Examples
Tests
Validation
Release package
```

---

# 28. No hidden coupling rule

Não permitir que:

```text
Core changes
```

dependam de módulos específicos.

Nem que:

```text
External modules
```

dependam de arquivos internos não públicos.

---

# 29. Core health report

Criar relatório periódico:

```text
Core Version
Dependencies
Startup
Memory
Package Size
Public APIs
Deprecated APIs
Compatibility Status
Security Status
Reference Module Tests
Documentation Status
```

---

# 30. Upgrade path

Toda versão deve preservar, quando possível:

```text
User configuration
Installed module registry
Module source metadata
Module state
```

Mudanças devem possuir:

```text
Migration
Backup
Rollback strategy
```

---

# 31. Acceptance criteria

Esta fase estará definida e operacional quando:

1. Core inclusion rule estiver documentada.
2. Core health metrics estiverem definidas.
3. Dependency governance existir.
4. Public API lifecycle estiver definido.
5. SDK compatibility policy existir.
6. Module contract changes forem governados.
7. ADR process estiver disponível.
8. Experimental APIs tiverem política.
9. Deprecation policy existir.
10. Reference ecosystem existir.
11. External compatibility tests existirem.
12. Marketplace scope estiver protegido.
13. Source abstraction permanecer estável.
14. Security maintenance process existir.
15. Module trust model estiver documentado.
16. Performance baselines existirem.
17. Documentation governance existir.
18. AI Context governance existir.
19. Issue triage estiver definido.
20. Feature request decision flow existir.
21. Release policy existir.
22. Support lifecycle existir.
23. Public module quality baseline existir.
24. Hidden coupling rule estiver validada.
25. Core health report estiver definido.
26. Upgrade and rollback strategy existir.

---

# Resultado esperado

Após esta fase, o TechForge não deve apenas estar pronto para ser publicado.

Ele deve possuir um modelo para continuar evoluindo:

```text
New Ideas
    ↓
Architecture Review
    ↓
Core or Module?
    ↓
Compatibility Review
    ↓
Implementation
    ↓
Documentation
    ↓
Reference Ecosystem Tests
    ↓
Performance Validation
    ↓
Release
```

A regra central permanece:

```text
Keep the Core small.
Keep the contracts stable.
Let the ecosystem grow through modules.
```
