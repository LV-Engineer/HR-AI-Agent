# HR AI Agent

An internal HR analytics chat assistant backed by Claude, combined with document management for
candidate CVs, HR policies, job requirements, and generated PDF reports. Built as a learning
project to practice a production-shaped agentic architecture: a strict tool-calling boundary
between the user-facing API and the LLM's data access, pgvector-based semantic search/matching,
and a full React frontend around it.

The app is HR-only — there is no role-based access control. Every authenticated user can see all
candidates, policies, job requirements, reports, and their own chat history.

## Tech Stack

**Backend**
- Python 3.13, [FastAPI](https://fastapi.tiangolo.com/), SQLAlchemy 2.0, Pydantic
- PostgreSQL 16 (`pgvector/pgvector` image) with the `pgvector` extension for embedding
  similarity search
- Redis — rate-limit storage (`slowapi`)
- [Ollama](https://ollama.com/) running `bge-m3` — local embeddings for CVs, policies, and job
  requirements
- Anthropic Claude — the chat agent, via a tool-calling loop over MCP
- [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) — the tool server the LLM
  calls, isolated with **read-only** DB credentials
- ReportLab + Matplotlib — generated PDF reports (charts, tables, formatted conclusions)
- JWT access tokens + rotated, hashed opaque refresh tokens
- `uv` for dependency management, `pytest` + `testcontainers` for tests, `mypy --strict`

**Frontend**
- React 19, Vite, TypeScript
- Tailwind CSS v4, shadcn/ui (Radix UI primitives)
- React Router, React Hook Form + Zod
- `react-markdown` (chat/report rendering), Sonner (toasts)
- Vitest + React Testing Library

**Infra**
- Docker Compose (5 services: postgres, redis, ollama, agent-service, mcp-server, plus frontend
  served via nginx)
- GitHub Actions CI

## Project Structure

```
hr-ai-agent/
├── agent-service/            # User-facing API — the only service with read-write DB access and auth
│   ├── app/
│   │   ├── auth/              # login, refresh (rotation + theft detection), JWT
│   │   ├── candidates/        # CV upload / list / view / delete
│   │   ├── conversations/     # chat history + SSE /query endpoint (calls mcp-server as the LLM's tool backend)
│   │   ├── job_requirements/
│   │   ├── policies/
│   │   ├── reports/           # lists/serves/deletes generated PDFs directly from disk (no DB row)
│   │   ├── core/               # config, db session, auth deps, rate limiting, the Claude tool-calling loop, embeddings
│   │   └── main.py
│   └── tests/                  # mirrors app/ layout; spins up a real Postgres via testcontainers
├── mcp-server/                # MCP tool server exposed to the LLM — read-only DB access, enforced at the DB role level too
│   ├── app/
│   │   ├── core/                # db, candidate/vacancy matching, policy search, PDF report generation
│   │   ├── assets/fonts/         # fonts for PDF reports
│   │   └── server.py             # the 5 MCP tools: get_schema, query_database, search_hr_policy, match_candidate, generate_report
│   └── tests/
├── db/
│   ├── init/                   # one-time schema init (staff / auth / documents / chat schemas + the read-only DB role)
│   └── seed/                   # seed_staff.py — populates the staff schema with fake org data (employees, salaries, departments...)
├── frontend/
│   └── src/
│       ├── api/                  # typed fetch wrappers per domain
│       ├── features/             # auth, chat, candidates, policies, job-requirements, reports
│       ├── components/           # shared UI (shadcn/ui-based)
│       ├── layouts/              # AppShell — sidebar nav, conversation list
│       └── lib/
├── storage/                    # bind-mounted PDF storage: cv/, policies/, reports/
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Setup & Running

**Prerequisites:** Docker + Docker Compose, an [Anthropic API key](https://console.anthropic.com/).

1. Copy the env template and fill it in:
   ```bash
   cp .env.example .env
   ```
   At minimum set `ANTHROPIC_API_KEY`, `JWT_SECRET_KEY`, Postgres credentials, and
   `COMPANY_EMAIL_DOMAIN` (login emails must match the format `name.surname@<domain>`).

2. Build and start everything:
   ```bash
   docker-compose up --build
   ```
   This starts `postgres` (:5432), `redis`, `ollama` (:11434), `agent-service` (:8000),
   `mcp-server` (:8001, MCP protocol only — not a browsable API), and `frontend` (:8080).

3. Pull the embedding model into Ollama (required before uploading any CV/policy or matching a
   job requirement):
   ```bash
   docker exec -it ollama ollama pull bge-m3
   ```

4. Create a user. There is no self-registration — users are created directly in Postgres via a
   SQL function:
   ```bash
   docker exec -it postgres-db bash
   psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT auth.create_user('name.surname@yourdomain.com', 'yourpassword');"
   ```

5. (Optional) Seed baseline HR data into the `staff` schema:
   ```bash
   cd db/seed
   uv sync
   uv run python seed_staff.py
   ```

6. Open `http://localhost:8080` and log in.

## Tests

**Backend** (`agent-service/` and `mcp-server/`, each with its own `uv`-managed venv):
```bash
cd agent-service   # or mcp-server
uv sync
uv run pytest
uv run pytest --cov=. --cov-report=term-missing   # with coverage
uv run mypy                                        # strict mode — run bare, not `uv run mypy .`
```
Tests spin up a **real** Postgres (`testcontainers`, `pgvector/pgvector:pg16`) and run
`db/init/*.sql` against it — the database layer isn't mocked.

**Frontend:**
```bash
cd frontend
npm install
npm test              # vitest, watch mode
npm test -- run       # single run (what CI uses)
```

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`, as three independent jobs:

| Job | Steps |
|---|---|
| `agent-service` | `uv sync` → `uv run mypy` → `uv run pytest --cov=. --cov-report=term-missing` |
| `mcp-server` | `uv sync` → `uv run mypy` → `uv run pytest --cov=app --cov-report=term-missing` |
| `frontend` | `npm ci` → `npm run build` → `npm test -- run` |
