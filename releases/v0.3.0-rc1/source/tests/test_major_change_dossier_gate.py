from app.core.db import SessionLocal
from app.plugins.base import gateway


def _execute(project, payload):
    with SessionLocal() as db:
        return gateway.execute(db, "p07.major_change_dossier_gate", project, "cost", "cost_lead", payload)[1]


def test_ordinary_change_does_not_require_independent_dossier():
    result = _execute("P-MAJOR-1", {
        "change_id": "CE-001",
        "amount": 100000,
        "contract_amount": 10000000,
        "fixed_threshold": 500000,
        "ratio_threshold": 0.10,
    })
    assert result.outcome == "success"
    assert result.data["major"] is False
    assert result.data["independent_dossier_required"] is False


def test_major_change_requires_independent_dossier():
    result = _execute("P-MAJOR-2", {
        "change_id": "CE-002",
        "amount": 800000,
        "contract_amount": 10000000,
        "fixed_threshold": 500000,
        "ratio_threshold": 0.10,
    })
    assert result.outcome == "needs_information"
    assert result.data["major"] is True
    assert result.data["workflow_state"] == "dossier_required"
    assert "dossier_id" in result.data["required"]


def test_major_change_independent_evidence_and_approval_are_mandatory():
    pending_evidence = _execute("P-MAJOR-3", {
        "change_id": "CE-003",
        "amount": 800000,
        "contract_amount": 10000000,
        "fixed_threshold": 500000,
        "ratio_threshold": 0.10,
        "dossier_id": "DOS-CE-003",
        "evidence_closure_ratio": 0.75,
    })
    assert pending_evidence.outcome == "partial"
    assert pending_evidence.data["workflow_state"] == "independent_evidence_pending"

    pending_approval = _execute("P-MAJOR-4", {
        "change_id": "CE-004",
        "amount": 1200000,
        "contract_amount": 10000000,
        "fixed_threshold": 500000,
        "ratio_threshold": 0.10,
        "dossier_id": "DOS-CE-004",
        "evidence_closure_ratio": 1.0,
        "human_approved": False,
    })
    assert pending_approval.outcome == "partial"
    assert pending_approval.data["workflow_state"] == "independent_approval_pending"
    assert pending_approval.data["automatic_verification"] is False


def test_major_change_moves_to_independent_settlement_tracking():
    ready = _execute("P-MAJOR-5", {
        "change_id": "CE-005",
        "amount": 1500000,
        "contract_amount": 10000000,
        "fixed_threshold": 500000,
        "ratio_threshold": 0.10,
        "dossier_id": "DOS-CE-005",
        "evidence_closure_ratio": 1.0,
        "human_approved": True,
        "settlement_submitted": False,
    })
    assert ready.outcome == "success"
    assert ready.data["workflow_state"] == "independent_settlement_ready"

    review = _execute("P-MAJOR-6", {
        "change_id": "CE-006",
        "amount": 1500000,
        "contract_amount": 10000000,
        "fixed_threshold": 500000,
        "ratio_threshold": 0.10,
        "dossier_id": "DOS-CE-006",
        "evidence_closure_ratio": 1.0,
        "human_approved": True,
        "settlement_submitted": True,
    })
    assert review.outcome == "success"
    assert review.data["workflow_state"] == "settlement_review"


def test_manual_major_flag_also_forces_independent_dossier():
    result = _execute("P-MAJOR-7", {
        "change_id": "CE-007",
        "amount": 1000,
        "contract_amount": 10000000,
        "fixed_threshold": 500000,
        "ratio_threshold": 0.10,
        "manual_major": True,
    })
    assert result.outcome == "needs_information"
    assert result.data["major"] is True
    assert "manual_major" in result.data["trigger_reasons"]
