# Configuration and deployment

**Direction update:** The next milestone is a local Chrome extension with user-controlled handoff between actual web apps. Follow [PRODUCT_DIRECTION.md](PRODUCT_DIRECTION.md). This document records setup for the existing mock foundation; provider API credentials and the live-provider gates below are historical/deferred and are not prerequisites for the browser milestone. Extension installation instructions will be added when the extension exists.

## Created cloud resource

Supabase project **black-fire**, Mumbai (`ap-south-1`), in the user-selected organization. Organization plan was verified as Free. Project ref: `iynrlcrvddswmxbglvia`.

Dashboard: https://supabase.com/dashboard/project/iynrlcrvddswmxbglvia

The initial migration is applied and RLS tests passed. No permanent demo user or private user data has been created. The migration uses Supabase CLI's conventional `supabase/migrations` location instead of the plan's proposed `database/migrations` path.

## Enable cloud storage locally

1. In Supabase Authentication → Users, provision a demo user with your own email/password using the dashboard. Keep credentials out of chat and Git. No public signup is required for this slice.
2. Set the ignored root `.env` to `STORAGE_BACKEND=supabase`, the project HTTPS URL, and its **publishable** API key. Keep `APP_ENV=development` locally.
3. Set the same public URL/key as `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in `apps/web/.env.local`.
4. Restart frontend and API. Sign in and create a mock task. Reload and verify it in history. Sign out and verify private data disappears. Repeat with a second user before opening access to testers.

The local-only demo needs no Supabase configuration. Do not use the legacy service-role key or an `sb_secret_` key in either frontend variable.

## Environment inventory

| Variable | Location | Current purpose |
|---|---|---|
| APP_ENV | Backend | development / production; production refuses SQLite |
| STORAGE_BACKEND | Backend | sqlite / supabase |
| SQLITE_PATH | Backend, local only | Default `.local/black-fire.sqlite3` |
| CORS_ORIGINS | Backend | Exact comma-separated frontend origins; no wildcard |
| SUPABASE_URL | Backend | Project HTTPS endpoint |
| SUPABASE_PUBLISHABLE_KEY | Backend | Public API key; user JWT controls access |
| VITE_API_URL | Frontend | Empty for Vite proxy, HTTPS API URL when hosted |
| VITE_SUPABASE_URL | Frontend | Public project URL |
| VITE_SUPABASE_PUBLISHABLE_KEY | Frontend | Public key only |
| GEMINI_API_KEY / GEMINI_MODEL | Backend, future | Not consumed by day-one code |
| CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN | Backend, future | Not consumed by day-one code |

## Planned hosting (not deployed)

The user chose to build the mock slice before setting up Gemini, Cloudflare, and Render accounts. No alternative paid hosting or inference was activated.

1. Create/configure Render and Cloudflare accounts; verify Free plans and billing/overage settings.
2. Link this GitHub repository to Render using `render.yaml`. Review Free compute and the Docker build. Configure Supabase URL/key and exact deployed frontend origin. Use `/health/ready` as health check. Auto-deploy is off.
3. Cloudflare Pages: repository root is the build root; build `npm ci && npm run build`; output `apps/web/dist`. Configure frontend public variables and `VITE_API_URL` pointing to Render HTTPS.
4. Test sign-in → mock run → history reload on the hosted URLs, and cross-user access denial. Record a clip and actual URLs in the daily report.
5. A restart must preserve Supabase data. Render local storage is not used in hosted mode.

Docker build command: `docker build -f infra/Dockerfile -t black-fire-api .`. Docker was not installed locally; the GitHub workflow successfully built it on Linux for implementation commit `97f40b6`.

## Live provider gates

Before enabling real inference, verify the owner's account eligibility and Free billing state, record model IDs and quotas, implement server-owned attempt counters and bounded input/output limits, and run one genuine text and image request per provider. Cloudflare's Llama vision model requires explicit license/acceptable-use acceptance by the user. No automatic agreement request is sent by this code.

Then integrate LangGraph with private persistent checkpoints, ownership, and explicit interrupted/uncertain states. Mock success is not evidence of model quality, live latency, fallback, or quota exhaustion.
