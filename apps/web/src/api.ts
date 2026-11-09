import { createClient } from "@supabase/supabase-js";

const base = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
const url = import.meta.env.VITE_SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;
export const supabase = url && key ? createClient(url, key) : null;

export type TaskType = "summarize" | "extract" | "code_review";
export type RunInput = {
  prompt: string;
  task_type: TaskType;
  constraints: string;
  allowed_providers: string[];
  locked_model: string | null;
};
export type Run = {
  id: string;
  created_at: string;
  status: "accepted" | "completed" | "paused" | "failed";
  input: RunInput;
  provider: string | null;
  model: string | null;
  simulated: boolean;
  result: string | null;
  route_reason: string;
  events: {
    sequence: number;
    type: string;
    message: string;
    timestamp: string;
  }[];
  context: {
    version: number;
    objective: string;
    exact_constraints: string;
    source_run_id: string;
    completed_steps: string[];
    next_action: string;
  } | null;
};
export type Provider = {
  id: string;
  name: string;
  models: string[];
  modalities: string[];
  available: boolean;
  simulated: boolean;
  status: string;
  quota_remaining: number | null;
};
export type Health = {
  status: string;
  storage: string;
  inference: string;
  auth_required: boolean;
};

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const session = supabase
    ? (await supabase.auth.getSession()).data.session
    : null;
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (session) headers.set("Authorization", `Bearer ${session.access_token}`);
  let response: Response;
  try {
    response = await fetch(base + path, {
      ...options,
      headers,
      signal: AbortSignal.timeout(25000),
    });
  } catch {
    throw new Error(
      "API unreachable. Check that the backend is running. Retrying the unchanged task uses the same request key.",
    );
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : `Request failed (${response.status}). Check your input or session.`,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
