# Black Fire

One workspace to manage ChatGPT, Claude, and Gemini web apps, route tasks, switch applications, and preserve context.

**Full product target:** Submit work and view results in Black Fire while it coordinates the actual ChatGPT, Claude, and Gemini web apps in local Chrome. Routing and authorized switching depend on user requests, verified capabilities, observed quota/availability, and model preferences/locks. A local extension is the selected first connector approach. See the [canonical implementation plan and completion checklist](docs/IMPLEMENTATION_PLAN.md). Assisted handoff is an intermediate validation step; fully automatic operation across all three apps is unverified. The existing mock prototype has no extension or real app control yet.

**Day-one foundation — mock inference only.** A real React frontend and FastAPI backend save task inputs, exact requirements, routing decisions, results, and activity. The deterministic worker is explicitly labeled; it does not generate an AI answer. Gemini, Cloudflare, image uploads, live streaming, fallback, and durable LangGraph checkpoints are not enabled yet.

Black Fire is the implementation name for the earlier Catalyst plan. LedgerDesk is a superseded alternative.

## Run locally

Requirements: Node 22.12+ (tested 22.16), Python 3.12 (tested 3.12.10).

From the repository root, in PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r services/api/requirements-dev.lock
npm ci
Copy-Item .env.example .env
Copy-Item apps/web/.env.example apps/web/.env.local
.venv/Scripts/python.exe -m uvicorn blackfire.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --no-proxy-headers
```

In a second terminal at the repository root:

```powershell
npm run dev
```

Open http://127.0.0.1:5173. Choose an example, add requirements, and select **Run mock task**. Inspect Result, Activity, and Context capsule; reload and reopen it from Task history. Export JSON downloads the saved record. Delete removes a run permanently.

Local mode uses SQLite at `.local/black-fire.sqlite3` and one development identity. It is loopback-only, is not multi-user authentication, and cannot run with `APP_ENV=production`. Do not expose the local development server to a network. Supabase mode requires verified login and owner-scoped database policies.

## Verify

```powershell
npm run build
.venv/Scripts/python.exe -m pytest services/api/tests -q
.venv/Scripts/python.exe -m ruff check services/api/blackfire services/api/tests
```

If a restricted Windows sandbox blocks temporary files or loopback, run these commands in your ordinary terminal. Do not disable Windows security protections. Docker is used by CI; it was unavailable on the development machine.

## Repository

| Path | Purpose |
|---|---|
| `apps/web` | React/TypeScript workspace and Supabase login |
| `services/api/blackfire` | FastAPI, authentication, routing, context, storage adapters |
| `services/api/tests` | Input, idempotency, isolation, restart, route-policy tests |
| `supabase/migrations` | Initial owner-scoped cloud schema |
| `database/tests` | Transactional RLS regression check |
| `infra/Dockerfile`, `render.yaml` | Backend hosting configuration; not yet deployed |
| `contracts/openapi.json` | Generated API contract |
| `docs` | Architecture, setup, day-one evidence, next gates |

See [setup and deployment](docs/SETUP.md), [architecture](docs/ARCHITECTURE.md), and the [day-one report](docs/DAY_01.md).

No provider keys belong in Git, screenshots, browser configuration, or frontend bundles. Real keys go only in the ignored root `.env` / hosting secrets. `VITE_*` values are public. The runtime does not require a Supabase service-role key.
