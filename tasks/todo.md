# Tarefas: feedback do SDK TechForge

## Tarefa 1: Preservar arquivos de modelo no pacote `.mod`

**Descrição:** Alterar o empacotador para incluir `.env-model` por allowlist, mantendo a exclusão de demais dotfiles e de artefatos de build.

**Aceitação:**
- [x] Um `.mod` contém `.env-model` quando presente.
- [x] Um `.mod` não contém `.env` nem `.git`.
- [x] A instalação de um pacote com `.env-model` preserva o arquivo no módulo instalado.

**Verificação:** testes focados de `PackageBuilder` e `PackageManager.install`; suíte backend a partir de `core/backend/`.

**Dependências:** Nenhuma.

**Arquivos prováveis:** `core/backend/app/package_manager/builder.py`, testes de builder/instalação.

**Escopo:** Pequeno.

## Tarefa 2: Aceitar export default de bundles ESM

**Descrição:** Tornar a verificação estática de export default compatível com `export default` e com reexportação nomeada como default, comum em Vite/Rollup.

**Aceitação:**
- [x] O módulo vanilla atual continua válido.
- [x] `export { Component as default, config as moduleConfig }` é válido.
- [x] Um arquivo sem export default continua inválido.

**Verificação:** `pytest cli/tests -q` a partir de `cli/`.

**Dependências:** Nenhuma.

**Arquivos prováveis:** `cli/techforge_cli/validators/module_validator.py`, `cli/tests/test_phase3.py`.

**Escopo:** Pequeno.

## Tarefa 3: Tornar a saída do CLI compatível com cp1252

**Descrição:** Centralizar a escolha de símbolos em `console.py`, usando ASCII quando a saída não codifica Unicode; preservar a apresentação Rich em UTF-8.

**Aceitação:**
- [ ] `validate-module` e `package-module` não lançam `UnicodeEncodeError` em stdout cp1252.
- [ ] A saída UTF-8 mantém os símbolos atuais.
- [ ] A saída em fallback continua legível e indica sucesso/erro.

**Verificação:** testes do CLI com stream cp1252 simulado e `pytest cli/tests -q`.

**Dependências:** Nenhuma.

**Arquivos prováveis:** `cli/techforge_cli/console.py`, testes de comandos/console.

**Escopo:** Médio.

## Checkpoint: pacote e CLI

- [ ] Testes focados das tarefas 1–3 passam.
- [ ] Backend e CLI continuam empacotando um módulo de referência.

## Tarefa 4: Conectar `/api/v1/health` ao runtime do módulo

**Descrição:** Fazer o endpoint de health chamar o hook existente para módulos ativos e responder com estado de runtime e erro diagnóstico, sem confundir estado administrativo com saúde real.

**Aceitação:**
- [x] Hook saudável retorna módulo saudável.
- [x] Hook que falha ou expira retorna não saudável, sem derrubar a resposta global.
- [x] Módulos não instalados não têm hook executado.

**Verificação:** testes de rota e runtime em `core/backend/tests`; suíte backend a partir de `core/backend/`.

**Dependências:** Definir timeout e modelo de resposta na própria tarefa.

**Arquivos prováveis:** `core/backend/app/api/routes/health.py`, `core/backend/app/core/settings.py`, testes de health/runtime.

**Escopo:** Médio.

## Tarefa 5: Consolidar o contrato do manifest e o guia de lifecycle

**Descrição:** Atualizar a referência canônica do manifest e o guia de desenvolvimento com todos os campos atuais, defaults, fetch relativo `/api`, lifecycle via activate/deactivate e nota sobre reloader.

**Aceitação:**
- [ ] Documentação cobre `channel`, `source_type`, `dependencies`, `configuration` e versionamento de documentação.
- [ ] Guia orienta teste de lifecycle pelo endpoint correto.
- [ ] Exemplo de fetch relativo é explícito.

**Verificação:** testes de documentação existentes e revisão dos links no Developer Center.

**Dependências:** Nenhuma.

**Arquivos prováveis:** `docs/manifest.example.yaml`, `docs/developer-center/reference/manifest.md`, `docs/developer-center/guides/development-guide.md`.

**Escopo:** Médio.

## Checkpoint: runtime e documentação

- [ ] Suíte backend e lint/build do frontend passam.
- [ ] Fluxo de ativação, health e desativação foi validado manualmente com `hello_world`.

## Tarefa 6: Especificar persistência oficial do SDK

**Descrição:** Produzir uma decisão técnica para SQLite isolado por módulo ou para a remoção/depreciação explícita de `sdk.database`, cobrindo local do banco, API, migrações, retenção, backup, concorrência e compatibilidade.

**Aceitação:**
- [ ] Não há ambiguidade sobre persistência de dados em produção.
- [ ] O mock deixa de parecer armazenamento durável enquanto a decisão não é implementada.
- [ ] Há plano de migração para módulos que usam o mock.

**Verificação:** revisão de decisão e testes/documentação de aviso temporário.

**Dependências:** Aprovação da questão pendente do plano.

**Arquivos prováveis:** documentação de arquitetura, `sdk/python/techforge_sdk/database/__init__.py` e testes do SDK.

**Escopo:** Médio para especificação; grande para implementação.

## Tarefa 7: Implementar a persistência do SDK aprovada

**Descrição:** Implementar a decisão da tarefa 6 em fatias: provisionamento, execução SQL/transações, migrações e testes de reinício/isolamento.

**Aceitação:**
- [ ] Dados persistem após reinício.
- [ ] Um módulo não acessa o banco de outro.
- [ ] Operações e migrações falham com diagnóstico acionável.

**Verificação:** testes unitários e integração de reinício/isolamento; suíte backend e SDK.

**Dependências:** Tarefa 6.

**Arquivos prováveis:** SDK, runtime/paths do backend, configurações e testes.

**Escopo:** Grande; dividir antes de iniciar.

## Tarefa 8: Criar módulo de referência React/TypeScript

**Descrição:** Adicionar exemplo independente, com Vite em library mode, bundle ESM e teste de carregamento pelo Core.

**Aceitação:**
- [ ] Build reproduzível produz o arquivo referenciado pelo manifest.
- [ ] Validação e instalação do exemplo passam sem `--skip-validation`.
- [ ] Guia descreve build, bundle e fetch relativo.

**Verificação:** build do exemplo, validação CLI e teste de asset/integração.

**Dependências:** Tarefa 2 e Tarefa 5.

**Arquivos prováveis:** novo módulo de exemplo, documentação e testes de integração.

**Escopo:** Médio.

## Checkpoint: persistência e exemplos

- [ ] Decisão de persistência aprovada antes da tarefa 7.
- [ ] Todos os testes, `npm run lint` e `npm run build` passam.
- [ ] Revisão humana do contrato público e do exemplo React concluída.

## Tarefa 9: Cobrir upgrade e desinstalação por pacote

**Descrição:** Criar testes de integração para install, upgrade e uninstall completos a partir de arquivos `.mod`, incluindo hooks e limpeza de artefatos.

**Aceitação:**
- [ ] Upgrade preserva a semântica esperada de `upgrade(from_version)`.
- [ ] Uninstall invoca o hook e remove os artefatos previstos.
- [ ] Falhas deixam diagnóstico e estado consistentes.

**Verificação:** testes de `PackageManager` em `core/backend/tests`.

**Dependências:** Tarefa 1.

**Arquivos prováveis:** testes de lifecycle/package manager e, se necessário, implementação correspondente.

**Escopo:** Médio.

## Tarefa 10: Definir e testar desempate da navegação de módulos

**Descrição:** Confirmar ou explicitar a ordenação determinística quando módulos compartilham `category` e `order`.

**Aceitação:**
- [ ] Dois módulos na mesma categoria são exibidos deterministicamente.
- [ ] Empate de `order` tem critério documentado e coberto por teste.
- [ ] Não há perda de módulo ou conflito de rota.

**Verificação:** testes do `NavigationBuilder` e, se aplicável, da rota de navegação.

**Dependências:** Nenhuma.

**Arquivos prováveis:** `core/backend/app/module_engine/navigation.py`, `core/backend/tests/test_nav_metadata.py`, documentação do manifest.

**Escopo:** Pequeno.
