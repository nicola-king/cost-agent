from app.core.db import SessionLocal
from app.plugins.base import gateway


def _payload():
    return {
        "resources": {
            "labor": {"unit": "工日", "drawing_quantity": 120, "quota_quantity": 135},
            "material": {"unit": "t", "drawing_quantity": 82, "quota_quantity": 78},
            "equipment": {"unit": "台班", "drawing_quantity": 30, "quota_quantity": 30},
        }
    }


def test_resource_control_line_takes_lower_quantity():
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p03.resource_control_line", "P-RESOURCE-1", "cost", "cost_lead", _payload())
    assert result.outcome == "success"
    rows = result.data["resources"]
    assert rows["labor"]["baseline_control_quantity"] == 120
    assert rows["labor"]["baseline_source"] == "drawing"
    assert rows["material"]["baseline_control_quantity"] == 78
    assert rows["material"]["baseline_source"] == "quota"
    assert rows["equipment"]["baseline_control_quantity"] == 30
    assert rows["equipment"]["baseline_source"] == "equal"
    assert result.data["baseline_is_immutable"] is True


def test_approved_change_adjusts_current_not_baseline():
    payload = _payload()
    payload["resources"]["material"]["approved_change_delta"] = 5
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p03.resource_control_line", "P-RESOURCE-2", "cost", "cost_lead", payload)
    material = result.data["resources"]["material"]
    assert material["baseline_control_quantity"] == 78
    assert material["approved_change_delta"] == 5
    assert material["current_control_quantity"] == 83
    assert material["state"] == "adjusted"


def test_missing_drawing_or_quota_returns_needs_information():
    payload = _payload()
    del payload["resources"]["equipment"]["quota_quantity"]
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p03.resource_control_line", "P-RESOURCE-3", "cost", "cost_lead", payload)
    assert result.outcome == "needs_information"
    assert "resources.equipment.quota_quantity" in result.data["required"]
    assert "labor" in result.data["partial"]


def test_negative_quantity_is_rejected():
    payload = _payload()
    payload["resources"]["labor"]["drawing_quantity"] = -1
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p03.resource_control_line", "P-RESOURCE-4", "cost", "cost_lead", payload)
    assert result.outcome == "failed"
    assert result.data["reason"] == "negative_quantity_not_allowed"
