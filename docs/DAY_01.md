# Day one — November 9, 2026 (IST)

## Delivered

- Renamed the active Catalyst concept to **Black Fire**, using the user's existing `altatharvaa150-coder/black-fire` repository.
- Built the React/TypeScript/Vite workspace: mock task creation, requirements, route controls, result/activity views, context capsule, history, deletion, JSON export, and connection status.
- Built FastAPI health endpoints and owned run endpoints, deterministic routing/worker/context steps, input validation, request hashing, and idempotency.
- Implemented local SQLite persistence and a Supabase REST adapter that forwards a verified user JWT. Hosted configuration rejects anonymous SQLite.
- Created the Supabase project in Mumbai in the explicitly selected organization; verified its Free plan. Applied the initial migration and checked policies.
- Added exact dependency lockfiles, OpenAPI contract, Docker/Render configuration, Linux CI, and setup/architecture documents.

## Verification and measurements

| Check | Observed result |
|---|---|
| Backend tests | 15 passed in 4.44 seconds |
| Frontend | TypeScript check and production build passed locally and in Linux CI |
| GitHub Actions | Both web/API jobs passed for implementation commit `97f40b6`; Linux tests and Docker build succeeded |
| Production assets | JavaScript 236.81 kB / 73.90 kB gzip; CSS 15.37 kB / 4.29 kB gzip |
| Python static checks | Ruff passed |
| Dependency checks | npm reported 0 vulnerabilities; pip check reported no broken requirements |
| Supabase RLS | Owner read/write permitted; other-owner read/update/delete blocked; owner reassignment blocked; anonymous read blocked |
| Supabase advisors | No security findings. Informational unused-index notice expected on the newly created empty table |
| Browser | Create task, exact context, activity, reload/history/reopen, connection disclosures, JSON export passed |
| Responsive inspection | Desktop and 390px mobile layout inspected |
| Live model requests | **0**; no provider credentials or accounts configured |

Screenshots: [workspace](evidence/day-one-workspace.jpg), [mobile](evidence/day-one-mobile.jpg).

These are deterministic/mock and access-control checks. They are not real model quality, latency, handoff, or quota benchmarks. Database fixtures were rolled back; no permanent demo user was created.

## Failures and decisions

Windows application control blocked LangGraph's native serializer dependency. A compatible UUID dependency resolved one import failure, but the serializer remained unavailable. We retained explicit Python workflow steps for this mock slice and deferred LangGraph installation/integration to day two. No endpoint security settings were disabled.

The restricted development sandbox also prevented local sockets and temporary test files. Tests and loopback preview were run with approved local execution access. A React hot-reload warning led to separating the App component from the root entry point; the production build then passed again.

The user explicitly chose **build the mock-backed slice first**, because Gemini, Cloudflare, and Render accounts are not set up. Consequently, the original full day-one exit gate is **not complete**: two genuine model routes and public frontend/API hosting remain pending. Supabase project/schema is live; frontend/API are local. Supabase sign-in and the full browser → API → cloud database path still need a provisioned demo account and a live end-to-end check. Local SQLite end-to-end flow is verified.

Docker was unavailable on the development machine. The Linux CI workflow successfully built the container after push. [Verified workflow run](https://github.com/altatharvaa150-coder/black-fire/actions/runs/42593167734).

## Next work

1. Provision a Supabase demo account and verify the authenticated cloud path with two users.
2. Configure Gemini, Cloudflare, and Render Free accounts without enabling paid fallbacks. Keep keys in ignored local/server configuration.
3. Verify actual text/image model access, IDs, quotas, responses, and provider terms. Do not auto-accept Cloudflare vision licensing.
4. Resolve the LangGraph runtime environment; add private persistent checkpoints and server-owned attempt/usage records before real inference.
5. Deploy the thin slice to Render + Cloudflare Pages and record public HTTPS evidence.
6. Independently resolve the hackathon's Open/Wildcard registration mapping with the organizer; no registration action was performed here.
