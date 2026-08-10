from app.core.db import SessionLocal
from app.plugins.base import gateway


def test_same_boq_uses_award_price_and_waits_for_evidence():
    payload = {
        "boq_classification": "same_boq",
        "proposed_quantity": 100,
        "award_unit_price": 80,
        "forecast_cost": 6500,
        "evidence_closure_ratio": 0.75,
    }
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p05.change_workflow_gate", "P-CHG-1", "cost", "cost_lead", payload)
    assert result.outcome == "success"
    assert result.data["price_basis"] == "award_unit_price"
    assert result.data["forecast_revenue"] == 8000
    assert result.data["forecast_profit"] == 1500
    assert result.data["workflow_state"] == "evidence_open"
    assert result.data["settlement_ready"] is False


def test_similar_boq_requires_candidate_price_and_human_approval():
    payload = {
        "boq_classification": "similar_boq",
        "proposed_quantity": 50,
        "candidate_unit_price": 120,
        "forecast_cost": 5000,
        "evidence_closure_ratio": 1,
    }
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p05.change_workflow_gate", "P-CHG-2", "cost", "cost_lead", payload)
    assert result.data["price_state"] == "candidate_requires_human_approval"
    assert result.data["workflow_state"] == "awaiting_human_approval"
    assert result.data["automatic_verification"] is False


def test_missing_boq_requires_new_price_candidate():
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p05.change_workflow_gate", "P-CHG-3", "cost", "cost_lead", {
            "boq_classification": "no_boq",
            "proposed_quantity": 20,
        })
    assert result.outcome == "needs_information"
    assert result.data["required"] == ["new_unit_price_candidate"]
    assert result.data["next_step"] == "price_candidate"


def test_approved_closed_change_can_enter_settlement():
    payload = {
        "boq_classification": "no_boq",
        "proposed_quantity": 20,
        "new_unit_price_candidate": 300,
        "forecast_cost": 4200,
        "evidence_closure_ratio": 1,
        "human_approved": True,
    }
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p05.change_workflow_gate", "P-CHG-4", "cost", "project_manager", payload)
    assert result.data["workflow_state"] == "approved_ready_for_settlement"
    assert result.data["settlement_ready"] is True
    assert result.data["next_step"] == "settlement_submission"


def test_submission_moves_to_settlement_review():
    payload = {
        "boq_classification": "same_boq",
        "proposed_quantity": 10,
        "award_unit_price": 100,
        "forecast_cost": 700,
        "evidence_closure_ratio": 1,
        "human_approved": True,
        "settlement_submitted": True,
    }
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p05.change_workflow_gate", "P-CHG-5", "cost", "cost_lead", payload)
    assert result.data["workflow_state"] == "submitted_for_settlement"
    assert result.data["next_step"] == "settlement_review"


def test_noncommercial_role_cannot_access_change_profit():
    payload = {
        "boq_classification": "same_boq",
        "proposed_quantity": 10,
        "award_unit_price": 100,
        "forecast_cost": 700,
        "evidence_closure_ratio": 1,
    }
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p05.change_workflow_gate", "P-CHG-6", "tech", "technical", payload)
    assert result.outcome == "failed"
    assert result.data["reason"] == "commercial_confidential"
