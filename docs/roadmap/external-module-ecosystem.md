---
title: Visão — Ecossistema Público de Módulos
category: governanca-setup
domain: [governanca-setup]
tags: [roadmap, limitations]
---

# Ecossistema Público de Módulos

> Visão de futuro, sem decisão de quando (ou se) será construída. Aguarda
> uma decisão de produto e governança sobre publicação de terceiros em
> escala, não um plano de implementação.

## O que já existe hoje

O Core já suporta múltiplas fontes de catálogo (local, oficial via
índice remoto, customizada via repositório GitHub), já assina e verifica
integridade de módulo (Module Trust), e já resolve dependências entre
módulos instalados com uma direção clara (Application pode depender de
Service, nunca o inverso). Isso é a base sobre a qual um ecossistema
público seria construído — não algo que precisaria ser refeito.

## O problema que essa iniciativa resolveria

Hoje, adicionar um módulo de uma fonte externa passa pelo mesmo pipeline
de instalação local. Mas não existe ainda um caminho oficial para: um
desenvolvedor de fora construir um módulo num repositório independente,
publicar uma release, e um usuário do TechForge simplesmente colar a URL
desse repositório e instalar — sem que o TechForge precise saber
previamente que aquele módulo existe.

## Perguntas em aberto que essa iniciativa cobriria

- **Módulo por URL, não repositório inteiro.** Uma URL representaria um
  módulo independente (não um repositório com vários módulos dentro).
  O fluxo de resolução (inspecionar → validar → empacotar → instalar)
  precisaria ser o mesmo pipeline usado hoje pra importação local — o
  instalador não deveria nunca precisar saber de onde o módulo veio.
- **Instalação a partir de release, nunca de branch.** Por segurança e
  reprodutibilidade, instalar a partir de uma release publicada e
  versionada (com checksum e assinatura), nunca diretamente do código
  de uma branch em desenvolvimento.
- **Declaração formal de tipo e modo do módulo.** Hoje um módulo já se
  declara `application` ou `service`; um ecossistema público precisaria
  formalizar também um modo operacional (passivo — carregado sob
  demanda — vs. ativo — com execução em segundo plano), já que módulos
  de terceiros teriam perfis de execução mais variados que os módulos
  de exemplo atuais.
- **Curadoria e confiança em escala.** Module Trust já existe para
  verificar integridade e assinatura, mas confiança técnica não é o
  mesmo que confiança de conteúdo — um módulo tecnicamente válido não é
  automaticamente recomendável. Precisaria existir uma política clara
  de curadoria antes de expor publicação de terceiros amplamente.
- **Atualização segura vindo de fonte externa.** Verificação de nova
  versão, aprovação manual (nunca atualização automática silenciosa por
  padrão), e comportamento previsível se a fonte externa ficar
  indisponível — o módulo já instalado deveria continuar funcionando
  offline se não depender da fonte em runtime.
- **Isolamento de falha da fonte.** Uma URL externa fora do ar, uma
  release corrompida, ou uma fonte removida não podem quebrar módulos
  já instalados nem travar o Marketplace.
- **Fluxo de desenvolvedor externo documentado de ponta a ponta.** Um
  desenvolvedor de fora deveria conseguir criar, testar, empacotar e
  publicar um módulo usando só o SDK e a documentação pública — sem
  precisar tocar no repositório do Core.

## O que esta iniciativa explicitamente NÃO cobriria

Marketplace federado (múltiplos catálogos centrais competindo),
qualquer URL arbitrária tratada como código executável sem validação,
um segundo resolvedor de dependências ou instalador paralelo ao que já
existe, ou uma segunda especificação de manifest. A regra de ouro seria
a mesma de sempre: módulos externos passam pelo mesmo pipeline, nunca
um pipeline próprio.
