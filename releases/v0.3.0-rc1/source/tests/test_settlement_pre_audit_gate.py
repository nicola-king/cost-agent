from app.core.db import SessionLocal
from app.plugins.base import gateway


def _closed_gates():
    return {
        "award_boq": {"state": "closed"},
        "drawing_baseline": {"state": "closed"},
        "baseline0": {"state": "closed"},
        "boq_classification": {"state": "closed"},
        "evidence_closure": {"state": "closed"},
        "material_batch_final": {"state": "closed"},
        "major_change_dossiers": {"state": "closed"},
        "monthly_control": {"state": "closed"},
    }


def _run(payload, role="cost_lead", project="P-PREAUDIT"):
    with SessionLocal() as db:
        return gateway.execute(db, "p07.settlement_pre_audit_gate", project, "cost", role, payload)[1]


def test_pre_audit_requires_all_gates():
    gates = _closed_gates()
    del gates["evidence_closure"]
    result = _run({"gates": gates, "settlement_amount": 1000000})
    assert result.outcome == "needs_information"
    assert "gates.evidence_closure" in result.data["required"]


def test_pre_audit_blocks_any_open_critical_gate():
    gates = _closed_gates()
    gates["material_batch_final"] = {"state": "conflict", "reason": "coverage_above_105_percent"}
    result = _run({"gates": gates, "settlement_amount": 1000000})
    assert result.outcome == "conflict"
    assert result.data["formal_settlement_allowed"] is False
    assert result.data["blocker_count"] == 1
    assert result.data["blockers"][0]["gate"] == "material_batch_final"


def test_pre_audit_blocks_unclosed_major_change_dossier():
    gates = _closed_gates()
    gates["major_change_dossiers"] = {"state": "partial", "reason": "unsigned_dossier"}
    result = _run({"gates": gates, "settlement_amount": 1000000})
    assert result.outcome == "conflict"
    assert result.data["blockers"][0]["gate"] == "major_change_dossiers"


def test_pre_audit_passes_only_when_all_gates_closed():
    result = _run({"gates": _closed_gates(), "settlement_amount": 12800000})
    assert result.outcome == "success"
    assert result.data["state"] == "pre_audit_passed"
    assert result.data["formal_settlement_allowed"] is True
    assert result.data["human_final_review_required"] is True
    assert result.data["automatic_approval"] is False


def test_pre_audit_commercial_data_denied_to_technical_role():
    result = _run({"gates": _closed_gates(), "settlement_amount": 12800000}, role="technical", project="P-PREAUDIT-ACL")
    assert result.outcome == "failed"
    assert result.data["reason"] == "commercial_confidential"
