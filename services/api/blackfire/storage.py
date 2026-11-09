import sqlite3
from pathlib import Path
from uuid import UUID

import httpx

from .models import Run


class StorageUnavailable(Exception):
    pass


class SQLiteStore:
    """Single-machine development store. Never enabled in production."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, idempotency_key TEXT NOT NULL,
                created_at TEXT NOT NULL, payload TEXT NOT NULL,
                UNIQUE(owner_id, idempotency_key))""")
            db.execute("CREATE INDEX IF NOT EXISTS runs_owner_created ON runs(owner_id, created_at)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    async def ready(self):
        with self.connect() as db:
            db.execute("SELECT 1 FROM runs LIMIT 1")

    async def create(self, run: Run, token: str) -> tuple[Run, bool]:
        with self.connect() as db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO runs VALUES (?, ?, ?, ?, ?)",
                (str(run.id), str(run.owner_id), str(run.idempotency_key),
                 run.created_at, run.model_dump_json()),
            )
            if cursor.rowcount:
                return run, True
            row = db.execute("SELECT payload FROM runs WHERE owner_id=? AND idempotency_key=?",
                             (str(run.owner_id), str(run.idempotency_key))).fetchone()
            return Run.model_validate_json(row[0]), False

    async def save(self, run: Run, token: str):
        with self.connect() as db:
            db.execute("UPDATE runs SET payload=? WHERE id=? AND owner_id=?",
                       (run.model_dump_json(), str(run.id), str(run.owner_id)))

    async def get(self, run_id: UUID, owner_id: UUID, token: str) -> Run | None:
        with self.connect() as db:
            row = db.execute("SELECT payload FROM runs WHERE id=? AND owner_id=?",
                             (str(run_id), str(owner_id))).fetchone()
        return Run.model_validate_json(row[0]) if row else None

    async def list(self, owner_id: UUID, token: str) -> list[Run]:
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM runs WHERE owner_id=? ORDER BY created_at DESC LIMIT 30",
                              (str(owner_id),)).fetchall()
        return [Run.model_validate_json(row[0]) for row in rows]

    async def delete(self, run_id: UUID, owner_id: UUID, token: str):
        with self.connect() as db:
            db.execute("DELETE FROM runs WHERE id=? AND owner_id=?", (str(run_id), str(owner_id)))


class SupabaseStore:
    """Forward verified user JWTs to PostgREST; no service-role bypass."""

    def __init__(self, client: httpx.AsyncClient, url: str, key: str):
        self.client, self.url, self.key = client, url.rstrip("/"), key

    async def request(self, method: str, token: str = "", **kwargs):
        headers = {"apikey": self.key, "Prefer": "return=representation"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = await self.client.request(
                method, f"{self.url}/rest/v1/blackfire_runs", headers=headers, **kwargs
            )
        except httpx.HTTPError as exc:
            raise StorageUnavailable from exc
        if response.status_code not in (200, 201, 204, 409):
            raise StorageUnavailable
        return response

    async def ready(self):
        # Anonymous has SELECT grant but no matching policy: an empty result proves
        # table availability without exposing any user's data or calling a model.
        response = await self.request("GET", params={"select": "id", "limit": "0"})
        if response.status_code != 200:
            raise StorageUnavailable

    async def create(self, run: Run, token: str) -> tuple[Run, bool]:
        response = await self.request("POST", token, json={
            "id": str(run.id), "owner_id": str(run.owner_id),
            "idempotency_key": str(run.idempotency_key), "created_at": run.created_at,
            "payload": run.model_dump(mode="json"),
        })
        if response.status_code == 409:
            existing = await self.request("GET", token, params={
                "owner_id": f"eq.{run.owner_id}",
                "idempotency_key": f"eq.{run.idempotency_key}", "select": "payload",
            })
            rows = existing.json()
            if not rows:
                raise StorageUnavailable
            return Run.model_validate(rows[0]["payload"]), False
        return run, True

    async def save(self, run: Run, token: str):
        response = await self.request("PATCH", token, params={
            "id": f"eq.{run.id}", "owner_id": f"eq.{run.owner_id}",
        }, json={"payload": run.model_dump(mode="json")})
        if response.status_code != 200 or not response.json():
            raise StorageUnavailable

    async def get(self, run_id: UUID, owner_id: UUID, token: str) -> Run | None:
        response = await self.request("GET", token, params={
            "id": f"eq.{run_id}", "owner_id": f"eq.{owner_id}", "select": "payload",
        })
        rows = response.json()
        return Run.model_validate(rows[0]["payload"]) if rows else None

    async def list(self, owner_id: UUID, token: str) -> list[Run]:
        response = await self.request("GET", token, params={
            "owner_id": f"eq.{owner_id}", "select": "payload",
            "order": "created_at.desc", "limit": "30",
        })
        return [Run.model_validate(row["payload"]) for row in response.json()]

    async def delete(self, run_id: UUID, owner_id: UUID, token: str):
        await self.request("DELETE", token, params={
            "id": f"eq.{run_id}", "owner_id": f"eq.{owner_id}",
        })
