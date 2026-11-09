import asyncio
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from blackfire.auth import Identity, identity
from blackfire.config import Settings
from blackfire.main import create_app
from blackfire.models import Run, RunInput
from blackfire.storage import SupabaseStore


@pytest.fixture
def app(tmp_path):
    return create_app(Settings(sqlite_path=tmp_path / "test.sqlite3", _env_file=None))


def post(client, body=None, key=None):
    return client.post('/api/v1/runs', json=body or {"prompt": "Explain a loop"},
                       headers={"Idempotency-Key": str(key or uuid4())})


def test_mock_is_honest_and_context_is_exact(app):
    with TestClient(app) as client:
        assert client.get('/health/ready').json()['inference'] == 'mock'
        response = post(client, {"prompt": "Explain a loop", "constraints": "  Keep EXACT dates.\n3 bullets."})
        assert response.status_code == 201
        run = response.json()
        assert run['simulated'] and run['provider'] == 'mock' and run['model'] == 'mock-v1'
        assert 'no AI model was called' in run['result']
        assert run['context']['exact_constraints'] == "  Keep EXACT dates.\n3 bullets."
        assert [e['sequence'] for e in run['events']] == list(range(1, len(run['events']) + 1))
        assert client.get('/api/v1/runs/' + run['id']).json() == run


def test_idempotency_does_not_dispatch_again_and_rejects_changed_input(app):
    with TestClient(app) as client:
        key = uuid4()
        first = post(client, key=key)
        second = post(client, key=key)
        assert first.json() == second.json()
        assert second.status_code == 200
        assert len(client.get('/api/v1/runs').json()) == 1
        assert post(client, {"prompt": "Different task"}, key).status_code == 409


@pytest.mark.parametrize('policy', [
    {"locked_model": "gemini-unconfigured"}, {"allowed_providers": ["gemini", "cloudflare"]},
])
def test_unavailable_or_unapproved_route_pauses(app, policy):
    with TestClient(app) as client:
        run = post(client, {"prompt": "Hello", **policy}).json()
        assert run['status'] == 'paused'
        assert run['result'] is None and run['provider'] is None
        assert not any(e['type'] == 'provider_started' for e in run['events'])


def test_restart_retains_result(tmp_path):
    settings = Settings(sqlite_path=tmp_path / 'restart.sqlite3', _env_file=None)
    with TestClient(create_app(settings)) as client:
        run = post(client).json()
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/v1/runs/' + run['id']).json() == run


def test_other_owner_cannot_read_delete_or_list(app):
    first, second = Identity(uuid4()), Identity(uuid4())
    app.dependency_overrides[identity] = lambda: first
    with TestClient(app) as client:
        run = post(client).json()
        app.dependency_overrides[identity] = lambda: second
        assert client.get('/api/v1/runs/' + run['id']).status_code == 404
        assert client.get('/api/v1/runs').json() == []
        assert client.delete('/api/v1/runs/' + run['id']).status_code == 204
        app.dependency_overrides[identity] = lambda: first
        assert client.get('/api/v1/runs/' + run['id']).status_code == 200
        client.delete('/api/v1/runs/' + run['id'])
        assert client.get('/api/v1/runs/' + run['id']).status_code == 404


@pytest.mark.parametrize('body', [
    {"prompt": " "}, {"prompt": "x" * 8001}, {"prompt": "hello", "owner_id": str(uuid4())},
    {"prompt": "hello", "allowed_providers": []}, {"prompt": "hello", "image": "fake"},
])
def test_invalid_input_rejected(app, body):
    with TestClient(app) as client:
        assert post(client, body).status_code == 422


def test_local_demo_rejects_untrusted_origin_and_host(app):
    with TestClient(app) as client:
        assert client.get('/api/v1/runs', headers={"Origin": "https://evil.example"}).status_code == 403
        assert client.get('/api/v1/runs', headers={"Host": "evil.example"}).status_code == 403


def test_production_rejects_local_anonymous_mode():
    with pytest.raises(ValidationError):
        Settings(app_env='production', storage_backend='sqlite', _env_file=None)


def test_supabase_mode_requires_auth():
    app = create_app(Settings(storage_backend='supabase', supabase_url='https://example.supabase.co',
                              supabase_publishable_key='public-test-key', _env_file=None))
    with TestClient(app) as client:
        assert client.get('/api/v1/runs').status_code == 401


def test_supabase_adapter_scopes_reads_and_forwards_user_jwt():
    owner = uuid4()
    run = Run(owner_id=owner, idempotency_key=uuid4(), request_hash='abc', input=RunInput(prompt='test'))

    def handler(request):
        assert request.headers['Authorization'] == 'Bearer user-token'
        assert request.headers['apikey'] == 'publishable-key'
        assert request.url.params['owner_id'] == f'eq.{owner}'
        assert request.url.params['id'] == f'eq.{run.id}'
        return httpx.Response(200, json=[{'payload': run.model_dump(mode='json')}])

    async def check():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            store = SupabaseStore(client, 'https://example.supabase.co', 'publishable-key')
            assert await store.get(run.id, owner, 'user-token') == run
    asyncio.run(check())
