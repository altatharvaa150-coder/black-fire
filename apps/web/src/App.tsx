import { useEffect, useRef, useState } from "react";

import type { Session } from "@supabase/supabase-js";
import {
  api,
  supabase,
  type Health,
  type Provider,
  type Run,
  type TaskType,
} from "./api";

function Flame() {
  return (
    <svg
      width="26"
      height="29"
      viewBox="0 0 26 29"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M14 1C15 9 24 11 24 19a11 11 0 0 1-22 0c0-5 3-8 6-11-1 7 3 7 4 4 1-3 1-6 2-11Z"
        fill="currentColor"
      />
      <path d="M14 15c0 4 5 5 4 8a5 5 0 0 1-10-1c0-3 4-5 6-7Z" fill="#151819" />
    </svg>
  );
}
const examples = [
  {
    title: "Summarize a note",
    detail: "Turn a long update into the essentials.",
    type: "summarize" as TaskType,
    prompt:
      "Summarize this update in three bullets: The Black Fire prototype now has a React workspace, a Python API, and saved task history. Real provider connections are next. Keep the distinction between mock results and AI-generated answers clear.",
  },
  {
    title: "Extract key details",
    detail: "Find structure in everyday text.",
    type: "extract" as TaskType,
    prompt:
      "Extract the project name, goal, and next milestone: Black Fire preserves task context across AI providers. The next milestone is verifying two permitted free model connections.",
  },
  {
    title: "Review a snippet",
    detail: "Explain code without executing it.",
    type: "code_review" as TaskType,
    prompt:
      "Explain this Python function and suggest edge cases to check:\n\ndef average(values):\n    return sum(values) / len(values)",
  },
];

export default function App() {
  const [page, setPage] = useState<"workspace" | "history" | "connections">(
    "workspace",
  );
  const [health, setHealth] = useState<Health | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [active, setActive] = useState<Run | null>(null);
  const [prompt, setPrompt] = useState("");
  const [constraints, setConstraints] = useState("");
  const [taskType, setTaskType] = useState<TaskType>("summarize");
  const [lock, setLock] = useState("automatic");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [resultTab, setResultTab] = useState<"result" | "activity">("result");
  const pending = useRef<{ body: string; key: string } | null>(null);
  const textarea = useRef<HTMLTextAreaElement>(null);

  async function loadHistory() {
    setRuns(await api<Run[]>("/api/v1/runs"));
  }
  async function connect() {
    setError("");
    try {
      const [h, p] = await Promise.all([
        api<Health>("/health/ready"),
        api<Provider[]>("/api/v1/providers"),
      ]);
      setHealth(h);
      setProviders(p);
    } catch (e) {
      setHealth(null);
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void connect();
  }, []);
  useEffect(() => {
    if (!supabase) return;
    void supabase.auth
      .getSession()
      .then(({ data }) => setSession(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, value) => {
      setSession(value);
      setRuns([]);
      setActive(null);
    });
    return () => data.subscription.unsubscribe();
  }, []);
  useEffect(() => {
    if (health && (!health.auth_required || session))
      void loadHistory().catch((e) => setError(e.message));
  }, [health, session]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy || !prompt.trim()) return;
    setBusy(true);
    setError("");
    setNotice("");
    const body = JSON.stringify({
      prompt,
      task_type: taskType,
      constraints,
      allowed_providers: ["mock"],
      locked_model: lock === "automatic" ? null : lock,
    });
    if (pending.current?.body !== body)
      pending.current = { body, key: crypto.randomUUID() };
    try {
      const run = await api<Run>("/api/v1/runs", {
        method: "POST",
        body,
        headers: { "Idempotency-Key": pending.current.key },
      });
      setActive(run);
      setResultTab("result");
      pending.current = null;
      await loadHistory();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function openRun(id: string) {
    setError("");
    try {
      setActive(await api<Run>(`/api/v1/runs/${id}`));
      setPage("workspace");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  function newTask() {
    setActive(null);
    setPrompt("");
    setConstraints("");
    setNotice("");
    setError("");
    pending.current = null;
    setPage("workspace");
    setTimeout(() => textarea.current?.focus(), 0);
  }
  function download() {
    if (!active) return;
    const objectUrl = URL.createObjectURL(
      new Blob([JSON.stringify(active, null, 2)], { type: "application/json" }),
    );
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = `black-fire-${active.id}.json`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    setNotice("Run exported as JSON.");
  }
  async function removeRun(id: string) {
    try {
      await api(`/api/v1/runs/${id}`, { method: "DELETE" });
      await loadHistory();
      if (active?.id === id) setActive(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function login(event: React.FormEvent) {
    event.preventDefault();
    if (!supabase) return;
    setBusy(true);
    setError("");
    try {
      const { error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (authError) throw authError;
      setPassword("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const needsLogin = health?.auth_required && !session;
  const title =
    page === "workspace"
      ? "Your work, uninterrupted."
      : page === "history"
        ? "Pick up where you left off."
        : "Know where your work goes.";
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setPage("workspace");
          }}
        >
          <span className="brand-mark">
            <Flame />
          </span>
          <span>
            black fire<span className="brand-sub">CONTEXT THAT STAYS.</span>
          </span>
        </a>
        <button className="new-task" onClick={newTask} disabled={busy}>
          <span>＋</span> New task <span className="keyhint">↗</span>
        </button>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          <button
            className={page === "workspace" ? "nav active" : "nav"}
            onClick={() => setPage("workspace")}
          >
            <span>▦</span> Playground
          </button>
          <button
            className={page === "history" ? "nav active" : "nav"}
            onClick={() => setPage("history")}
          >
            <span>◷</span> Task history <small>{runs.length}</small>
          </button>
          <button
            className={page === "connections" ? "nav active" : "nav"}
            onClick={() => setPage("connections")}
          >
            <span>⌘</span> Connections <i />
          </button>
        </nav>
        <div className="recent">
          <div className="nav-label">RECENT TASKS</div>
          {runs.slice(0, 4).map((run) => (
            <button key={run.id} onClick={() => void openRun(run.id)}>
              <span>↳</span>
              {run.input.prompt}
            </button>
          ))}
          {!runs.length && <p>Your saved tasks will appear here.</p>}
        </div>
        <div className="sidebar-bottom">
          <div className="build-card">
            <span className="tiny-dot" /> DAY 01 / FOUNDATION
            <p>
              A small start.
              <br />A continuous workflow.
            </p>
            <div className="build-track">
              <span />
            </div>
          </div>
          <div className="profile">
            <span className="avatar">BF</span>
            <div>
              {session ? "Private workspace" : "Local workspace"}
              <small>
                {health?.storage === "supabase"
                  ? "Supabase connected"
                  : "Development preview"}
              </small>
            </div>
            {session && (
              <button
                aria-label="Sign out"
                onClick={() => void supabase?.auth.signOut()}
              >
                ↪
              </button>
            )}
          </div>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div>
            Workspace <span>/</span>{" "}
            <strong>
              {page === "workspace"
                ? "Playground"
                : page === "history"
                  ? "Task history"
                  : "Connections"}
            </strong>
          </div>
          <div className="top-status">
            <span className={health ? "status-dot" : "status-dot offline"} />
            {health ? "API connected" : "API offline"}
            <span className="version">v0.1</span>
          </div>
        </header>
        <div className="main-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">BLACK FIRE / {page.toUpperCase()}</div>
              <h1>{title}</h1>
              <p>
                One workspace for your tasks, model routes, and the context
                between them.
              </p>
            </div>
            <span className="mode-tag">◈ MOCK MODE</span>
          </div>
          <div className="demo-banner">
            <span className="banner-icon">i</span>
            <p>
              <strong>The foundation is live locally.</strong> Tasks use a
              deterministic mock. No AI provider is called and no inference
              quota is consumed.
            </p>
            <button onClick={() => setPage("connections")}>
              View connections <span>↗</span>
            </button>
          </div>
          {error && (
            <div role="alert" className="error">
              {error}
              {!health && (
                <button onClick={() => void connect()}>Reconnect</button>
              )}
            </div>
          )}
          {notice && (
            <div role="status" className="notice">
              {notice}
            </div>
          )}
          {needsLogin ? (
            <section className="panel login">
              <h2>Sign in to your private workspace</h2>
              <p>
                Use a pre-provisioned Supabase demo account. Task history is
                scoped to your login.
              </p>
              {supabase ? (
                <form onSubmit={login}>
                  <label>
                    Email
                    <input
                      type="email"
                      autoComplete="username"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </label>
                  <label>
                    Password
                    <input
                      type="password"
                      autoComplete="current-password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </label>
                  <button className="primary" disabled={busy}>
                    Sign in
                  </button>
                </form>
              ) : (
                <p>
                  Frontend Supabase configuration is missing. See the setup
                  guide.
                </p>
              )}
            </section>
          ) : (
            <>
              {page === "workspace" && (
                <div className="workspace-grid">
                  <div className="work-column">
                    <form className="panel composer" onSubmit={submit}>
                      <div className="panel-top">
                        <h2>
                          <span className="section-symbol">✳</span> Start
                          something
                        </h2>
                        <span className="small-label">TEXT WORKSPACE</span>
                      </div>
                      <label className="sr-only" htmlFor="prompt">
                        Your task
                      </label>
                      <textarea
                        ref={textarea}
                        id="prompt"
                        maxLength={8000}
                        value={prompt}
                        disabled={busy}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder={
                          "What are we working on?\nPaste a note, a question, or a code snippet…"
                        }
                        required
                      />
                      <div className="composer-meta">
                        <span>Non-sensitive demo content only</span>
                        <span>{prompt.length.toLocaleString()} / 8,000</span>
                      </div>
                      <div className="composer-controls">
                        <label>
                          Task type
                          <select
                            value={taskType}
                            onChange={(e) =>
                              setTaskType(e.target.value as TaskType)
                            }
                            disabled={busy}
                          >
                            <option value="summarize">Summarize text</option>
                            <option value="extract">Extract details</option>
                            <option value="code_review">
                              Explain / review code
                            </option>
                          </select>
                        </label>
                        <label>
                          Route
                          <select
                            value={lock}
                            onChange={(e) => setLock(e.target.value)}
                            disabled={busy}
                          >
                            <option value="automatic">
                              Automatic · mock only
                            </option>
                            <option value="mock-v1">Lock to mock-v1</option>
                          </select>
                        </label>
                      </div>
                      <label
                        className="constraints-label"
                        htmlFor="constraints"
                      >
                        Requirements to preserve <span>optional</span>
                      </label>
                      <input
                        id="constraints"
                        value={constraints}
                        maxLength={2000}
                        disabled={busy}
                        onChange={(e) => setConstraints(e.target.value)}
                        placeholder="e.g. Three bullets, plain English, preserve exact dates"
                      />
                      <div className="composer-footer">
                        <span>
                          <span className="status-dot" /> Nothing sent to
                          external AI
                        </span>
                        <button
                          className="primary"
                          disabled={busy || !health || !prompt.trim()}
                        >
                          {busy ? "Saving task…" : "Run mock task"}{" "}
                          <span>↑</span>
                        </button>
                      </div>
                    </form>
                    {!active ? (
                      <>
                        <div className="section-heading">
                          A PLACE TO BEGIN <span>Try an example</span>
                        </div>
                        <div className="examples">
                          {examples.map((example, i) => (
                            <button
                              key={example.title}
                              disabled={busy}
                              onClick={() => {
                                setPrompt(example.prompt);
                                setTaskType(example.type);
                                textarea.current?.focus();
                              }}
                            >
                              <span className="example-number">
                                0{i + 1} <span>↗</span>
                              </span>
                              <strong>{example.title}</strong>
                              <p>{example.detail}</p>
                            </button>
                          ))}
                        </div>
                        <div className="empty-result">
                          <span>⌁</span>
                          <h3>Your next result starts here.</h3>
                          <p>
                            Run a task to inspect its answer, route, and saved
                            context.
                          </p>
                        </div>
                      </>
                    ) : (
                      <section className="panel result-panel">
                        <div className="panel-top">
                          <div className="tabs">
                            <button
                              className={
                                resultTab === "result" ? "selected" : ""
                              }
                              onClick={() => setResultTab("result")}
                            >
                              Result
                            </button>
                            <button
                              className={
                                resultTab === "activity" ? "selected" : ""
                              }
                              onClick={() => setResultTab("activity")}
                            >
                              Activity <small>{active.events.length}</small>
                            </button>
                          </div>
                          <span className="result-badge">
                            {active.simulated ? "MOCK" : "LIVE"} ·{" "}
                            {active.status}
                          </span>
                        </div>
                        {resultTab === "result" ? (
                          <>
                            <div className="result-body">
                              <div className="result-model">
                                <span className="status-dot" />
                                {active.model ?? "No eligible model"}
                                <small>
                                  {new Date(
                                    active.created_at,
                                  ).toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  })}
                                </small>
                              </div>
                              <pre>
                                {active.result ??
                                  (active.status === "accepted"
                                    ? "This run was accepted but no completed result is saved. It has not been automatically reissued."
                                    : active.route_reason)}
                              </pre>
                            </div>
                            <div className="result-footer">
                              <span>
                                Saved in{" "}
                                {health?.storage === "supabase"
                                  ? "Supabase"
                                  : "local database"}
                              </span>
                              <button onClick={download}>Export JSON ↗</button>
                            </div>
                          </>
                        ) : (
                          <ol className="timeline">
                            {active.events.map((event) => (
                              <li key={event.sequence}>
                                <span>
                                  {String(event.sequence).padStart(2, "0")}
                                </span>
                                <div>
                                  <strong>
                                    {event.type.replaceAll("_", " ")}
                                  </strong>
                                  <p>{event.message}</p>
                                </div>
                              </li>
                            ))}
                            <li>
                              <span>✓</span>
                              <div>
                                <strong>Saved record retrieved</strong>
                                <p>
                                  These are recorded step events, not a live
                                  token stream.
                                </p>
                              </div>
                            </li>
                          </ol>
                        )}
                      </section>
                    )}
                  </div>
                  <aside className="context-column">
                    <section className="panel context-panel">
                      <div className="panel-top">
                        <h2>Context capsule</h2>
                        <span className="capsule-icon">▱</span>
                      </div>
                      <p className="panel-intro">
                        The important things travel with your task.
                      </p>
                      <div className="capsule-status">
                        <span className="status-dot" />
                        {active?.context
                          ? "Captured · version 1"
                          : "Ready when you are"}
                      </div>
                      <div className="context-field">
                        <span>01 / OBJECTIVE</span>
                        <p>
                          {active?.context?.objective ??
                            "Your task will be preserved here, exactly as you wrote it."}
                        </p>
                      </div>
                      <div className="context-field">
                        <span>02 / REQUIREMENTS</span>
                        <p>
                          {active?.context?.exact_constraints ||
                            "No explicit requirements saved yet."}
                        </p>
                      </div>
                      <div className="context-field">
                        <span>03 / NEXT STEP</span>
                        <p>
                          {active?.context?.next_action ??
                            "Create a task to start a portable context record."}
                        </p>
                      </div>
                      <div className="context-bottom">
                        {active ? (
                          <>
                            <span>↳</span> Source: run {active.id.slice(0, 8)}
                          </>
                        ) : (
                          <>
                            <span>↳</span> Original input stays attached.
                          </>
                        )}
                      </div>
                    </section>
                    <section className="route-card">
                      <div className="section-heading">
                        AVAILABLE ROUTE <span>01</span>
                      </div>
                      <div className="route-node">
                        <div className="node-icon">BF</div>
                        <div>
                          <strong>Local mock</strong>
                          <span>mock-v1 · text</span>
                        </div>
                        <span className="status-dot" />
                      </div>
                      <div className="route-line" />
                      <div className="route-destination">
                        ◉ <span>Your saved result</span>
                      </div>
                      <p>
                        Gemini and Cloudflare connect next. Fallbacks remain
                        disabled until verified.
                      </p>
                      <button onClick={() => setPage("connections")}>
                        Manage connections ↗
                      </button>
                    </section>
                  </aside>
                </div>
              )}
              {page === "history" && (
                <section className="panel history">
                  <div className="panel-top">
                    <h2>Saved tasks</h2>
                    <span className="small-label">LATEST 30</span>
                  </div>
                  {runs.length ? (
                    runs.map((run) => (
                      <div className="history-row" key={run.id}>
                        <button onClick={() => void openRun(run.id)}>
                          <strong>{run.input.prompt}</strong>
                          <span>
                            {new Date(run.created_at).toLocaleString()} ·{" "}
                            {run.model ?? "No route"} · {run.status} · MOCK
                          </span>
                        </button>
                        <button
                          className="delete"
                          aria-label={`Delete task ${run.input.prompt.slice(0, 40)}`}
                          onClick={() => void removeRun(run.id)}
                        >
                          Delete
                        </button>
                      </div>
                    ))
                  ) : (
                    <div className="empty-result">
                      <h3>No saved tasks yet.</h3>
                      <p>Create your first mock task in the playground.</p>
                      <button onClick={newTask}>New task ↗</button>
                    </div>
                  )}
                </section>
              )}
              {page === "connections" && (
                <section className="connections">
                  {providers.map((provider) => (
                    <article className="panel provider-card" key={provider.id}>
                      <div className="panel-top">
                        <h2>{provider.name}</h2>
                        <span
                          className={
                            provider.available
                              ? "connection-ready"
                              : "small-label"
                          }
                        >
                          {provider.available ? "READY" : "NOT CONFIGURED"}
                        </span>
                      </div>
                      <p>{provider.status}</p>
                      <div className="provider-details">
                        <span>{provider.modalities.join(" + ")}</span>
                        <span>
                          {provider.simulated
                            ? "No inference usage"
                            : "Quota: unknown"}
                        </span>
                      </div>
                      <div className="provider-bottom">
                        {provider.simulated
                          ? "Runs locally. No task content is sent to Gemini or Cloudflare."
                          : "Needs account setup, free-tier verification, and a successful live request before activation."}
                      </div>
                    </article>
                  ))}
                  <div className="panel connection-note">
                    <h2>Your choice stays in control.</h2>
                    <p>
                      The day-one worker only supports the local mock route.
                      Exact model locks and provider allowlists are enforced by
                      the API. No automatic fallback or real image processing is
                      enabled yet.
                    </p>
                  </div>
                </section>
              )}
            </>
          )}
          <footer className="page-footer">
            <span>
              BLACK FIRE <span className="footer-divider">/</span> Built for
              continuity.
            </span>
            <span>
              Day-one prototype · {health?.storage ?? "database offline"}
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}
