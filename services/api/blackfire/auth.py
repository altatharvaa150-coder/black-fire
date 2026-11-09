import base64
import json
import time
from dataclasses import dataclass
from uuid import UUID

import httpx
from fastapi import HTTPException, Request

LOCAL_OWNER = UUID("00000000-0000-4000-8000-000000000001")


@dataclass
class Identity:
    id: UUID
    token: str = ""


async def identity(request: Request) -> Identity:
    settings = request.app.state.settings
    if settings.storage_backend == "sqlite":
        if request.client is None or request.client.host not in ("127.0.0.1", "::1", "testclient"):
            raise HTTPException(403, "Local demo is available only from loopback")
        if request.url.hostname not in ("127.0.0.1", "localhost", "::1", "testserver"):
            raise HTTPException(403, "Local demo requires a localhost hostname")
        origin = request.headers.get("origin")
        if origin and origin not in settings.cors_origins.split(","):
            raise HTTPException(403, "Untrusted origin")
        return Identity(LOCAL_OWNER)
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(401, "Sign in to access your workspace")
    token = header[7:]
    # Auth validates the token against this project's signing keys and active user.
    # Never authorize from a client-supplied owner ID or unverified decoded JWT.
    try:
        response = await request.app.state.http.get(
            settings.supabase_url.rstrip("/") + "/auth/v1/user",
            headers={"apikey": settings.supabase_publishable_key, "Authorization": header},
        )
    except httpx.HTTPError:
        raise HTTPException(503, "Authentication service is unavailable") from None
    if response.status_code >= 500:
        raise HTTPException(503, "Authentication service is unavailable")
    if response.status_code != 200:
        raise HTTPException(401, "Session expired or invalid; sign in again")
    try:
        user_id = UUID(response.json()["id"])
        segment = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
        audience = claims.get("aud")
        valid_audience = audience == "authenticated" or (
            isinstance(audience, list) and "authenticated" in audience
        )
        if (not valid_audience
            or claims["iss"] != settings.supabase_url.rstrip("/") + "/auth/v1"
            or claims["sub"] != str(user_id) or claims["exp"] <= time.time()):
            raise ValueError("Invalid session claims")
    except (ValueError, KeyError, IndexError, TypeError):
        raise HTTPException(401, "Invalid session claims") from None
    return Identity(user_id, token)
