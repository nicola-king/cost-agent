import json

from fastapi.testclient import TestClient

from app.main import app


def _config(monkeypatch):
    monkeypatch.setenv(
        "CCI_PREREGISTERED_IDENTITIES_JSON",
        json.dumps(
            {
                "13800000000": {
                    "actor": "张三",
                    "role": "project_manager",
                    "department": "project",
                    "verification_secret": "pm-initial-code",
                },
                "TECH-001": {
                    "actor": "李四",
                    "role": "technical",
                    "department": "technical",
                    "verification_secret": "tech-initial-code",
                },
            },
            ensure_ascii=False,
        ),
    )


def test_anonymous_cannot_escalate_commercial_role(monkeypatch):
    monkeypatch.delenv("CCI_PREREGISTERED_IDENTITIES_JSON", raising=False)
    client = TestClient(app)
    response = client.get("/api/projects/P-NONE/commercial-access?role=cost_lead")
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "viewer"
    assert body["allowed"] is False
    assert response.headers["X-CCI-Role"] == "viewer"
    assert response.headers["X-CCI-Authenticated"] == "false"


def test_preregistered_identity_first_login_registers_session(monkeypatch):
    _config(monkeypatch)
    client = TestClient(app)
    login = client.post(
        "/api/auth/register",
        json={
            "login_id": "13800000000",
            "verification_secret": "pm-initial-code",
            "device_id": "phone-001",
        },
    )
    assert login.status_code == 200
    data = login.json()
    assert data["authenticated"] is True
    assert data["actor"] == "张三"
    assert data["role"] == "project_manager"
    token = data["session_token"]

    me = client.get("/api/auth/me", headers={"X-CCI-Identity-Token": token})
    assert me.status_code == 200
    assert me.json()["authenticated"] is True
    assert me.json()["role"] == "project_manager"

    commercial = client.get(
        "/api/projects/P-NONE/commercial-access?role=technical",
        headers={"X-CCI-Identity-Token": token},
    )
    assert commercial.status_code == 200
    assert commercial.json()["role"] == "project_manager"
    assert commercial.json()["allowed"] is True


def test_unregistered_or_wrong_verification_stays_viewer(monkeypatch):
    _config(monkeypatch)
    client = TestClient(app)
    missing = client.post(
        "/api/auth/register",
        json={"login_id": "UNKNOWN", "verification_secret": "x", "device_id": "d1"},
    )
    assert missing.json()["authenticated"] is False
    assert missing.json()["role"] == "viewer"
    assert missing.json()["status"] == "not_preregistered"

    wrong = client.post(
        "/api/auth/register",
        json={"login_id": "TECH-001", "verification_secret": "wrong", "device_id": "d2"},
    )
    assert wrong.json()["authenticated"] is False
    assert wrong.json()["role"] == "viewer"
    assert wrong.json()["status"] == "verification_failed"


def test_capability_body_role_is_overridden(monkeypatch):
    monkeypatch.delenv("CCI_PREREGISTERED_IDENTITIES_JSON", raising=False)
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
