# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

HR analytics AI agent. An HR-only (no roles/RBAC — every authenticated user sees everything) chat
assistant backed by Claude, plus document management (candidate CVs, HR policies, job requirements,
generated PDF reports). Three runtime pieces behind `docker-compose.yml`: **agent-service** (user-facing
API), **mcp-server** (tool server the LLM calls), and Postgres (`pgvector/pgvector` image) shared by both,
plus Redis (rate-limit storage) and Ollama (local embeddings).

## Commands

Each Python project (`agent-service/`, `mcp-server/`, `db/seed/`) has its own `uv`-managed venv.
Run these from inside the respective directory.

```bash
uv sync                                    # install deps
uv run pytest                              # run tests
uv run pytest --cov=. --cov-report=term-missing   # with coverage
uv run pytest tests/candidates/test_service.py -k test_stores_file   # single test
uv run mypy                                # strict mode — run bare, do NOT pass a path/`.`
```

`uv run mypy .` (or any path arg) overrides `[tool.mypy] files = ["app"]` in `pyproject.toml` and pulls
`tests/` into the check, which breaks because `tests/` isn't set up for mypy's module resolution the way
`app/` is.

Tests for both services spin up a **real** Postgres (`testcontainers`, `pgvector/pgvector:pg16`) and run
`db/init/*.sql` against it — no mocking of the database layer.

Docker (local dev, from repo root):
```bash
docker-compose up --build
```
`agent-service` on :8000, `mcp-server` on :8001 (only for the MCP protocol endpoint, not a browsable API),
Postgres on :5432, Ollama on :11434.

Seeding (`db/seed/`, own `uv` venv): `uv run python seed_staff.py`, `seed_documents.py` (HR policies),
`seed_candidate_cv.py`, `seed_job_requirements.py`. These insert directly with admin Postgres credentials
and call Ollama for embeddings — they are not part of any API flow.

`db/init/*.sql` only runs once, when the Postgres container's data volume is first created
(`docker-entrypoint-initdb.d`). Editing these files does nothing for an already-initialized local
`postgres-db` container — apply schema changes to a live container manually (e.g.
`docker exec -i postgres-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'` with SQL piped over
stdin), or accept the data loss from `docker-compose down -v`.

## Architecture

### Why two services, and why their DB permissions differ

`mcp-server` exposes 5 MCP tools to the LLM (`get_schema`, `query_database`, `search_hr_policy`,
`match_candidate`, `generate_report`) and connects to Postgres with **read-only** credentials
(`MCP_DB_USER`, enforced both by `_validate_select_only` in `mcp-server/app/core/db.py` and by an actual
read-only Postgres role — see `db/init/02_schema_auth.sql` grants and
`mcp-server/tests/test_db.py::test_readonly_role_blocked_at_db_level`). This is deliberate: the LLM's
tool-calling loop must never be able to mutate data, however it's prompted.

`agent-service` is the only service with read-write DB credentials and the only one with auth. It owns
everything that writes: login/refresh, conversation persistence, and all document CRUD (CV/policy/job
requirement upload, report deletion). It calls `mcp-server` over the MCP protocol (`mcp_server_url`,
`agent-service/app/core/agent.py`) as the tool backend for chat, not as a data-access API.

`mcp-server` stays a flat, single-layer codebase (`app/core/*.py`, plain functions, `TypedDict` return
types) by deliberate choice — a Controller/Service/Repository split was tried and reverted as unneeded
complexity for its size.

### agent-service: feature-first layout

Each domain owns a package under `app/` with `models.py` / `schemas.py` / `repositories.py` / `service.py`
/ `routes.py`: `auth/`, `conversations/` (also owns `/query`), `candidates/`, `policies/`,
`job_requirements/`, `reports/` (no `models.py`/`repositories.py` — reports have no DB row, see below).
`app/core/` holds only genuinely cross-cutting infra (`config.py`, `db.py` session/engine, `deps.py` auth
dependency, `security.py`, `rate_limit.py`, `agent.py` the Claude tool-calling loop, `embeddings.py`,
`text_extraction.py`). `tests/` mirrors this per-domain layout and every directory has `__init__.py` —
required so pytest doesn't collide two files sharing a basename (e.g. `test_routes.py`) across different
domain directories.

Within a domain: **Controller** (`routes.py`) is HTTP-only — parses input, calls the service, translates a
domain exception to an HTTP status. **Service** holds business logic, raises plain Python exceptions
(never `HTTPException`), and is the only layer that calls `db.commit()` (for atomicity across multiple
repository calls). **Repository** is pure data access and generally doesn't commit (`flush()` at most, to
get a server-generated id back). Create a new exception class only when a caller must react differently to
it (compare `InvalidCredentialsError` vs `UserNotFoundError`, which must stay separate, against
`InvalidRefreshTokenError`, deliberately reused for both "reused" and "expired" refresh tokens so both
return an identical response — leaking which case occurred would be a security bug).

Route handlers whose `Depends(get_current_user)` return value isn't read in the body use
`dependencies=[Depends(get_current_user)]` on the decorator instead of binding an unused parameter.

### Shared Postgres, one database, four schemas

- `staff` — pre-seeded HR data (employees, salaries, departments, vacations); read/query-only, never
  written by either service's application code.
- `auth` — `users`, `refresh_tokens`; owned by `agent-service`.
- `chat` — `conversations`, `messages`; owned by `agent-service`.
- `documents` — `hr_policies`, `candidate_cv`, `job_requirements`, each with a pgvector `embedding vector(1024)`
  column (bge-m3 via Ollama) for similarity search/matching. `candidate_cv.file_path` is `NOT NULL`;
  `hr_policies.file_path` is nullable (three policies were seeded before file upload existed and have no
  file — `PolicyService`/routes 404 rather than crash on those). `job_requirements` intentionally has no
  FK into `staff` (a real deployment's HRIS data wouldn't be something the documents domain can assume
  referential integrity against).

Vectors are mapped with `pgvector.sqlalchemy.Vector` in `agent-service` ORM models; `mcp-server` (no ORM
layer) builds vector literals as strings by hand (`'[' + ','.join(...) + ']'`) — the two approaches coexist
by design, not by inconsistency.

### File storage (CV/policy/report PDFs)

Local disk, mounted into containers via `docker-compose.yml` (`storage/{reports,cv,policies}/`), path kept
in `.env` (`*_STORAGE_DIR`/`REPORTS_DIR`). Uploaded files are written under a random `uuid4()` filename —
never the original filename — because the on-disk name is never exposed; view/download endpoints look the
row up by DB id (or, for reports, validate the requested filename) and set
`Content-Disposition: inline` with the *display* name from the DB, so nothing needs the original filename
to be trustworthy. **Reports have no DB row at all** (`generate_report` in mcp-server just writes a PDF and
returns a path string) — `agent-service/app/reports/service.py` lists/serves/deletes them by reading the
directory directly, and `resolve_report_path` is the path-traversal guard (resolve + verify the result is
still under `REPORTS_DIR`) since, unlike every other domain, the filename comes straight from the URL
rather than a trusted DB column.

### Auth

JWT access token (short-lived) + opaque refresh token, hashed (`hash_refresh_token`, SHA-256) before
storage. Refresh tokens carry a `family_id`; reusing an already-rotated refresh token revokes the entire
family (theft detection) rather than just rejecting the one token.

### Chat / SSE

`POST /query` streams Server-Sent Events (`agent-service/app/conversations/routes.py`). The frontend must
consume this with `fetch()` + manual `ReadableStream` reading — **not** `EventSource`, which can't send an
`Authorization` header or issue a POST. `ask_agent` (`core/agent.py`) only surfaces `tool_use` names as
`step` events and the final text as one `answer` event — it does not currently expose tool *results*
(e.g. a `generate_report` call's returned file path isn't captured anywhere), so nothing today can
associate a generated report with the conversation or user that produced it.

### Testing patterns worth knowing before writing a new test

- `db_session` (both services' `conftest.py`) binds a `Session` to a single connection with
  `join_transaction_mode='create_savepoint'` and rolls back at teardown — commits inside application code
  become savepoints, invisible outside that one connection.
- Most service/route code takes the injected session directly, so the plain `client`/`db_session` fixtures
  are sufficient. The one exception is `ConversationService.persist_user_message`/`persist_assistant_message`,
  `@staticmethod`s that each open their own `SessionLocal()` (because they must still run after the SSE
  generator's request-scoped session may have closed) — tests that exercise them need the
  `real_client`/`real_conversation_id` fixtures (`tests/conversations/test_query_routes.py`,
  `tests/conversations/test_service.py`), which use genuinely committed sessions plus explicit cleanup
  instead of rollback. The user's message is persisted immediately, before calling `ask_agent`, precisely so
  it survives a mid-stream client disconnect even though the assistant's answer (persisted only after the
  stream completes) would not.
- Patch a module-level function (e.g. `get_embedding`, `ask_agent`) where it's *imported into and called
  from*, not where it's defined — e.g. `monkeypatch.setattr(app.candidates.service, 'get_embedding', ...)`.

## Frontend

Not yet built. Planned: React + Vite + TypeScript + Tailwind + shadcn/ui. Design mockups (Login + Chat with
conversation sidebar) already exist in `design/frontend-mockup/*.dc.html`, published as a Claude Design
canvas Artifact; `canvas.json` is only that canvas tool's layout manifest (artboard positions/pages), not
consumed by application code — pull colors/typography/structure from the `.dc.html` files themselves when
building components. The mockups cover only login/chat; none of the CV/policy/job-requirement/report CRUD
surface has a designed UI yet.
