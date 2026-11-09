# Black Fire — browser app switching

User clarification, November 9, 2026. This supersedes the earlier API-routing product direction.

## Selected first target

Build for the actual ChatGPT, Claude, and Gemini web applications in **local Google Chrome**. Use a **local Chrome extension connected to Black Fire** as the first browser companion. Native desktop application support is deferred. This is the recommended implementation direction, not a claim that the extension is already implemented.

For the short hackathon build window, first prove user-controlled context handoff between two web applications. Extend to the third application after that path works. Provider API routing does not replace the app-switching requirement.

## Core requirement

Black Fire should let a user start work in one web application and switch to another while carrying an explicit record of the task and relevant context. The user remains in their own browser and signs into each application directly.

Examples include image identification/explanation, conversation, code generation such as binary search, and generating a static website. These are desired capabilities, not features demonstrated by the current prototype.

## Intended experience

1. The user signs into the selected web applications directly in Chrome. Black Fire does not collect their passwords or copy session cookies to its backend.
2. The user creates a task in Black Fire and chooses allowed applications and any model preference or lock.
3. Black Fire keeps the objective, exact requirements, user-supplied conversation excerpts, decisions, and authorized attachment references in its context capsule.
4. The user chooses the next application or accepts Black Fire's recommendation. The first version uses explicit user preferences and capability rules; no claim of an objectively best model is made without evaluation.
5. The extension opens or focuses that application's tab. Black Fire prepares a readable handoff containing the selected context, which the user reviews, copies/pastes, and sends in the destination application.
6. The user brings the relevant response back into Black Fire using an explicit copy/paste action. Black Fire saves progress and labels the selected application and any user-confirmed model. Unverified model identity stays unknown.
7. Reopening Black Fire restores the saved task and handoff history.

This is the first assisted milestone. Automatic response extraction, prompt insertion/submission, completion detection, quota detection, and unattended switching are separate feasibility gates. Do not represent assisted handoff as a completed autonomous agent. Add site automation only after establishing a supported/permitted interaction path for that provider.

The portable context record is Black Fire's own record; hidden provider memory or internal conversation state is not assumed transferable.

## Component responsibilities

| Component | Responsibility |
|---|---|
| Black Fire workspace | Task input, editable handoff context, application selection, saved progress, exports |
| Local Chrome extension | User-invoked tab discovery/open/focus; only the browser permissions needed for the implemented workflow |
| Existing backend and storage | Persist Black Fire's owned task/context records; no model-provider API calls required for this milestone |
| Optional later coordinator | Consider LangGraph when durable multi-step execution warrants it; it does not itself control browser tabs |
| Optional later browser service | Reconsider TinyFish only if a hosted browser, account/session flow, and verified cost fit the project; it is not the selected first connector |

Codex's browser access in this development chat is a testing tool, not an app dependency or a browser connector shipped with Black Fire.

## What exists today

The implemented frontend, FastAPI backend, local history, context records, and mock worker remain a foundation. They do not control any external application. No Chrome extension, TinyFish integration, real app switching, or live model interaction has been implemented.

## Next implementation sequence

1. Add editable context and an assisted handoff screen to the existing workspace. Build/export the handoff from user-provided content without a model call.
2. Build the Chrome extension with explicit user-invoked open/focus actions and a clear connection to the Black Fire workspace. Start with tab control; page-content access is not required for this milestone.
3. Demonstrate one text/code task moving between two actual web applications, with the user reviewing/sending the handoff and copying back the result.
4. Verify original requirements, destination application, model-lock behavior, reload persistence, and handoff provenance. If an exact model cannot be verified, request user verification rather than silently substituting it.
5. Add the third application and image handoff. Initial image handling may require the user to reattach the original file in the destination app; do not imply file references transfer the image bytes.
6. Evaluate provider-specific automation separately before expanding the assisted workflow.

The browser MVP exit gate is a reproducible two-application handoff with saved context and honest manual/automatic labels. A recorded demonstration must show the actual applications, rather than mock provider results.

## Sources behind the recommendation

- [Chrome Tabs API](https://developer.chrome.com/docs/extensions/reference/api/tabs): extensions can create/activate tabs and communicate with content scripts.
- [OpenAI consumer terms](https://openai.com/policies/row-terms-of-use/): restrictions on automated output extraction remain relevant to any proposed response-capture feature.
- [Anthropic consumer terms](https://www.anthropic.com/legal/consumer-terms): automated-access restrictions mean browser-control capability alone is not sufficient evidence of permission. Establish the applicable terms for the account/region before adding automation.

These sources support the browser mechanism and the need to verify provider interaction paths. They do not establish approval for unattended automation across all three services.

Provider-API adapter work remains paused. Preserve historical day-one evidence and keep the zero-incremental-spending constraint. Native desktop support, mandatory TinyFish usage, and mandatory LangGraph integration are outside the first browser milestone.
