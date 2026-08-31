---
title: Visão — Governança de Longo Prazo do Core
category: governanca-setup
domain: [governanca-setup]
tags: [roadmap, limitations]
---

# Governança de Longo Prazo do Core

> Visão de futuro: como o Core deveria continuar evoluindo depois que um
> ecossistema de módulos externos existir de verdade — sem perder
> estabilidade, leveza e compatibilidade. Ainda não é um processo em
> vigor, é o modelo pretendido para quando fizer sentido formalizá-lo.

## O risco que essa governança evitaria

Um ecossistema aberto naturalmente traz pedidos de funcionalidade. Sem
uma regra clara, cada pedido tende a virar "só mais uma coisinha no
Core" — e um Core que cresce sem controle vira lento pra iniciar, pesado
em dependências e difícil de manter compatível. O princípio central que
guiaria essa governança:

> O Core é uma plataforma, não uma coleção de funcionalidades.

## Regra de inclusão no Core

Antes de adicionar qualquer coisa nova ao Core, a pergunta seria sempre:
"isto poderia ser um módulo independente?" Se a resposta for sim, não
entra no Core sem uma justificativa arquitetural explícita. O Core só
cresceria quando o benefício for para o lifecycle de módulo, a
infraestrutura da plataforma, segurança, runtime, SDK, compatibilidade
ou experiência de desenvolvedor — nunca para uma funcionalidade de
domínio específica.

## O que essa governança cobriria

- **Orçamento de peso do Core.** Acompanhar métricas de saúde (tempo de
  startup, uso de memória, tamanho do pacote, contagem de dependências,
  tempo de descoberta de módulos) e exigir que mudanças relevantes
  comparem antes/depois — não deixar o peso crescer silenciosamente.
- **Toda nova dependência justificada.** Por que é necessária, se uma
  dependência já existente resolveria, impacto no tamanho do pacote,
  manutenção de segurança, licença, impacto multiplataforma.
- **Estabilidade de contrato público declarada.** Cada contrato público
  (manifest, dependências, service contracts, formato de pacote,
  lifecycle de runtime) precisaria de uma classificação explícita
  (Stable / Experimental / Deprecated) — módulos externos nunca deveriam
  depender de detalhe de implementação interna do Core.
- **Ciclo de vida de API pública formal.** Introduzir substituto → marcar
  o antigo como deprecated → documentar migração → manter um período de
  compatibilidade → remover só em release major. Nunca remover um
  contrato público silenciosamente.
- **Registro de decisões arquiteturais (ADR) para mudanças estruturais**
  — arquitetura do Core, contratos de módulo, modelo de segurança,
  formato de pacote, mudanças breaking, modelo de dependência.
- **Ecossistema de referência para testar compatibilidade.** Manter um
  pequeno conjunto de módulos de referência (aplicação, serviço passivo,
  serviço ativo, aplicação dependente) construídos em repositórios
  verdadeiramente independentes, e rodar contra eles antes de releases
  importantes — sem alterar o Core artificialmente pra fazê-los
  funcionar.
- **Confiança de módulo como modelo formal, não implícito.** Separar
  segurança da plataforma de confiança de módulo — um módulo
  tecnicamente válido não é automaticamente confiável. Estados como
  desconhecido/não verificado/verificado/confiável/bloqueado precisam
  existir como modelo, mesmo que a implementação inicial seja simples.
- **Triagem de pedidos de funcionalidade.** Toda sugestão passaria por
  "isto exige infraestrutura de plataforma?" antes de "isto pode ser um
  módulo?" — a maioria das respostas deveria apontar pra módulo, não
  pro Core.
- **Cadência de release por qualidade, não por calendário.** Publicar
  quando houver mudança validada, correção de segurança ou melhoria
  compatível — não por uma frequência artificial.

## O que já ajuda hoje

Uma política de deprecação (Mark → Document → Warn → Migrate → Remove) e
a classificação de estabilidade dos contratos públicos do Core já foram
formalizadas na consolidação arquitetural mais recente — essa governança
de longo prazo herdaria essas bases em vez de recomeçar do zero.
