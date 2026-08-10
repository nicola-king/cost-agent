from app.core.db import SessionLocal
from app.plugins.base import gateway


def _run(payload, project="P-MONTHLY"):
    with SessionLocal() as db:
        return gateway.execute(db, "p06.monthly_control_gate", project, "cost", "cost_lead", payload)[1]


def _snapshot():
    return {
        "forecast_revenue": 12000000,
        "forecast_cost": 10500000,
        "forecast_profit": 1500000,
        "change_amount": 650000,
        "risk_amount": 320000,
        "evidence_gap_count": 3,
        "material_batch_conflict_count": 1,
        "open_responsibility_count": 2,
    }


def test_monthly_snapshot_requires_complete_commercial_and_control_fields():
    data = _snapshot()
    del data["risk_amount"]
    result = _run({"month": "2026-08", "snapshot": data})
    assert result.outcome == "needs_information"
    assert "snapshot.risk_amount" in result.data["required"]


def test_monthly_snapshot_stops_before_declaration():
    result = _run({"month": "2026-08", "snapshot": _snapshot()})
    assert result.outcome == "partial"
    assert result.data["state"] == "snapshot_ready_for_declaration"


def test_declared_month_requires_cost_briefing():
    result = _run({"month": "2026-08", "snapshot": _snapshot(), "declared": True})
    assert result.outcome == "partial"
    assert result.data["state"] == "declared_waiting_for_briefing"


def test_briefing_requires_responsibility_register_and_personal_signatures():
    payload = {
        "month": "2026-08",
        "snapshot": _snapshot(),
        "declared": True,
        "briefing": {"held": True, "date": "2026-08-31", "presenter": "cost_lead"},
        "responsibilities": [
            {"department": "technical", "assignee": "Zhang", "action": "complete hidden-work evidence", "due_date": "2026-09-05", "signed": True},
            {"department": "production", "assignee": "Li", "action": "close measurement gap", "due_date": "2026-09-03", "signed": False},
        ],
    }
    result = _run(payload)
    assert result.outcome == "partial"
    assert result.data["state"] == "briefed_waiting_for_signatures"
    assert result.data["unsigned_count"] == 1


def test_monthly_control_closes_only_after_all_responsible_people_sign():
    payload = {
        "month": "2026-08",
        "snapshot": _snapshot(),
        "declared": True,
        "briefing": {"held": True, "date": "2026-08-31", "presenter": "cost_lead"},
        "responsibilities": [
            {"department": "technical", "assignee": "Zhang", "action": "complete hidden-work evidence", "due_date": "2026-09-05", "signed": True, "sign_time": "2026-08-31T10:10:00+08:00"},
            {"department": "production", "assignee": "Li", "action": "close measurement gap", "due_date": "2026-09-03", "signed": True, "sign_time": "2026-08-31T10:12:00+08:00"},
        ],
    }
    result = _run(payload)
    assert result.outcome == "success"
    assert result.data["state"] == "monthly_control_closed"
    assert result.data["declaration_completed"] is True
    assert result.data["briefing_completed"] is True
    assert result.data["all_responsibilities_signed"] is True
    assert result.data["next_month_follow_up_required"] is True
    assert result.data["automatic_approval"] is False


def test_monthly_commercial_control_is_not_visible_to_technical_role():
    with SessionLocal() as db:
        envelope, _ = gateway.execute(db, "p06.monthly_control_gate", "P-MONTHLY-ACL", "tech", "technical", {"month": "2026-08", "snapshot": _snapshot()})
    assert envelope.status == "DENIED"
