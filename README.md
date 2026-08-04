<!--
[mcp-local harness] feature: docs-readme-v2-update | plano: 06a9bd54 | 2026-08-04 11:03:06
Atualiza README para refletir v2.0.0: RBAC + Supabase Auth completos e testados, guia de conexao a infra real por ERP filho, pegadinhas conhecidas
-->
# erp-core-template

Template base para sistemas ERP/CRM web, responsivos (desktop e mobile),
com autenticação (local + Google via Supabase Auth), controle de acesso
por módulo (RBAC) e CI/CD integrado ao GitHub. Serve como marco zero
para derivar instâncias de ERP isoladas por negócio.

**Versão atual: `v2.0.0`** — RBAC completo e Supabase Auth (login local
+ Google OAuth) implementados, testados de ponta a ponta em produção
(via o ERP `gasfavero`, primeira instância derivada) e validados por
smoke test neste próprio repositório. Todo ERP novo deve nascer a
partir desta tag, não da `main` correndo solta:

```powershell
git clone --branch v2.0.0 https://github.com/ricardoshuree/erp-core-template.git meu-novo-erp
```

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.14, FastAPI, SQLModel, Alembic, Argon2 |
| Frontend | React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Router |
| Banco | PostgreSQL via Supabase (produção) / SQLite in-memory (testes) |
| Auth | **Supabase Auth** — login local (e-mail/senha) + Google OAuth, testados e funcionando |
| Deploy | Vercel (frontend) + Railway (backend, via Dockerfile) |
| CI/CD | GitHub Actions |
| Dev | uv, mcp-local (servidor MCP local, opcional, ignorado pelo git) |

---

## Estrutura

```
erp-core-template/
├── backend/
│   ├── app/
│   │   ├── alembic/versions/   ← migrations de banco (inclui RBAC)
│   │   ├── api/routes/         ← endpoints FastAPI
│   │   ├── core/               ← config, db, security, supabase_auth
│   │   └── models.py           ← todos os modelos SQLModel (inclui RBAC)
│   └── tests/rbac/              ← testes de RBAC (SQLite, sem Docker)
├── frontend/
│   ├── vite.config.ts          ← outDir: "dist" (Vercel espera isso)
│   ├── vercel.json             ← rewrite catch-all p/ SPA routing
│   └── src/
│       ├── components/Sidebar/ ← menu lateral dinâmico por role
│       ├── hooks/
│       │   ├── useAuth.ts      ← autenticação (local + Google/Supabase)
│       │   └── usePermissions.ts ← permissões por módulo
│       ├── lib/supabase.ts     ← cliente Supabase (só auth, dados via backend)
│       └── routes/login.tsx    ← form local + botão "Continuar com Google"
├── .github/workflows/
│   ├── test-rbac.yml           ← CI: roda testes RBAC a cada push/PR
│   └── ...                     ← outros workflows do template original
├── .env.example                 ← variáveis necessárias (sem valores reais)
├── activate.ps1                 ← ativa venv do backend no Windows/VS Code
└── mcp-local/                   ← servidor MCP local (ignorado pelo git)
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

Roles e módulos padrão criados automaticamente na primeira inicialização
(idempotente, seguro rodar N vezes):
- **Roles**: `admin` (leitura + edição), `editor` (leitura + edição), `viewer` (somente leitura)
- **Módulos**: `usuarios`, `configuracoes`

Proteção de rota no backend via `require_module_permission(module_name,
need_edit=False)` (factory de `Depends` em `deps.py`) — superusuários
passam direto, os demais precisam de `RolePermission.can_read`/`can_edit`
no módulo. No frontend, `usePermissions()` consome
`GET /api/v1/users/me/permissions` e expõe `canRead(module)` /
`canEdit(module)` para gatear UI e menu lateral.

Para adicionar um novo módulo num ERP filho:
1. Crie a migration Alembic inserindo o módulo na tabela `module` (ou
   adicione em `DEFAULT_MODULES`, em `backend/app/core/db.py`, se for
   um módulo padrão que todo ERP deveria ter)
2. Proteja as rotas correspondentes com `require_module_permission("nome-do-modulo")`
3. Adicione a entrada em `frontend/src/components/Sidebar/AppSidebar.tsx`
   no array `MODULE_ITEMS` com o mesmo nome de módulo

---

## Autenticação — local + Google OAuth (Supabase Auth)

**Já implementado e testado — não é mais um "próximo passo".** Fluxo:

- **Login local** (e-mail/senha): `POST /api/v1/login/access-token`
  gera um JWT assinado com `SECRET_KEY` local.
- **Login Google**: `useAuth().loginWithGoogle()` chama
  `supabase.auth.signInWithOAuth({ provider: "google", redirectTo:
  window.location.origin })`. O Supabase redireciona pro Google, volta
  com o consent, e a sessão resultante é sincronizada com
  `localStorage["access_token"]` via `useSupabaseSessionSync()`
  (`frontend/src/hooks/useAuth.ts`).
- **Backend**: `get_current_user` (`backend/app/api/deps.py`) tenta
  decodificar o token como JWT local primeiro; se falhar, tenta validar
  como JWT do Supabase via JWKS (`verify_supabase_token`, em
  `backend/app/core/supabase_auth.py`) — sem precisar de segredo
  compartilhado, só a `SUPABASE_URL`. Um usuário Google que ainda não
  existe localmente é criado por e-mail, **sem role nenhuma** — um
  admin precisa atribuir role manualmente antes do usuário ter qualquer
  permissão além do próprio perfil.

Cada ERP filho precisa do seu próprio projeto Supabase com Auth
configurado (ver seção "Conectando um ERP filho" abaixo) — isto aqui no
template é só o código, não uma instância viva de Supabase.

---

## Como rodar localmente

### Pré-requisitos

- Python 3.14+ — `winget install Python.Python.3.14` (Windows)
- uv — `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)
- Node.js 20+ — https://nodejs.org

### Backend

```powershell
cp .env.example .env
# Edite .env com seus valores locais -- SUPABASE_URL agora e OBRIGATORIO
# (pode ser um placeholder tipo https://placeholder-dev.supabase.co se
# voce so quer rodar localmente sem testar login Google de verdade)

uv sync
. .\activate.ps1

cd backend
uv run alembic upgrade head        # aplica as migrations (inclui RBAC)
uv run python -m app.initial_data  # cria superuser e seed de roles/módulos
uv run uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000 — Docs: http://localhost:8000/docs

### Frontend

Crie `frontend/.env` (não commitado) com:

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=<mesma SUPABASE_URL do backend>
VITE_SUPABASE_ANON_KEY=<mesma SUPABASE_ANON_KEY do backend, ou vazio p/ dev sem Google>
```

```bash
cd frontend
npm install   # ou: bun install
npm run dev   # ou: bun dev
```

App: http://localhost:5173

### Testes

```powershell
cd backend
uv run pytest tests/rbac/ -v   # roda sem banco externo (SQLite in-memory)
```

**Smoke test completo** (rodado e validado antes de fechar a `v2.0.0`):
```powershell
uv sync
cd backend
uv run python -c "from app.core.config import settings; print('OK:', settings.SUPABASE_URL)"
uv run pytest tests/rbac/ -v
cd ../frontend
npm install
npm run build
Test-Path dist/index.html   # precisa dar True
```

---

## Conectando um ERP filho ao Supabase, Railway e Vercel

**Este template não tem projeto Supabase/Railway/Vercel próprio.** Cada
ERP derivado precisa provisionar sua própria infraestrutura — isso
nunca faz parte do template (credenciais são por definição locais a
cada instância). Roteiro completo, na ordem:

### 1. Criar projeto no Supabase

1. https://supabase.com/dashboard → Novo projeto → região mais próxima
   do público final (`South America (São Paulo)` para clientes BR)
2. Gere a senha do banco só com caracteres alfanuméricos — a URI de
   conexão em `backend/app/core/config.py` não escapa caracteres
   especiais (dívida técnica conhecida, ver nota no fim desta seção)
3. Em **Project Settings → API**, anote `Project URL` (→
   `SUPABASE_URL`), Publishable key (→ `SUPABASE_ANON_KEY`) e Secret
   key (→ `SUPABASE_SERVICE_ROLE_KEY`)
4. Recomendado: `Enable automatic RLS` ligado, `Automatically expose
   new tables` desligado — o backend acessa o Postgres direto via
   SQLModel, não pela API REST autogerada do Supabase. O RBAC deste
   template é aplicado em nível de aplicação (FastAPI `Depends`), não
   via Postgres RLS.
5. Conexão via **Session pooler** (porta 5432), não Transaction pooler
   — o backend roda como processo persistente (Railway), não serverless.

### 2. Configurar Google OAuth (se o ERP for usar login Google)

1. https://console.cloud.google.com/apis/credentials → crie um projeto
   dedicado (um por ERP) → **OAuth consent screen** → modo **Testing**
   é suficiente para uso interno
2. **Credentials → Create Credentials → OAuth client ID** → Web application
3. Em **Authorized redirect URIs**, adicione:
   `https://<seu-projeto>.supabase.co/auth/v1/callback`
4. Em **Google Auth Platform → Audience → Test users**, adicione os
   e-mails que vão logar (obrigatório em modo Testing)
5. No Supabase: **Authentication → Sign In / Providers → Google** →
   **ative o toggle "Enable Sign in with Google"** (vem desligado por
   padrão, mesmo com Client ID/Secret preenchidos — passo fácil de
   esquecer) → cole Client ID e Secret → Save

### 3. Configurar URLs de autenticação no Supabase

Em **Authentication → URL Configuration** (nasce com valores de
localhost, precisa trocar):
- **Site URL**: `https://<dominio-do-frontend>.vercel.app`
- **Redirect URLs**: adicione o mesmo domínio, e opcionalmente um
  wildcard pra preview deployments (`https://<projeto>-*-<time>.vercel.app`)

### 4. Variáveis de ambiente

Backend (`.env` local + Variables do Railway):
```env
PROJECT_NAME=<nome-do-erp>
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_ANON_KEY=<publishable-key>
SUPABASE_SERVICE_ROLE_KEY=<secret-key>
POSTGRES_SERVER=<host-do-pooler>
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=<usuario-do-pooler>
POSTGRES_PASSWORD=<senha-do-banco>
SECRET_KEY=<secrets.token_urlsafe(32)>
FIRST_SUPERUSER=<email-admin-inicial>
FIRST_SUPERUSER_PASSWORD=<senha-forte>
BACKEND_CORS_ORIGINS=https://<dominio-do-frontend>.vercel.app
```

Frontend (Variables do projeto na Vercel):
```env
VITE_API_URL=https://<seu-backend>.up.railway.app
VITE_SUPABASE_URL=<mesma SUPABASE_URL do backend>
VITE_SUPABASE_ANON_KEY=<mesma SUPABASE_ANON_KEY do backend>
```

### 5. Aplicar migrations no Supabase

```powershell
cd backend
uv run alembic upgrade head
uv run python -m app.initial_data
```

### 6. Railway (backend)

1. New Project → Deploy from GitHub repo → repositório do ERP
2. **Settings → Source → Root Directory**: `backend`
3. Garanta que existe um `backend/Dockerfile` simples e exclusivo do
   backend (não builda o frontend junto) — Railway detecta e usa
   automaticamente. Custom Build/Start Command **vazios** (tudo no
   Dockerfile).
4. Configure as variáveis de ambiente (seção 4 acima) via **Variables → Raw Editor**
5. **Networking → Generate Domain**
6. Valide em `<dominio>/docs` que a API responde

### 7. Vercel (frontend)

1. New Project → importa o repositório do ERP
2. **Root Directory**: `frontend` (Framework preset Vite, auto-detectado)
3. Variáveis de ambiente (seção 4 acima)
4. Deploy
5. Confirme depois do deploy que buildou certo — se der "No Output
   Directory named dist", confira se `frontend/vite.config.ts` tem
   `outDir: "dist"` (deve ter, já vem certo no template a partir da
   `v2.0.0`)
6. Se renomear o projeto na Vercel pra um domínio mais curto: o domínio
   `.vercel.app` **não migra sozinho** — precisa editar manualmente em
   **Settings → Domains**
7. Volte no Google Cloud Console e no Supabase (seções 2 e 3) e
   atualize as URLs com o domínio final da Vercel

### ⚠️ Pegadinhas conhecidas (todas já corrigidas no código deste
### template a partir da `v2.0.0`, documentadas aqui para contexto)

- **`BACKEND_CORS_ORIGINS` vazio faz o frontend falhar com "Network
  Error" genérico**, mesmo que o backend responda 200 — o navegador
  bloqueia a resposta por falta de header CORS antes dela chegar no JS.
  Só aparece no log do servidor, nunca na aba de rede do navegador.
- **Provider Google no Supabase nasce desabilitado**, mesmo com projeto
  GCP certo — precisa ativar manualmente o toggle.
- **Site URL do Supabase nasce como `localhost:3000`** — trocar antes
  de testar login Google em produção.
- **Nunca editar arquivos `.json` (`package.json`, `vercel.json`, etc.)
  via ferramentas de escrita de MCPs locais tipo `mcp-local`** — elas
  costumam injetar um comentário de rastreabilidade `# ...` no topo do
  arquivo, o que é inválido em JSON e quebra o parse no build. Editar
  `.json` sempre via terminal ou editor de texto direto.
- **Dívida técnica conhecida, ainda não corrigida**: `backend/app/core/config.py`
  monta a URI de conexão do Postgres concatenando usuário/senha sem
  escapar caracteres especiais (`urllib.parse.quote_plus` resolveria).
  Enquanto isso, use senha de banco só com caracteres alfanuméricos.

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

```powershell
# 1. Clone a partir da tag estavel (nunca da main correndo solta)
git clone --branch v2.0.0 https://github.com/ricardoshuree/erp-core-template.git meu-novo-erp
cd meu-novo-erp

# 2. Aponte para o novo repositório GitHub
git remote set-url origin https://github.com/ricardoshuree/meu-novo-erp.git
git push -u origin main

# 3. (opcional) Clone o mcp-local para desenvolvimento assistido
git clone https://github.com/ricardoshuree/mcp-local.git mcp-local
cd mcp-local
# Edite config.yaml: project_name = mcp-meu-novo-erp
uv sync
uv run start.py   # registra no Claude Desktop
cd ..

# 4. Configure o .env com as credenciais do novo projeto
cp .env.example .env
# preencher com valores reais -- ver "Conectando um ERP filho" acima

# 5. Crie as migrations dos módulos específicos do negócio
cd backend
uv run alembic revision --autogenerate -m "add modulos <nome-do-erp>"
uv run alembic upgrade head
```

A partir daí, adicione os módulos e rotas específicos do negócio. RBAC,
Auth (local + Google), CI/CD e estrutura base já vêm prontos e
testados — o trabalho real fica concentrado em: (a) provisionar a
infraestrutura própria (Supabase/Railway/Vercel, seção acima) e (b)
construir as telas e regras de negócio específicas do cliente.

---

## Plataformas de hospedagem

| Serviço | Plataforma | O que cobre |
|---|---|---|
| Frontend | Vercel | Build e deploy automático via GitHub |
| Backend | Railway | Deploy do FastAPI via Dockerfile, auto-deploy via GitHub |
| Banco + Auth | Supabase | PostgreSQL gerenciado, Auth, RLS |

---

## Histórico de versões

- **`v2.0.0`** — RBAC completo + Supabase Auth (local + Google OAuth)
  implementados, testados de ponta a ponta em produção (via `gasfavero`,
  primeiro ERP derivado) e validados por smoke test neste repositório
  (Settings instancia sem erro, 10/10 testes RBAC passam, build gera
  `dist/index.html` no lugar certo). Corrige bugs herdados do template
  original: `outDir` do Vite incompatível com deploy Vercel separado,
  `app.frontend()` incondicional derrubando o backend quando rodado
  isolado (sem frontend no mesmo container).
- **`v1.0.0`** — RBAC básico (roles, módulos, permissões), auth JWT
  local, CI de testes RBAC. Fork inicial de
  [`fastapi/full-stack-fastapi-template`](https://github.com/fastapi/full-stack-fastapi-template).
