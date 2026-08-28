from httpx import ASGITransport, AsyncClient

from app.db import init_db
from app.main import app

HEADERS = {"X-Workspace-ID": "test", "X-Actor": "alex", "X-Role": "approver"}


async def client() -> AsyncClient:
    await init_db()
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_health_and_readiness() -> None:
    async with await client() as http:
        assert (await http.get("/healthz")).json() == {"status": "ok"}
        assert (await http.get("/readyz")).json() == {"status": "ready"}


async def test_create_is_idempotent() -> None:
    payload = {
        "resource": "staging/catalog",
        "permission": "read",
        "environment": "staging",
        "requester": "alex",
        "reason": "Validate the catalog release candidate before promotion.",
        "ttl_hours": 4,
    }
    async with await client() as http:
        first = await http.post(
            "/api/v1/access-requests",
            json=payload,
            headers={**HEADERS, "Idempotency-Key": "same-1"},
        )
        second = await http.post(
            "/api/v1/access-requests",
            json=payload,
            headers={**HEADERS, "Idempotency-Key": "same-1"},
        )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


async def test_requester_cannot_approve() -> None:
    payload = {
        "resource": "prod/payments/logs",
        "permission": "read",
        "environment": "production",
        "requester": "alex",
        "reason": "Investigate a production issue with a linked incident.",
    }
    async with await client() as http:
        created = await http.post("/api/v1/access-requests", json=payload, headers=HEADERS)
        response = await http.post(
            f"/api/v1/access-requests/{created.json()['id']}/approve",
            json={"note": "not allowed"},
            headers={**HEADERS, "X-Role": "requester"},
        )
    assert response.status_code == 403


async def test_approval_updates_overview() -> None:
    payload = {
        "resource": "staging/catalog",
        "permission": "admin",
        "environment": "staging",
        "requester": "alex",
        "reason": "Run the migration verification suite for the release candidate.",
    }
    async with await client() as http:
        created = await http.post("/api/v1/access-requests", json=payload, headers=HEADERS)
        request_id = created.json()["id"]
        approved = await http.post(
            f"/api/v1/access-requests/{request_id}/approve",
            json={"note": "Approved for the release window."},
            headers=HEADERS,
        )
        overview = await http.get("/api/v1/overview", headers=HEADERS)
    assert approved.json()["status"] == "approved"
    assert overview.json()["decisions_today"] >= 1


async def test_audit_chain_links_events() -> None:
    payload = {
        "resource": "staging/catalog",
        "permission": "read",
        "environment": "staging",
        "requester": "alex",
        "reason": "Review the latest staging telemetry before release approval.",
    }
    async with await client() as http:
        await http.post("/api/v1/access-requests", json=payload, headers=HEADERS)
        events = (await http.get("/api/v1/audit", headers=HEADERS)).json()
    assert len(events) >= 1
    assert events[0]["prev_hash"] is not None or len(events) == 1
