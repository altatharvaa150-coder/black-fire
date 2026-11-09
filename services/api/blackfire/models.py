from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def now() -> str:
    return datetime.now(UTC).isoformat()


class RunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=8000)
    task_type: Literal["summarize", "extract", "code_review"] = "summarize"
    constraints: str = Field(default="", max_length=2000)
    allowed_providers: list[Literal["mock", "gemini", "cloudflare"]] = Field(
        default_factory=lambda: ["mock"], min_length=1, max_length=3
    )
    locked_model: str | None = Field(default=None, max_length=150)

    @field_validator("prompt")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Enter a task")
        return value


class Event(BaseModel):
    sequence: int
    type: str
    message: str
    timestamp: str = Field(default_factory=now)


class Capsule(BaseModel):
    version: int = 1
    objective: str
    exact_constraints: str
    source_run_id: str
    completed_steps: list[str] = Field(default_factory=list)
    next_action: str = "Run a real provider after configuration and free-tier verification."


class Run(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID
    idempotency_key: UUID
    request_hash: str
    created_at: str = Field(default_factory=now)
    status: Literal["accepted", "completed", "paused", "failed"] = "accepted"
    input: RunInput
    provider: str | None = None
    model: str | None = None
    simulated: bool = True
    result: str | None = None
    route_reason: str = ""
    events: list[Event] = Field(default_factory=list)
    context: Capsule | None = None


class Provider(BaseModel):
    id: str
    name: str
    models: list[str]
    modalities: list[str]
    available: bool
    simulated: bool
    status: str
    quota_remaining: int | None = None


PROVIDERS = [
    Provider(id="mock", name="Local mock", models=["mock-v1"], modalities=["text"],
             available=True, simulated=True, status="Ready · deterministic fixture"),
    Provider(id="gemini", name="Google Gemini", models=[], modalities=["text", "image"],
             available=False, simulated=False, status="Not configured · access unverified"),
    Provider(id="cloudflare", name="Cloudflare Workers AI", models=[],
             modalities=["text", "image"], available=False, simulated=False,
             status="Not configured · access unverified"),
]
