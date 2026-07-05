---
title: FAQ
order: 1
tags: [faq, troubleshooting, common-questions]
---

# Perguntas Frequentes (FAQ)

## Geral

**Posso modificar o Core da plataforma?**
Não. O Core (pasta `core/`) não deve ser modificado. Toda extensão acontece via módulos. Se uma funcionalidade que você precisa não está disponível no SDK, abra uma issue.

**Quantos módulos posso instalar?**
Não há limite definido. O desempenho depende dos recursos do servidor.

**Um módulo pode depender de outro?**
Sim. Declare dependências no `api.yaml` do contrato de serviço. A resolução automática de dependências está planejada para uma fase futura.

---

## Desenvolvimento

**Por que meu módulo aparece como INVALID?**
As causas mais comuns são:
- `manifest.yaml` com campos obrigatórios ausentes (`icon`, `order`)
- Arquivo declarado em `entry_backend` ou `entry_frontend` não existe no disco
- YAML inválido no manifest
- Formato incorreto do campo `icon` (deve ser kebab-case lucide)

Execute `techforge validate-module .` para obter o relatório completo.

**O campo `icon` aceita qualquer valor?**
Não. Deve ser um nome de ícone do [Lucide React](https://lucide.dev/icons) em **kebab-case**. Exemplo: `shield-check`, `database`, `hard-drive`. Ícones em PascalCase (`ShieldCheck`) serão rejeitados pelo validator.

**Posso usar componentes React customizados no meu módulo?**
Sim, dentro da área de conteúdo do módulo. Você não pode modificar o Header, Sidebar ou qualquer elemento global. Use os componentes do SDK Frontend para manter consistência visual.

**Como faço para que meu módulo apareça no sidebar?**
Automaticamente, ao instalar o módulo com um `manifest.yaml` válido. A Sidebar é construída a partir dos campos `category`, `vendor`, `icon`, `order` e `color` do manifest. Nenhuma configuração adicional é necessária.

---

## SDK

**Qual a diferença entre `sdk.storage` e `sdk.database`?**
- `sdk.storage` é para arquivos binários e texto (JSON, CSV, imagens, PDFs)
- `sdk.database` é para dados estruturados com queries SQL

**O `sdk.database` usa o mesmo banco do Core?**
Não. Cada módulo tem seu próprio namespace isolado. Um módulo não pode acessar dados de outro.

**Como persisto configurações do meu módulo?**
Use `sdk.settings.set("chave", valor)`. Os dados são salvos em `modules/installed/<id>/data/settings.json`.

**O SDK está disponível no frontend também?**
Sim. O SDK Frontend (`@techforge/sdk`) oferece componentes React, tokens de design e contratos de tipo. Os serviços de dados (database, storage) só estão disponíveis no backend.

---

## Marketplace e Packaging

**Como distribuo meu módulo?**
1. `techforge validate-module .` — garanta que está válido
2. `techforge package-module .` — gera `<id>-<version>.mod`
3. Distribua o arquivo `.mod`

**Como atualizo um módulo instalado?**
Via Marketplace → aba Atualizações, ou via `POST /api/v1/marketplace/update/{id}`. O Package Manager verifica compatibilidade e faz backup automático da versão anterior.

**O que acontece se uma atualização falhar?**
O Package Manager reverte automaticamente para a versão anterior usando o backup em `modules/cache/`.

---

## Developer Center

**Como a documentação do meu módulo é indexada?**
Qualquer arquivo `.md` em `modules/installed/<id>/docs/` é indexado automaticamente ao instalar o módulo. Não é necessária nenhuma configuração.

**Como exporto o contexto para uma IA?**
Acesse Developer Center → botão "Export AI Context", ou via API:
```
GET /api/v1/docs/export/ai-context
```
Isso gera um único arquivo Markdown consolidando toda a documentação da plataforma.
