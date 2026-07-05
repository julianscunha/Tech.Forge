# TechForge — Guia de Setup (Windows)

## Pré-requisitos

| Software | Versão mínima | Download |
|---|---|---|
| Python | 3.11+ | https://python.org/downloads |
| Node.js | 18+ | https://nodejs.org |
| Git (opcional) | — | https://git-scm.com |

---

## Passo 1 — Preparar a estrutura

Extraia o ZIP para uma pasta de sua escolha.  
Exemplo: `C:\TechForge\`

A estrutura deve ficar assim:
```
C:\TechForge\
├── core\
│   ├── backend\
│   └── frontend\
├── modules\
│   ├── installed\
│   └── repository\
├── sdk\
├── cli\
└── config\
```

---

## Passo 2 — Backend (Python / FastAPI)

Abra o **PowerShell** ou **Prompt de Comando** como administrador.

```powershell
# Entrar na pasta do backend
cd C:\TechForge\core\backend

# Criar ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Copiar configuração
copy ..\..\config\.env.example ..\..\config\.env

# Subir o servidor
python run.py
```

O backend estará disponível em: http://127.0.0.1:8000  
Documentação da API: http://127.0.0.1:8000/api/docs

### Saída esperada ao subir corretamente

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started server process
INFO:     Waiting for application startup.
INFO: TechForge 1.0.0 starting up…
INFO: Database initialized.
INFO: Module loaded: Hello World v1.0.0 (Examples)
INFO: Module loaded: Veeam M365 Sizing v1.0.0 (Backup)
INFO: Module scan complete: 2 installed, 0 invalid, 0 incompatible.
INFO:     Application startup complete.
```

> **Os erros `test_module` e `unknown` são normais** — são resíduos de
> diretórios de teste criados durante o desenvolvimento. Podem ser ignorados.
> Para eliminá-los, delete as pastas:
> `modules\installed\test_module\` e `modules\installed\unknown\`

---

## Passo 3 — Frontend (React / Vite)

Abra **outro terminal** (mantenha o backend rodando).

```powershell
# Entrar na pasta do frontend
cd C:\TechForge\core\frontend

# Instalar dependências (necessário apenas na primeira vez)
npm install

# Iniciar o servidor de desenvolvimento
npm run dev
```

O frontend estará disponível em: http://localhost:5173

### Saída esperada

```
  VITE v5.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

Abra http://localhost:5173 no navegador.

---

## Passo 4 — Verificar que tudo funciona

1. Abra http://localhost:5173
2. O Dashboard deve carregar e exibir:
   - Backend: **Online**
   - Banco de Dados: **Conectado**
3. Na Sidebar esquerda deve aparecer a hierarquia:
   ```
   Backup
   └── Veeam
       └── Veeam M365 Sizing
   Examples
   └── TechForge
       └── Hello World
   ```
4. A página **Módulos** deve listar os dois módulos com status `INSTALLED`

---

## Problemas comuns no Windows

### `python` não reconhecido

Use `py` em vez de `python`:
```powershell
py -m venv .venv
py run.py
```

### Erro de permissão no `.venv\Scripts\activate`

Execute no PowerShell como administrador:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `npm` não reconhecido

Reinstale o Node.js em https://nodejs.org e marque a opção "Add to PATH".

### Erro `ModuleNotFoundError: No module named 'yaml'`

O pyyaml não foi instalado. Execute:
```powershell
pip install -r requirements.txt
```
ou individualmente:
```powershell
pip install pyyaml fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings python-dotenv
```

### Frontend mostra tela em branco

1. Verifique que o backend está rodando em http://127.0.0.1:8000
2. Abra o console do navegador (F12) e procure erros de rede
3. Garanta que o `npm install` foi executado antes do `npm run dev`

### Erro CORS (Frontend não consegue chamar o backend)

Verifique o arquivo `config\.env`:
```
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

### Caminhos com espaços (ex: `C:\Usuários\Juliano\Downloads`)

Prefira extrair o projeto para um caminho sem espaços ou acentos:
- `C:\TechForge\` ✓
- `C:\Projects\techforge\` ✓
- `C:\Usuários\Juliano\Downloads\techforge\` ✗ (pode causar problemas)

---

## Estrutura de portas

| Serviço | Porta | URL |
|---|---|---|
| Backend (FastAPI) | 8000 | http://127.0.0.1:8000 |
| Frontend (Vite dev) | 5173 | http://localhost:5173 |
| API Docs (Swagger) | 8000 | http://127.0.0.1:8000/api/docs |

O Vite dev server já tem proxy configurado: qualquer chamada para `/api/*`
é redirecionada automaticamente para `http://127.0.0.1:8000`.

---

## Sobre os 404 no log do backend

```
GET / HTTP/1.1  404 Not Found
GET /favicon.ico HTTP/1.1  404 Not Found
```

Esses erros são **completamente normais** — o FastAPI não serve o frontend.
O frontend é servido pelo Vite em `localhost:5173`.
Acesse sempre pelo Vite, não diretamente pelo backend.

---

## Remover módulos de teste inválidos (opcional)

```powershell
# Na raiz do projeto
rmdir /s /q modules\installed\test_module
rmdir /s /q modules\installed\unknown
```

Após isso, ao subir o backend você verá apenas:
```
INFO: Module scan complete: 2 installed, 0 invalid, 0 incompatible.
```
