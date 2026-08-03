<!--
[mcp-local harness] feature: docs | plano: d31a2728 | 2026-08-03 15:42:42
README completo com stack, estrutura, como rodar localmente, Supabase Auth passo a passo, CI/CD e como derivar um novo ERP
-->
# erp-core-template

Template base para sistemas ERP/CRM web, responsivos (desktop e mobile),
com autenticação, controle de acesso por módulo (RBAC) e CI/CD integrado
ao GitHub. Serve como marco zero para derivar instâncias de ERP isoladas
por negócio.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, FastAPI, SQLModel, Alembic, Argon2 |
| Frontend | React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Router |
| Banco | PostgreSQL (produção) / SQLite in-memory (testes) |
| Auth | JWT próprio (pronto para migrar para Supabase Auth) |
| Deploy | Vercel (frontend) + Railway (backend) |
| CI/CD | GitHub Actions |
| Dev | uv, Docker Compose (futuro), mcp-local-erp |

---

## Estrutura

```
erp-core-template/
├── backend/
│   ├── app/
│   │   ├── alembic/versions/   ← migrations de banco
│   │   ├── api/routes/         ← endpoints FastAPI
│   │   ├── core/               ← config, db, security
│   │   └── models.py           ← todos os modelos SQLModel
│   └── tests/
│       └── rbac/               ← testes de RBAC (SQLite, sem Docker)
├── frontend/
│   └── src/
│       ├── components/Sidebar/ ← menu lateral dinâmico por role
│       ├── hooks/
│       │   ├── useAuth.ts      ← autenticação JWT
│       │   └── usePermissions.ts ← permissões por módulo
│       └── routes/             ← páginas do app
├── .github/workflows/
│   ├── test-rbac.yml           ← CI: roda testes RBAC a cada push/PR
│   └── ...                     ← outros workflows do template original
├── .env.example                ← variáveis necessárias (sem valores reais)
├── activate.ps1                ← ativa venv do backend no Windows/VS Code
└── mcp-local/                  ← servidor MCP local (ignorado pelo git)
```

---

## Módulo de segurança — RBAC

O controle de acesso é baseado em quatro tabelas:

```
Role           → papel do usuário ("admin", "editor", "viewer")
Module         → módulo do sistema ("clientes", "financeiro", "estoque"...)
RolePermission → matriz role × módulo com can_read e can_edit
UserRole       → associação usuário × role
```

Roles e módulos padrão criados automaticamente na primeira inicialização:
- **Roles**: `admin` (leitura + edição), `editor` (leitura + edição), `viewer` (somente leitura)
- **Módulos**: `usuarios`, `configuracoes`

O menu lateral do frontend é renderizado dinamicamente com base nas
permissões do usuário logado. Para adicionar um novo módulo num ERP filho:
1. Crie a migration Alembic inserindo o módulo na tabela `module`
2. Adicione a entrada em `frontend/src/components/Sidebar/AppSidebar.tsx`
   no array `MODULE_ITEMS` com o mesmo nome de módulo

---

## Como rodar localmente

### Pré-requisitos

- Python 3.12+ — `winget install Python.Python.3.12` (Windows)
- uv — `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)
- Node.js 20+ — https://nodejs.org

### Backend

```powershell
# Na raiz do projeto
cp .env.example .env
# Edite .env com seus valores locais

uv sync
. .\activate.ps1          # ativa o venv (Windows)

cd backend
uv run alembic upgrade head   # aplica as migrations
uv run python -m app.initial_data  # cria superuser e seed de roles/módulos
uv run uvicorn app.main:app --reload --port 8000
```

API disponível em: http://localhost:8000
Documentação interativa: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install   # ou: bun install
npm run dev   # ou: bun dev
```

App disponível em: http://localhost:5173

### Testes

```powershell
cd backend
pytest tests/rbac/ -v   # roda sem banco externo (SQLite in-memory)
```

---

## Configurar Supabase Auth (passo a passo — antes do deploy)

O template usa JWT próprio por padrão. Para migrar para Supabase Auth
(que adiciona login com Google e gerenciamento de sessão hospedado):

### 1. Criar projeto no Supabase

1. Acesse https://supabase.com e crie uma conta
2. Crie um novo projeto (um por instância de ERP, um por ambiente)
3. Anote as três chaves em **Project Settings → API**:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` → `SUPABASE_ANON_KEY`
   - `service_role secret` → `SUPABASE_SERVICE_ROLE_KEY`

### 2. Configurar Google OAuth (opcional)

1. Acesse https://console.cloud.google.com
2. Crie um projeto → APIs & Services → Credentials → OAuth 2.0 Client ID
3. Em Authorized redirect URIs adicione: `https://<seu-projeto>.supabase.co/auth/v1/callback`
4. No Supabase: Authentication → Providers → Google → cole Client ID e Secret

### 3. Adicionar variáveis de ambiente

No `.env` local e nas variáveis de ambiente do Railway (backend) e Vercel (frontend):

```env
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_ANON_KEY=<chave-anon>
SUPABASE_SERVICE_ROLE_KEY=<chave-service-role>
```

### 4. Substituir o fluxo de autenticação

Os arquivos a modificar estão marcados com o comentário
`# TODO: substituir por Supabase Auth`:

- `backend/app/api/deps.py` → `get_current_user`: trocar decodificação JWT
  local pela verificação do token Supabase via `SUPABASE_SERVICE_ROLE_KEY`
- `backend/app/api/routes/login.py` → remover endpoint de login próprio;
  o Supabase passa a gerenciar login, registro e recuperação de senha
- `frontend/src/hooks/useAuth.ts` → substituir `LoginService` pelo
  cliente Supabase (`@supabase/supabase-js`)

### 5. Manter o RBAC intacto

As tabelas `role`, `module`, `role_permission` e `user_role` continuam
no seu Postgres (via Supabase). Apenas a camada de autenticação muda —
o RBAC permanece funcionando exatamente como está.

---

## CI/CD

A cada push ou PR na `main`, o GitHub Actions executa automaticamente:

| Workflow | O que faz | Tempo |
|---|---|---|
| `test-rbac.yml` | 10 testes RBAC com SQLite, sem Docker | ~25s |

Para ativar o gate de qualidade (bloquear merge se os testes falharem):
GitHub → Settings → Branches → Add rule → `main` → marcar
"Require status checks to pass" → selecionar "RBAC unit tests"

---

## Como derivar um novo ERP a partir deste template

```bash
# 1. Clone o template para uma nova pasta
git clone https://github.com/ricardoshuree/erp-core-template.git erp-gasfavero
cd erp-gasfavero

# 2. Aponte para o novo repositório GitHub
git remote set-url origin https://github.com/ricardoshuree/erp-gasfavero.git
git push -u origin main

# 3. Clone o mcp-local para desenvolvimento
git clone https://github.com/ricardoshuree/mcp-local.git mcp-local
cd mcp-local
# Edite config.yaml: project_name = mcp-gasfavero
uv sync
uv run start.py   # registra no Claude Desktop

# 4. Configure o .env com as credenciais do novo projeto
cp .env.example .env

# 5. Crie as migrations dos módulos específicos do negócio
cd backend
uv run alembic revision --autogenerate -m "add modulos erp-gasfavero"
uv run alembic upgrade head
```

A partir daí, adicione os módulos e rotas específicos do negócio.
O RBAC, auth, CI/CD e estrutura base já estão prontos.

---

## Plataformas de hospedagem

| Serviço | Plataforma | O que cobre |
|---|---|---|
| Frontend | Vercel | Build e deploy automático via GitHub |
| Backend | Railway | Deploy do FastAPI, auto-deploy via GitHub |
| Banco + Auth | Supabase | PostgreSQL gerenciado, Auth, RLS |

Deploy automático completo com Docker será configurado em etapa posterior.
