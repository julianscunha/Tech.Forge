---
title: Visão — Servidor Central & Multiusuário
category: governanca-setup
domain: [governanca-setup]
tags: [roadmap, limitations]
---

# Servidor Central & Multiusuário

> Visão de futuro, sem decisão de quando (ou se) será construída. Aguarda
> uma necessidade de negócio real, não uma antecipação especulativa.

## O problema que isso resolveria

Hoje o TechForge roda como uma instalação Desktop: um único processo, um
único usuário, SQLite local, `127.0.0.1`. Isso é deliberado — é o que
mantém a plataforma simples e fácil de rodar. Mas há um cenário
razoavelmente previsível em que isso deixa de bastar: uma equipe inteira
querendo compartilhar o mesmo conjunto de módulos instalados, o mesmo
catálogo e os mesmos dados, a partir de um servidor central em vez de
cada pessoa ter sua própria instalação isolada.

## O princípio que guiaria a solução

Separar claramente **modelo de deployment** de **arquitetura de
negócio**. Um módulo não deveria precisar saber se está rodando num
desktop isolado ou num servidor compartilhado — essa diferença deveria
ser absorvida pelo Runtime, não vazar para dentro da lógica de cada
módulo.

## Perguntas em aberto que essa iniciativa cobriria

- **Perfis de deployment.** Um modo `desktop` e um modo `server`
  configuráveis, com o Desktop continuando simples, leve e sem serviços
  externos obrigatórios — o modo servidor ganhando os requisitos que
  fazem sentido só nesse contexto (rede, múltiplos usuários,
  PostgreSQL, catálogo central).
- **Estado sem acoplamento a processo único.** O backend hoje pode
  assumir implicitamente que só existe uma requisição por vez, um único
  usuário, um único processo. Rodar em servidor exigiria eliminar
  qualquer estado global mutável que dependa disso, sem introduzir
  autenticação ou multiusuário de verdade antes da hora.
- **Contexto de execução isolado por requisição.** Hoje não há uma
  noção formal de "de onde veio esta chamada" além do processo em si.
  Um servidor compartilhado precisaria de um contexto de requisição
  (id, origem, execução) que pudesse mais tarde carregar identidade de
  usuário sem quebrar o contrato existente.
- **Portabilidade de storage e filesystem.** SQLite localmente,
  PostgreSQL num servidor — a camada de acesso a dados já precisa estar
  abstraída o suficiente pra essa troca não exigir reescrever módulos.
  O mesmo vale para arquivos: nenhum módulo deveria assumir um caminho
  de disco específico do host.
- **Rede, proxy reverso e múltiplas instâncias.** Hoje a plataforma
  assume `127.0.0.1` por padrão. Um modo servidor precisaria de binding
  configurável, prontidão para rodar atrás de Nginx/Caddy, e uma URL de
  API que não seja fixa no frontend.
- **Autorização, mas não ainda.** Não faz sentido implementar RBAC,
  SSO ou multiusuário completo sem um caso de uso real guiando o
  design. O que faz sentido agora é não introduzir estado global que
  torne isso impossível de adicionar depois.
- **Trabalho em segundo plano mais longo.** Operações que hoje rodam
  rápido no processo local (cálculos, geração de relatório) poderiam
  precisar de uma abstração de tarefa/job antes de justificar fila
  distribuída, Redis ou Celery — que não deveriam entrar sem
  necessidade concreta.

## O que já ajuda hoje

A revisão de arquitetura já confirmou que o Core não tem acoplamento
óbvio impossível de migrar: configuração já é centralizada (sem
URLs/portas hardcoded fora do módulo de settings), e o ponto mais
concreto de acoplamento a processo único encontrado até agora é o
rastreamento de jobs de instalação remota, que hoje vive em memória
amarrado ao processo que o criou — um detalhe conhecido, não uma
barreira estrutural.

## O que esta iniciativa explicitamente NÃO cobriria

Login, RBAC, SSO, MFA, cluster, Kubernetes, load balancer obrigatório,
filas obrigatórias (Redis/RabbitMQ), pool de workers, ou multi-tenancy
completa. O objetivo seria deixar o caminho aberto, não construir a
escala corporativa antes de ela ser necessária.
