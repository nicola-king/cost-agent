from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


@register(CapabilityManifest(id="p07.major_change_dossier_gate", version="1.0.0", risk="high", commercial=True))
def major_change_dossier_gate(db, project_id, actor, role, payload):
    required = ["change_id", "amount", "contract_amount"]
    missing = [key for key in required if payload.get(key) is None]
    if missing:
        return CapabilityResult("needs_information", {"required": missing})

    try:
        amount = float(payload["amount"])
        contract_amount = float(payload["contract_amount"])
        fixed_threshold = float(payload.get("fixed_threshold", 0) or 0)
        ratio_threshold = float(payload.get("ratio_threshold", 1) or 1)
        closure = float(payload.get("evidence_closure_ratio", 0) or 0)
    except (TypeError, ValueError):
        return CapabilityResult("needs_information", {"reason": "numeric_field_invalid"})

    if amount < 0 or contract_amount < 0 or fixed_threshold < 0 or ratio_threshold < 0:
        return CapabilityResult("failed", {"reason": "negative_value_not_allowed"})

    contract_ratio = amount / contract_amount if contract_amount else 0.0
    manual_major = bool(payload.get("manual_major", False))
    fixed_hit = fixed_threshold > 0 and amount >= fixed_threshold
    ratio_hit = contract_amount > 0 and contract_ratio >= ratio_threshold
    major = fixed_hit or ratio_hit or manual_major

    trigger_reasons = []
    if fixed_hit:
        trigger_reasons.append("fixed_threshold")
    if ratio_hit:
        trigger_reasons.append("contract_ratio_threshold")
    if manual_major:
        trigger_reasons.append("manual_major")

    if not major:
        return CapabilityResult("success", {
            "change_id": str(payload["change_id"]),
            "major": False,
            "workflow_state": "ordinary_change_workflow",
            "independent_dossier_required": False,
            "amount": amount,
            "contract_ratio": contract_ratio,
            "thresholds": {"fixed": fixed_threshold, "ratio": ratio_threshold},
        })

    dossier_id = str(payload.get("dossier_id") or "").strip()
    if not dossier_id:
        return CapabilityResult("needs_information", {
            "change_id": str(payload["change_id"]),
            "major": True,
            "workflow_state": "dossier_required",
            "independent_dossier_required": True,
            "required": ["dossier_id"],
            "trigger_reasons": trigger_reasons,
            "amount": amount,
            "contract_ratio": contract_ratio,
            "thresholds": {"fixed": fixed_threshold, "ratio": ratio_threshold},
        })

    if closure < 1.0:
        return CapabilityResult("partial", {
            "change_id": str(payload["change_id"]),
            "major": True,
            "dossier_id": dossier_id,
            "workflow_state": "independent_evidence_pending",
            "independent_dossier_required": True,
            "independent_evidence_required": True,
            "evidence_closure_ratio": max(0.0, min(closure, 1.0)),
            "trigger_reasons": trigger_reasons,
        })

    if not bool(payload.get("human_approved", False)):
        return CapabilityResult("partial", {
            "change_id": str(payload["change_id"]),
            "major": True,
            "dossier_id": dossier_id,
            "workflow_state": "independent_approval_pending",
            "independent_dossier_required": True,
            "evidence_closure_ratio": 1.0,
            "human_approval_required": True,
            "automatic_verification": False,
            "trigger_reasons": trigger_reasons,
        })

    settlement_submitted = bool(payload.get("settlement_submitted", False))
    return CapabilityResult("success", {
        "change_id": str(payload["change_id"]),
        "major": True,
        "dossier_id": dossier_id,
        "workflow_state": "settlement_review" if settlement_submitted else "independent_settlement_ready",
        "independent_dossier_required": True,
        "independent_evidence_required": True,
        "evidence_closure_ratio": 1.0,
        "human_approved": True,
        "automatic_verification": False,
        "settlement_submitted": settlement_submitted,
        "trigger_reasons": trigger_reasons,
        "amount": amount,
        "contract_ratio": contract_ratio,
        "thresholds": {"fixed": fixed_threshold, "ratio": ratio_threshold},
    })
