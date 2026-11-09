import hashlib
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth import Identity, identity
from .config import Settings
from .models import PROVIDERS, Event, Run, RunInput
from .storage import SQLiteStore, StorageUnavailable, SupabaseStore
from .workflow import execute


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            app.state.http = client
            app.state.store = (
                SQLiteStore(settings.sqlite_path) if settings.storage_backend == "sqlite"
                else SupabaseStore(client, settings.supabase_url, settings.supabase_publishable_key)
            )
            yield

    app = FastAPI(title="Black Fire API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origins.split(","),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )

    @app.exception_handler(StorageUnavailable)
    async def storage_error(request: Request, exc: StorageUnavailable):
        return JSONResponse(status_code=503, content={"detail": "Database unavailable. Retry with the same request key."})

    @app.middleware("http")
    async def private_responses(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/health/live")
    async def live():
        return {"status": "ok", "service": "black-fire"}

    @app.get("/health/ready")
    async def ready():
        await app.state.store.ready()
        return {"status": "ready", "storage": settings.storage_backend,
                "inference": "mock", "auth_required": settings.storage_backend == "supabase"}

    @app.get("/api/v1/providers")
    async def providers():
        return PROVIDERS

    @app.post("/api/v1/runs", response_model=Run, status_code=201)
    async def create_run(
        body: RunInput, response: Response,
        user: Annotated[Identity, Depends(identity)],
        idempotency_key: Annotated[UUID, Header()],
    ):
        digest = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
        new_run = Run(owner_id=user.id, idempotency_key=idempotency_key,
                      request_hash=digest, input=body)
        new_run.events.append(Event(sequence=1, type="accepted", message="Task accepted."))
        saved, created = await app.state.store.create(new_run, user.token)
        if not created:
            if saved.request_hash != digest:
                raise HTTPException(409, "This request key belongs to a different task")
            response.status_code = 200
            # A previously accepted task is returned as pending/uncertain, never redispatched.
            return saved
        completed = await execute(saved)
        await app.state.store.save(completed, user.token)
        return completed

    @app.get("/api/v1/runs", response_model=list[Run])
    async def list_runs(user: Annotated[Identity, Depends(identity)]):
        return await app.state.store.list(user.id, user.token)

    @app.get("/api/v1/runs/{run_id}", response_model=Run)
    async def get_run(run_id: UUID, user: Annotated[Identity, Depends(identity)]):
        run = await app.state.store.get(run_id, user.id, user.token)
        if run is None:
            raise HTTPException(404, "Run not found")
        return run

    @app.delete("/api/v1/runs/{run_id}", status_code=204)
    async def delete_run(run_id: UUID, user: Annotated[Identity, Depends(identity)]):
        await app.state.store.delete(run_id, user.id, user.token)
        return Response(status_code=204)

    return app


app = create_app()
