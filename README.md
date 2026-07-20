# PG AI Assistant

A natural-language-to-SQL assistant for PostgreSQL. It has three independently
runnable components:

| Component | Folder | Tech | Default URL |
|---|---|---|---|
| Backend API | `text_to_sql_backend` | FastAPI (Python) | http://localhost:8010 |
| MCP server | `text_to_sql_mcp` | FastMCP / Starlette (Python) | http://localhost:8020 |
| Frontend | `text_to_sql_frontend` | React + MUI + Vite | http://localhost:5173 |

The backend stores its data (users, encrypted credentials, chat history) in a
local **SQLite** database that is created automatically on first run — no
separate database server needs to be installed for the app itself.

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** (with npm)
- A **PostgreSQL** database you want to query (added later through the UI)

---

## 1. Backend API — `text_to_sql_backend`

```powershell
cd text_to_sql_backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# create your .env from the template, then edit it
Copy-Item .env.example .env
# Set at least: JWT_SECRET, DATA_ENCRYPTION_KEY, DB_CONNECTION_TOKEN_SECRET

python run.py
```

Runs at http://localhost:8010. The SQLite database and tables are created
automatically via `init_db()` — there is no migration step.

## 2. MCP server — `text_to_sql_mcp` (new terminal)

```powershell
cd text_to_sql_mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# create your .env from the template
Copy-Item .env.example .env
# IMPORTANT: DB_CONNECTION_TOKEN_SECRET must be IDENTICAL to the backend's value

python server.py
```

Runs at http://localhost:8020.

> ⚠️ `DB_CONNECTION_TOKEN_SECRET` **must match** the value in the backend `.env`,
> otherwise database-connection tokens issued by the backend will be rejected.

## 3. Frontend — `text_to_sql_frontend` (new terminal)

```powershell
cd text_to_sql_frontend
npm install

# optional: only needed if the backend is not on http://localhost:8010
Copy-Item .env.example .env

npm run dev
```

Open http://localhost:5173.

---

## First-time setup (in the browser)

1. Open http://localhost:5173 and **sign up** — this creates the first account.
2. Go to **Settings** and add an **LLM provider + API key**
   (OpenAI / Anthropic / Gemini / Groq / Azure OpenAI / Bedrock). Keys are
   entered in the UI and stored encrypted in the database, not in `.env`.
3. Add a **database connection** for the PostgreSQL database you want to query.

You can now ask questions in natural language and get generated SQL, results,
explanations, ER diagrams, and charts.

---

## Environment variables

Each app ships a `.env.example`. Copy it to `.env` and fill in real values —
never commit the real `.env`.

| App | Variable | Required | Notes |
|---|---|---|---|
| backend | `JWT_SECRET` | yes | random secret for auth tokens |
| backend | `DATA_ENCRYPTION_KEY` | yes | encrypts stored DB creds & API keys |
| backend | `DB_CONNECTION_TOKEN_SECRET` | yes | **must match MCP** |
| backend | `SMTP_*` | optional | only for password-reset emails |
| backend | `DATA_DIR` | optional | override the SQLite data directory |
| backend | `HOST` / `PORT` | optional | server bind address / port (default `0.0.0.0` / `8010`) |
| mcp | `DB_CONNECTION_TOKEN_SECRET` | yes | **must match backend** |
| mcp | `HOST` / `PORT` | optional | server bind address / port (default `0.0.0.0` / `8020`) |
| frontend | `VITE_API_BASE_URL` | optional | backend URL, defaults to `http://localhost:8010` |
| frontend | `FRONTEND_PORT` | optional | Vite dev/preview port (default `5173`) |

> If you change a port, keep the cross-references in sync: the backend's
> `MCP_SERVER_URL` must point at the MCP port, the frontend's `VITE_API_BASE_URL`
> must point at the backend port, and the backend's `CORS_ORIGINS` must include
> the frontend URL.

## Ports summary

| Service | Env var | Default |
|---|---|---|
| Backend API | `PORT` (backend `.env`) | 8010 |
| MCP server | `PORT` (mcp `.env`) | 8020 |
| Frontend (Vite) | `FRONTEND_PORT` (frontend `.env`) | 5173 |

---

## Running the apps on different ports (step by step)

All three ports are read from each app's `.env` file. The three services also
reference each other by URL, so when you change a port you must update the
matching URL in the other apps. Below is an example that moves everything to new
ports:

- Backend: `8010` → `9010`
- MCP: `8020` → `9020`
- Frontend: `5173` → `3000`

### 1. Change the backend port

In `text_to_sql_backend/.env`:

```dotenv
PORT=9010
# Allow the (new) frontend origin to call the API:
CORS_ORIGINS=http://localhost:3000
# Point at the (new) MCP port:
MCP_SERVER_URL=http://localhost:9020/mcp
```

### 2. Change the MCP port

In `text_to_sql_mcp/.env`:

```dotenv
PORT=9020
# Only needed if export/diagram/chart download links must be reachable
# (e.g. behind a proxy); otherwise leave the default:
EXPORT_PUBLIC_BASE_URL=http://localhost:9020
```

### 3. Change the frontend port and point it at the backend

In `text_to_sql_frontend/.env`:

```dotenv
FRONTEND_PORT=3000
# Point the UI at the (new) backend port:
VITE_API_BASE_URL=http://localhost:9010
```

### 4. Restart all three apps

```powershell
# terminal 1 — backend
cd text_to_sql_backend; .\.venv\Scripts\Activate.ps1; python run.py

# terminal 2 — mcp
cd text_to_sql_mcp; .\.venv\Scripts\Activate.ps1; python server.py

# terminal 3 — frontend
cd text_to_sql_frontend; npm run dev
```

Then open the frontend at its new port (e.g. http://localhost:3000).

### Cross-reference checklist

When changing ports, make sure these stay consistent:

| If you change… | Also update… |
|---|---|
| backend `PORT` | frontend `VITE_API_BASE_URL`, backend `CORS_ORIGINS` (frontend origin) |
| mcp `PORT` | backend `MCP_SERVER_URL` (and MCP `EXPORT_PUBLIC_BASE_URL` if used) |
| frontend `FRONTEND_PORT` | backend `CORS_ORIGINS` (must include the new frontend origin) |
