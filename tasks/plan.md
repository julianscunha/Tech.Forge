# Plano de implementação: feedback do SDK TechForge

## Objetivo

Eliminar os problemas comprovados encontrados no desenvolvimento do Lead.Tracker, melhorar o caminho de desenvolvimento de módulos e evitar mudanças arquiteturais prematuras.

## Avaliação e decisões

| Item do feedback | Decisão | Prioridade | Motivo |
|---|---|---|---|
| `.env-model` excluído do `.mod` | Corrigir | P0 | Bug reproduzível que quebra `install()` de módulos empacotados. |
| `export default` em bundle Vite | Corrigir | P0 | Falso-positivo do validador; bloqueia bundles ESM válidos. |
| Unicode no CLI Windows | Corrigir | P1 | Impede uso normal no console cp1252. |
| `/health` não executa hook | Corrigir | P1 | O hook já existe no runtime; falta expô-lo com semântica segura. |
| `sdk.database` in-memory | Decidir arquitetura antes; mitigar já | P0/P2 | Hoje pode perder dados; uma implementação real altera contrato, isolamento e migrações. |
| Exemplo React/TS | Adicionar | P2 | Reduz tentativa e erro; não altera o Core. |
| React compartilhado entre Core e módulos | Adiar | — | Cria acoplamento de versão/ABI e reduz isolamento; só reconsiderar com medição de múltiplos módulos. |
| Processos órfãos do reloader | Documentar | P2 | É comportamento do watcher, não defeito do Core. |
| Schema de manifest incompleto | Consolidar documentação | P1 | Já há referência parcial, mas faltam campos e defaults atuais. |

## Decisões arquiteturais

- Dotfiles: permitir somente uma allowlist explícita de arquivos de modelo públicos, inicialmente `.env-model`; nunca liberar `.env` genericamente.
- Validador frontend: usar uma expressão regular limitada para as duas formas ESM aceitas (`export default` e `export { x as default }`). Não introduzir parser JS como dependência para uma checagem de sanidade.
- Health: o endpoint deve chamar o hook apenas para módulos `INSTALLED`, com timeout configurável. O status administrativo e o estado de runtime devem continuar distintos.
- Banco do SDK: não expor uma sessão do banco do Core a módulos. A opção a especificar é SQLite por módulo em `data/<module>.db`, com API, migração, limites e backup definidos antes da implementação.

## Dependências

```text
Contrato de persistência do SDK
  -> implementação de SQLite por módulo
  -> exemplo/documentação de persistência

Runtime health existente
  -> endpoint /health integrado

Allowlist de pacote + regras de segurança
  -> testes de build e instalação
```

## Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Permitir dotfiles incluir segredos | Alto | Allowlist estrita e teste que `.env` continua excluído. |
| Hook de health lento derrubar health global | Alto | Timeout por módulo e retorno de `FAILED`/`DEGRADED`, sem bloquear a plataforma. |
| Banco real quebrar módulos que dependem do mock | Alto | Especificar versão/compatibilidade e migrar em etapa própria. |
| Regex aceitar JavaScript semanticamente inválido | Baixo | Tratar o validador como pré-check; preservar teste de carregamento no browser. |

## Ordem de execução

1. Corrigir empacotamento e validação ESM.
2. Tornar CLI resiliente a consoles não UTF-8.
3. Integrar health público ao runtime.
4. Corrigir e consolidar a documentação de desenvolvimento/manifest.
5. Definir o contrato de persistência e só então implementar o banco real.
6. Adicionar o módulo de referência React/TS após o contrato e o guia estarem estáveis.

## Questão pendente

- Aprovar SQLite isolado por módulo como persistência oficial do SDK, ou manter o SDK sem banco e documentar que cada módulo é responsável pela própria persistência?

## Cobertura dos fluxos ainda não testados

- Adicionar testes de ciclo completo de upgrade e desinstalação de um `.mod`.
- Adicionar testes de conflito/ordenação de navegação quando múltiplos módulos compartilham `category` e `order`.
