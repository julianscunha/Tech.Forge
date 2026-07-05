---
title: Writing Documentation for TechForge Modules
order: 2
tags: [documentation, markdown, api-yaml, best-practices, ai-context]
---

# Writing Documentation for TechForge Modules

Escrever boa documentação permite que outros desenvolvedores — e IAs — entendam e usem seu módulo corretamente.

## Estrutura esperada

```
my_module/docs/
├── overview.md             ← obrigatório — visão geral
├── contracts/
│   └── api.yaml            ← se for um service module
└── examples/
    ├── basic.md
    ├── advanced.md
    └── integration.md
```

## overview.md

O arquivo `overview.md` é a primeira coisa que os desenvolvedores veem. Inclua:

```markdown
# Nome do Módulo

Descrição clara em uma ou duas frases.

## O que faz

Liste as funcionalidades principais em bullet points.

## Quando usar

Descreva o caso de uso ideal.

## Dependências

- Serviço X (techforge_sdk)
- API externa Y (configure em settings)

## Configuração

Descreva as settings obrigatórias:
- `api_url` (string): URL da API externa
- `max_retries` (int): Número de tentativas (padrão: 3)
```

## contracts/api.yaml

Use `api.yaml` para documentar serviços exportados:

```yaml
service_id: my_service
description: Descrição clara do serviço
version: 1.0.0
dependencies:
  - other_service

exports:
  - name: process_job
    description: Processa um job e retorna o resultado
    parameters:
      - name: job_id
        type: str
        description: Identificador único do job
        required: true
      - name: timeout
        type: int
        description: Timeout em segundos
        required: false
    returns: "dict com keys: status, result, duration_ms"
    examples:
      - "result = await process_job('job_123', timeout=30)"
      - "result = await process_job('job_456')  # usa timeout padrão"
```

## examples/basic.md

```markdown
# Exemplo Básico

Demonstra o uso mais simples do módulo.

## Instalação e configuração

\`\`\`python
# Configure as settings do módulo
sdk.settings.set("api_url", "https://api.example.com")
sdk.settings.set("api_key", "sua-chave-aqui")
\`\`\`

## Uso básico

\`\`\`python
from techforge_sdk import create_sdk
sdk = create_sdk("my_module")

result = await sdk.database.fetch_all("SELECT * FROM jobs")
\`\`\`
```

## Boas práticas para consumo por IAs

Para que Claude, ChatGPT ou Gemini consigam ajudar desenvolvedores a usar seu módulo:

**1. Seja explícito sobre tipos**
```markdown
# ruim
Retorna o resultado do job.

# bom
Retorna `dict` com chaves:
- `status` (str): "success" | "failed" | "pending"
- `result` (any): payload de saída, ou None se pending
- `duration_ms` (int): tempo de execução em milissegundos
```

**2. Inclua exemplos funcionais completos**
```python
# Mostre imports, instanciação e uso em sequência
from techforge_sdk import create_sdk
sdk = create_sdk("my_module")

async def main():
    await sdk.storage.write("input.json", data.encode())
    result = await process_file("input.json")
    print(result)
```

**3. Documente erros esperados**
```markdown
## Erros comuns

- `PermissionError`: tentativa de acessar arquivo fora do sandbox
- `ConnectionError`: API externa indisponível — verifique `api_url` nas settings
```

**4. Use frontmatter com tags**
```yaml
---
title: Título claro e descritivo
order: 1
tags: [backup, veeam, m365, sizing]
---
```

**5. Evite ambiguidade em nomes de funções**
```markdown
# ruim
process()

# bom
calculate_m365_storage_sizing(users, mailbox_quota_gb, sharepoint_gb)
```

## Frontmatter YAML disponível

```yaml
---
title: Título da página
order: 5          # posição no índice (menor = primeiro)
tags: [tag1, tag2, tag3]
---
```
