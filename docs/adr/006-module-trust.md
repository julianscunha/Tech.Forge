---
title: "ADR-006: Module Trust"
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, adr]
---

# ADR-006: Module Trust

**Status**: Accepted

## Context

Módulos são código de terceiros carregado e executado no mesmo processo
do Core. Sem alguma forma de verificação de integridade/autenticidade, um
`.mod` adulterado (por engano ou má-fé) rodaria com o mesmo nível de
confiança que um módulo oficial, sem o usuário ter como saber.

## Decision

Cada módulo tem um manifesto de integridade por-arquivo (hash), verificado
contra o conteúdo real em disco. Assinatura de módulo usa Ed25519
(`Ed25519SignatureProvider`), resolvida junto com um Publisher Registry
(quem assinou) pra produzir um nível de confiança (`TrustResolver`). A
política de segurança padrão (`DesktopSecurityPolicy`) **não bloqueia**
instalação por nível de confiança isolado — `allows_install()` é sempre
`True` — mas está desenhada pra **sinalizar aviso**
(`requires_warning()`) em módulos não confiáveis.

## Consequences

- Adulteração de arquivo de módulo é detectável (hash não bate).
- Assinatura real (não um placeholder no-op) permite alcançar o nível
  `TRUSTED` de fato em produção.
- Decisão consciente de não bloquear instalação por trust reflete o
  contexto atual (módulos internos, instalação já é um ato deliberado do
  usuário) — não é adequado pra um marketplace público aberto sem
  revisão dessa política.
- **Gap fechado (TD-005)**: `install()`/`update()` agora resolvem o Trust
  Level do módulo logo após a extração (`resolve_module_trust()`,
  compartilhado com `GET /modules/{id}/trust`) e, quando
  `requires_warning()` é `True`, criam uma notificação real via
  `NotificationService` — o aviso chega ao sino de notificações do Core
  em vez de ficar só calculado e nunca exibido.

## Alternatives Considered

- **Bloquear instalação de módulo não confiável**: mais seguro, mas
  incompatível com o cenário atual de módulos internos/de desenvolvimento
  que ainda não têm assinatura — rejeitado por ora, revisitar se/quando
  houver distribuição pra público externo.
- **Sem verificação de integridade nenhuma**: mais simples, mas deixa
  adulteração silenciosa de módulo sem qualquer sinal — rejeitado por
  ser a lacuna de segurança mais barata de fechar desde o início.
