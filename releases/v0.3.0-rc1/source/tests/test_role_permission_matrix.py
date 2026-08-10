from app.core.db import SessionLocal
from app.plugins.base import gateway


def _run(capability, role, payload=None, project="P-ACL"):
    with SessionLocal() as db:
        return gateway.execute(db, capability, project, role, role, payload or {})[1]


def test_commercial_capabilities_are_limited_to_project_manager_and_cost_lead():
    restricted_roles = ["cost_engineer", "technical", "production", "measurement", "laboratory", "records", "materials", "equipment"]
    commercial_cases = [
        ("p04.cost_plan", {"forecast_revenue": 1, "costs": {}}),
        ("p04.market_cost_forecast", {}),
        ("p06.monthly_control_gate", {"month": "2026-08", "snapshot": {}}),
        ("p07.settlement_pre_audit_gate", {"settlement_amount": 1, "gates": {}}),
    ]
    for role in restricted_roles:
        for capability, payload in commercial_cases:
            result = _run(capability, role, payload, project=f"P-ACL-{role}-{capability}")
            assert result.outcome == "failed"
            assert result.data["reason"] == "commercial_confidential"


def test_project_manager_and_cost_lead_can_enter_commercial_capabilities():
    for role in ["project_manager", "cost_lead"]:
        result = _run("p04.cost_plan", role, {
            "forecast_revenue": 100,
            "costs": {
                "labor": 10, "material": 10, "equipment": 10,
                "organization_measures": 5, "technical_measures": 5,
                "management_fee": 5, "statutory_fee": 5, "tax": 5,
            },
        }, project=f"P-ACL-COM-{role}")
        assert result.data.get("reason") != "commercial_confidential"


def test_operational_departments_can_submit_evidence_as_candidate_only():
    roles = ["technical", "production", "measurement", "laboratory", "records", "materials", "equipment", "cost_engineer"]
    for role in roles:
        result = _run("p06.evidence_submit_gate", role, {
            "task_id": "TASK-1",
            "evidence_type": "photo",
        }, project=f"P-ACL-SUBMIT-{role}")
        assert result.outcome == "success"
        assert result.data["verification_state"] == "candidate"
        assert result.data["automatic_verification"] is False


def test_operational_departments_cannot_verify_evidence():
    roles = ["technical", "production", "measurement", "laboratory", "records", "materials", "equipment", "cost_engineer"]
    for role in roles:
        result = _run("p06.evidence_verify_gate", role, {
            "evidence_id": "E-1",
            "decision": "verified",
        }, project=f"P-ACL-VERIFY-{role}")
        assert result.outcome == "failed"
        assert result.data["reason"] == "role_not_allowed_to_verify_evidence"


def test_only_project_manager_and_cost_lead_can_verify_evidence():
    for role in ["project_manager", "cost_lead"]:
        result = _run("p06.evidence_verify_gate", role, {
            "evidence_id": "E-1",
            "decision": "verified",
        }, project=f"P-ACL-VERIFY-OK-{role}")
        assert result.outcome == "success"
        assert result.data["human_review_required"] is True
        assert result.data["automatic_verification"] is False
