from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


_ALLOWED_CLASSIFICATIONS = {"same_boq", "similar_boq", "no_boq"}


@register(CapabilityManifest(id="p05.change_workflow_gate", version="1.0.0", risk="high", commercial=True))
def change_workflow_gate(db, project_id, actor, role, payload):
    classification = payload.get("boq_classification")
    if classification not in _ALLOWED_CLASSIFICATIONS:
        return CapabilityResult("needs_information", {"required": ["boq_classification"], "allowed": sorted(_ALLOWED_CLASSIFICATIONS)})

    quantity = payload.get("proposed_quantity")
    if quantity is None:
        return CapabilityResult("needs_information", {"required": ["proposed_quantity"]})
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return CapabilityResult("needs_information", {"required_numeric": ["proposed_quantity"]})
    if quantity < 0:
        return CapabilityResult("failed", {"reason": "negative_quantity_not_allowed"})

    if classification == "same_boq":
        price = payload.get("award_unit_price")
        price_basis = "award_unit_price"
        price_state = "baseline_applicable"
    elif classification == "similar_boq":
        price = payload.get("candidate_unit_price")
        price_basis = "candidate_unit_price"
        price_state = "candidate_requires_human_approval"
    else:
        price = payload.get("new_unit_price_candidate")
        price_basis = "new_unit_price_candidate"
        price_state = "new_price_candidate_requires_human_approval"

    if price is None:
        return CapabilityResult("needs_information", {
            "required": [price_basis],
            "boq_classification": classification,
            "next_step": "price_candidate",
        })
    try:
        unit_price = float(price)
    except (TypeError, ValueError):
        return CapabilityResult("needs_information", {"required_numeric": [price_basis]})
    if unit_price < 0:
        return CapabilityResult("failed", {"reason": "negative_price_not_allowed", "field": price_basis})

    forecast_revenue = quantity * unit_price
    forecast_cost = payload.get("forecast_cost")
    forecast_profit = None
    if forecast_cost is not None:
        try:
            forecast_cost = float(forecast_cost)
        except (TypeError, ValueError):
            return CapabilityResult("needs_information", {"required_numeric": ["forecast_cost"]})
        forecast_profit = forecast_revenue - forecast_cost

    evidence_ratio = payload.get("evidence_closure_ratio")
    if evidence_ratio is None:
        return CapabilityResult("needs_information", {
            "required": ["evidence_closure_ratio"],
            "next_step": "evidence_closure",
            "forecast_revenue": forecast_revenue,
            "forecast_profit": forecast_profit,
        })
    try:
        evidence_ratio = float(evidence_ratio)
    except (TypeError, ValueError):
        return CapabilityResult("needs_information", {"required_numeric": ["evidence_closure_ratio"]})
    if not 0 <= evidence_ratio <= 1:
        return CapabilityResult("failed", {"reason": "invalid_evidence_closure_ratio"})

    human_approved = bool(payload.get("human_approved", False))
    settlement_submitted = bool(payload.get("settlement_submitted", False))

    if evidence_ratio < 1:
        workflow_state = "evidence_open"
        next_step = "complete_evidence"
        settlement_ready = False
    elif not human_approved:
        workflow_state = "awaiting_human_approval"
        next_step = "human_approval"
        settlement_ready = False
    elif not settlement_submitted:
        workflow_state = "approved_ready_for_settlement"
        next_step = "settlement_submission"
        settlement_ready = True
    else:
        workflow_state = "submitted_for_settlement"
        next_step = "settlement_review"
        settlement_ready = True

    return CapabilityResult("success", {
        "classification": "commercial_confidential",
        "boq_classification": classification,
        "quantity": quantity,
        "unit_price": unit_price,
        "price_basis": price_basis,
        "price_state": price_state,
        "forecast_revenue": forecast_revenue,
        "forecast_cost": forecast_cost,
        "forecast_profit": forecast_profit,
        "evidence_closure_ratio": evidence_ratio,
        "human_approved": human_approved,
        "settlement_ready": settlement_ready,
        "settlement_submitted": settlement_submitted,
        "workflow_state": workflow_state,
        "next_step": next_step,
        "automatic_verification": False,
    })
