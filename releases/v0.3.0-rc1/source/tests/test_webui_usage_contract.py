from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_desktop_webui_usage_contract():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    for marker in (
        'id="projectSelect"',
        'id="roleSelect"',
        'id="stageStrip"',
        'id="workspace"',
        'id="auditList"',
        'id="traceObject"',
        '/static/app.js',
    ):
        assert marker in html


def test_mobile_webui_is_operational_not_static_placeholder():
    response = client.get("/mobile")
    assert response.status_code == 200
    html = response.text
    for marker in (
        'id="mobileProject"',
        'id="mobileDepartment"',
        'id="mobileTasks"',
        'id="evidenceForm"',
        'id="evidenceFile"',
        '/static/mobile.js',
    ):
        assert marker in html


def test_webui_health_contract():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["architecture"] == "v1.0-frozen"
