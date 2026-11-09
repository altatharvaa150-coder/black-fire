# Black Fire — unified control centre for three AI web apps

Current implementation plan, November 9, 2026. This is the canonical plan and supersedes the original Catalyst API plan and any description of the product as only a context-transfer utility.

## 1. What we are building

**One Black Fire workspace for using the actual ChatGPT, Claude, and Gemini web applications.** The user submits work in Black Fire. Its coordinator selects an authorized application/model according to the request, supported capabilities, observed availability/quota, and the user's preferences. Browser connectors operate the actual applications where a supported/permitted integration is established. Black Fire brings the result and execution status back to the same workspace and keeps project context across turns and switches.

Context continuity is one component of this application manager. The product also needs a common composer/result view, application connections, routing, switching, model controls, availability observations, history, attachments, and explicit failure/recovery states.

This is the full target experience, not the current implementation. Automatic control and result collection from all three consumer applications have not been demonstrated or established as permitted. An assisted handoff is an intermediate milestone; it must not be presented as fulfillment of the entire product.

## 2. Target audience

People who already use more than one AI chat application and want to manage that work from one place. Initial testers: student developers, solo developers, and hackathon builders. Additional users: researchers, writers, and creators moving text or image work among these services.

The problem is fragmented AI work: deciding which application to use, dealing with an unavailable model, repeating project instructions, and tracking results in separate conversations. Black Fire should reduce that coordination overhead. It does not create additional provider quota or guarantee access to models absent from the user's account.

## 3. Target user journey

1. Install the local Chrome companion and open Black Fire. Sign into ChatGPT, Claude, and Gemini directly in their own tabs. Black Fire does not collect provider passwords or send browser cookies to its backend.
2. Choose allowed applications, automatic routing or an exact application/model lock, preferred quality/speed, and whether eligible handoffs may happen automatically. Image transfer needs explicit content-sharing scope.
3. Enter a message, image question, coding request, or website brief in the single Black Fire composer.
4. The coordinator filters routes by the user's authorization and lock, verified capabilities, account access, and observed availability. It chooses among remaining routes with an explainable rule and displays its reason.
5. The selected app connector runs the request through the actual web app where supported. The target result returns to Black Fire with application/model provenance and an honest execution status. Until an automation path is verified, that connector uses clearly labeled assisted steps.
6. A user request, observed limit, or capability need may trigger a switch. Save the current state first. Respect exact model locks; a locked model pauses rather than silently changing.
7. Carry the necessary context and authorized attachments to the next eligible app, continue, and keep the result/activity/history in Black Fire. Do not automatically resend a completed request or restart one whose outcome is uncertain.
8. The user can override routing, pause, stop, inspect context, and resume. Reopening Black Fire restores the saved project.

Provider-internal memory, hidden reasoning, and a destination app's private conversation state are not transferable. Black Fire maintains its own explicit record of requirements and progress.

## 4. Tasks and routing examples

| Request | Required route capability | Expected output |
|---|---|---|
| Explain a screenshot or identify objects | Verified image input and visual understanding for the selected account/model | Description with uncertainty where appropriate |
| Chat, explain a concept, summarize | Text conversation and sufficient context | Answer using relevant saved context |
| Write binary search | Code generation in the requested language | Code, explanation, and proposed tests |
| Create a static website | Code generation and adequate output capacity | HTML/CSS/JavaScript artifacts; preview and validation are separate features |

No untested assertion that one brand always produces the best code or image answer. Start with user preferences and task-capability rules, then evaluate representative tasks before introducing measured quality rankings. Do not run all three models on every prompt by default.

Quota handling uses states such as available, limit observed, reset known, unknown, disconnected, or verification needed, with source/time. Do not display invented account-wide remaining-message counts. An unknown quota is not proof that an application is available or exhausted. User-reported availability must be distinguished from an observed app notice.

## 5. Components and technology decisions

| Component | Selection/status | Role |
|---|---|---|
| Main interface | Existing React + TypeScript + Vite | Single composer, responses, app/model controls, attachments, activity, history |
| Local browser companion | Planned Chrome extension | User-authorized local browser connection; open/focus tabs; per-site operations only where verified |
| App connectors | Planned separate ChatGPT, Claude, and Gemini adapters | Normalize connection, capability/model observations, execution/result handling, limits, and errors |
| Coordinator | Start with explicit Python/TypeScript rules | Task routing, consent/locks, availability, attempt limits, switch decisions, recovery |
| Durable orchestration | LangGraph optional after connector feasibility | State transitions/checkpoints if the workflow warrants it; not the browser controller or an AI model |
| Backend | Existing FastAPI + Pydantic | Validated owned task/state operations and connector/coordinator contracts |
| Persistence | Existing local SQLite; Supabase schema/adapter prepared | Local history/context; cloud persistence after end-to-end auth verification |
| Browser agent service | TinyFish is an evaluated alternative, not selected or installed | Could supply hosted website automation, but requires session/integration and cost verification; does not automatically inherit local Chrome logins |
| Agent reasoning model | None required for initial routing | Deterministic rules first; no separate paid model needed to decide every route |

Do not build the browser product around developer model APIs. Our own backend/storage APIs and a browser service's control API are technically different from invoking a provider's model inference API.

TinyFish executes goals on websites; Chrome extension APIs operate local browser tabs. They are different deployment paths. Avoid implementing both for the first milestone. Keep the zero-incremental-spending constraint; TinyFish documentation currently describes Agent/Browser usage as wallet-funded, so it is not assumed to be a free dependency.

Codex's browser tools are development/testing access only and are not shipped to Black Fire users.

## 6. Difference from switching model API calls

| Aspect | Model API router | Black Fire target |
|---|---|---|
| Execution destination | Developer inference endpoint | Actual provider web application |
| Access | API credentials and API billing/quota | User's signed-in app session and actual account/model access |
| Work the connector must handle | Request/response schemas | UI state, selected model, attachments, response completion, interruptions |
| Availability | API errors and reported limits | Verified visible app observations, supported signals, or labeled user reports |
| Common interface/context | Can be provided by either design | Required here, together with real app control |

Using a Chrome extension or TinyFish does not establish provider permission. OpenAI's published consumer terms restrict automated output extraction; Anthropic's published consumer terms restrict automated access except when explicitly permitted. Establish an applicable supported/permitted path per application before claiming full automatic operation. If only assisted access is feasible, report that as a reduced demonstration, not completion of the autonomous target.

## 7. Actual implementation checklist

Checked against the repository and previously recorded checks in this session. A checked item describes the scope stated, not the larger future feature.

- [x] ✅ Black Fire React/TypeScript workspace and responsive layout.
- [x] ✅ FastAPI health and validated run create/read/list/delete endpoints.
- [x] ✅ Local SQLite task/result history surviving reload and backend restart tests.
- [x] ✅ Initial saved context capsule with original objective and exact requirements; currently read-only in the UI.
- [x] ✅ Saved activity events, JSON export, and delete.
- [x] ✅ Mock-only allowlist/model-lock checks, input validation, and duplicate-request protection.
- [x] ✅ Supabase Free project/schema, owner-based RLS, REST adapter, and authentication code; cloud login/end-to-end user flow still unverified.
- [x] ✅ Fifteen API tests passed earlier; frontend build and Linux CI/Docker build passed. These checks cover the mock foundation.
- [x] ✅ Source repository, pinned dependencies, setup instructions, and day-one evidence.
- [ ] Local Chrome extension and connection to Black Fire.
- [ ] Real ChatGPT, Claude, and Gemini app connectors.
- [ ] A real answer from any of these apps displayed in Black Fire.
- [ ] Basic chat and code-generation task support beyond the existing mock task schema.
- [ ] Editable/versioned project context and multi-turn conversation integration.
- [ ] Account-specific capability registry and verified model identity/locks.
- [ ] Availability/quota observation and request/capability/quota-based switching.
- [ ] Automatic submission/result capture, subject to provider-specific feasibility.
- [ ] Image upload and transfer, attachment ownership/provenance, image-task checks.
- [ ] Generated website file packaging, preview, and meaningful validation.
- [ ] Durable browser-action recovery, cancellation, and uncertain-outcome handling.
- [ ] TinyFish or LangGraph integration; neither is implemented.
- [ ] Verified cloud sign-in flow and public frontend/API deployment.
- [ ] Measured cross-app quality, constraint retention, and switching evaluation.

## 8. Changes needed in the existing code

Reuse the workspace, storage abstractions, run history, authentication groundwork, and mock regression tests. This is a substantial connector/coordinator change rather than a complete rewrite.

1. Replace the historical Gemini/Cloudflare API candidate registry with ChatGPT/Claude/Gemini web-app connection records. Keep the mock adapter for tests with unmistakable labels.
2. Expand task types from summarize/extract/code-review to conversation, image questions, code generation, and website generation.
3. Add connection IDs, verified or user-reported model identity, observed availability/capability provenance, routing preferences, and handoff policy to contracts.
4. Make context editable and versioned, with message/file references, completed work, and explicit next steps.
5. Replace the mock worker path with browser-connector job state. Preserve idempotency; never retry a browser Send action blindly after a timeout.
6. Add a single conversation/result view, attachments, stop/resume controls, and app/model switching controls. Observed results and user-imported results must remain distinguishable.
7. Add the Chrome extension and per-site adapters. A hosted frontend alone cannot operate the user's local tabs.
8. Replace the old live-API setup sequence with browser feasibility and connection tests. Keep existing database/backend setup applicable to state persistence.

## 9. Implementation order and provisional schedule

Dates are targets in IST, not promises. A failed feasibility gate changes what can honestly be delivered.

| Target | Work | Exit evidence |
|---|---|---|
| Nov 9 — foundation/replan | Keep completed mock foundation; settle unified-app specification and document gaps | This plan plus accurate implementation checklist |
| Nov 10 — critical feasibility | Inspect actual per-provider supported/permitted integration paths; build local extension tab connection; prove a bounded first connector or mark it assisted/blocked | Actual app behavior and explicit automation boundary; no simulated claim |
| Nov 11 — first unified workflow | Add single composer/result history, editable context, app connections, text/code task contracts; connect second app | One task/result saved through a real or explicitly assisted connector |
| Nov 12 — routing and switching | Enforce requests, model locks, capabilities, observed limits and allowed handoffs; add third app if access permits | One real two-app continuation with preserved requirements; clearly label injected limits |
| Nov 13 — images/artifacts/reliability | Add image path, generated code files, bounded website preview, cancellation and recovery; test failures | Actual modality checks and restart/duplicate-Send tests |
| Nov 14 — evaluation/release package | Evaluate routing and context preservation; deploy the hub/backend; package local extension; finish README/write-up/slides/video | Honest feature matrix, reproducible setup, demo backup, measured failures |
| Nov 15 — submission | Verify links, rehearse, resolve submission blockers; internal submission target 18:00 | Verified artifacts and portal confirmation after separate submission authorization |

Before polishing later features, prove that at least two intended app connectors can support the actual user workflow. If this is not achievable, present the assisted hub as a reduced milestone and do not call the full application-manager goal achieved. Organizer track mapping remains a separate unresolved registration task.

## 10. Definition of done

The full target is met only when the user can manage actual ChatGPT/Claude/Gemini work from one Black Fire workspace, choose or authorize routing, get actual results back, switch for a verified request/capability/availability reason, preserve necessary context/files, and recover without silently duplicating actions. Each app's supported interaction path and any manual steps must be visible. Native desktop clients are outside the first release.

## Sources checked in this session

- [Chrome Tabs API](https://developer.chrome.com/docs/extensions/reference/api/tabs).
- [TinyFish Agent overview](https://docs.tinyfish.ai/agent.md) and [usage overview](https://docs.tinyfish.ai/index.md).
- [LangGraph workflows](https://docs.langchain.com/oss/python/langgraph/workflows-agents).
- [OpenAI consumer terms](https://openai.com/policies/row-terms-of-use/) and [Anthropic consumer terms](https://www.anthropic.com/legal/consumer-terms).

Documentation and provider terms do not establish tested account access. The code checklist above is intentionally separate from planned capabilities.
