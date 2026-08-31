# Política de Segurança

## Reportando uma vulnerabilidade

Se você encontrou uma vulnerabilidade de segurança no TechForge, **não abra
uma issue pública**. Use o **GitHub Private Vulnerability Reporting**:

1. Vá na aba **Security** deste repositório.
2. Clique em **Report a vulnerability**.
3. Descreva o problema com o máximo de detalhe possível (passos para
   reproduzir, impacto, versão afetada).

Isso cria um relatório privado, visível só para os mantenedores, até que
o problema seja triado e corrigido.

## Escopo

**Em escopo**: o Core (`core/backend`, `core/frontend`), o CLI (`cli/`) e o
SDK (`sdk/`).

**Fora de escopo**: módulos de terceiros instalados via `.mod`. Cada
módulo publicado é responsabilidade de quem o desenvolveu e assinou — o
Core verifica integridade (hash por arquivo) e assinatura (Ed25519) de um
pacote, mas não audita o código de negócio dentro dele. Uma vulnerabilidade
dentro da lógica de um módulo específico deve ser reportada ao mantenedor
desse módulo, não aqui.

## Tempo de resposta

Este é um projeto mantido por uma pessoa, não uma equipe de segurança
corporativa — não há SLA formal. Na prática, espere uma resposta inicial
em poucos dias. Vulnerabilidades confirmadas recebem prioridade sobre
qualquer outro trabalho em andamento.

## Boas práticas já em vigor

- Pacotes de módulo (`.mod`) têm limite de recursos na extração (proteção
  contra zip bomb).
- Integridade por-arquivo e assinatura Ed25519 (Module Trust) — ver
  [`docs/adr/006-module-trust.md`](docs/adr/006-module-trust.md).
- Segredos de módulo isolados via `keyring` do sistema operacional, nunca
  em texto plano no banco.

Limitações conhecidas relacionadas a segurança (ex: aviso de confiança na
instalação ainda não conectado à UI) estão documentadas em
[`docs/limitations.md`](docs/limitations.md) — não são segredo, mas também
não deixam de ser candidatas legítimas a relatório se você achar um jeito
concreto de explorá-las.
