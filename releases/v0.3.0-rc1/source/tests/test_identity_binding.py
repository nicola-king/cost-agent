import json

from fastapi.testclient import TestClient

from app.main import app


def test_anonymous_cannot_escalate_commercial_role(monkeypatch):
    monkeypatch.delenv("CCI_LOCAL_IDENTITIES_JSON", raising=False)
    client = TestClient(app)
    response = client.get("/api/projects/P-NONE/commercial-access?role=cost_lead")
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "viewer"
    assert body["allowed"] is False
    assert response.headers["X-CCI-Role"] == "viewer"
    assert response.headers["X-CCI-Authenticated"] == "false"


def test_server_token_resolves_privileged_role(monkeypatch):
    monkeypatch.setenv(
        "CCI_LOCAL_IDENTITIES_JSON",
        json.dumps({"pm-secret": {"actor": "zhangsan", "role": "project_manager"}}),
    )
    client = TestClient(app)
    response = client.get(
        "/api/projects/P-NONE/commercial-access?role=technical",
        headers={"X-CCI-Identity-Token": "pm-secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "project_manager"
    assert body["allowed"] is True
    assert response.headers["X-CCI-Actor"] == "zhangsan"
    assert response.headers["X-CCI-Authenticated"] == "true"


def test_capability_body_role_is_overridden(monkeypatch):
    monkeypatch.delenv("CCI_LOCAL_IDENTITIES_JSON", raising=False)
    client = TestClient(app)
    response = client.post(
        "/api/capabilities/execute",
        json={
            "capability_id": "p04.cost_plan",
            "project_id": "P-SECURITY",
            "actor": "attacker",
            "role": "cost_lead",
            "payload": {},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "failed"
    assert body["data"]["reason"] == "commercial_confidential"
    assert response.headers["X-CCI-Role"] == "viewer"
