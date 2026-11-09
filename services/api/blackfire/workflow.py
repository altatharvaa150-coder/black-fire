from typing import TypedDict

from .models import Capsule, Event, Run


class State(TypedDict):
    run: Run


def event(run: Run, kind: str, message: str):
    run.events.append(Event(sequence=len(run.events) + 1, type=kind, message=message))


def route(state: State):
    run = state["run"]
    eligible = "mock" in run.input.allowed_providers
    compatible = run.input.locked_model in (None, "mock-v1")
    if not eligible or not compatible:
        run.status = "paused"
        run.route_reason = "No configured route satisfies your allowlist and exact model lock."
        event(run, "waiting", run.route_reason)
    else:
        run.provider, run.model = "mock", "mock-v1"
        run.route_reason = "Local mock is allowed and supports text. No external provider receives data."
        event(run, "routing", run.route_reason)
    return {"run": run}


def worker(state: State):
    run = state["run"]
    if run.status == "paused":
        return {"run": run}
    event(run, "provider_started", "Running the deterministic mock fixture (not AI inference).")
    run.result = (
        "MOCK RESULT — no AI model was called.\n\n"
        f"Your {run.input.task_type.replace('_', ' ')} task was received and saved.\n\n"
        "Task preview:\n" + run.input.prompt[:500] +
        ("…" if len(run.input.prompt) > 500 else "") + "\n\n"
        "This fixture verifies the task → route → result → saved history flow. "
        "It does not summarize, extract facts, or review your code. "
        "Connect and verify a free provider to generate an actual answer."
    )
    run.status = "completed"
    event(run, "completed", "Mock execution completed. Provider usage: zero.")
    return {"run": run}


def capsule(state: State):
    run = state["run"]
    run.context = Capsule(
        objective=run.input.prompt,
        exact_constraints=run.input.constraints,
        source_run_id=str(run.id),
        completed_steps=["Mock pipeline verified"] if run.status == "completed" else [],
    )
    event(run, "context_created", "Original task and exact constraints preserved in context v1.")
    return {"run": run}


async def execute(run: Run) -> Run:
    """Day-one deterministic pipeline; no durable graph or autonomous agent yet.

    These explicit steps are ready to become LangGraph nodes on day two.
    Windows application control currently blocks its native serializer dependency.
    """
    state: State = {"run": run}
    for step in (route, worker, capsule):
        state = step(state)
    return state["run"]
