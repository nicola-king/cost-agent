from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


_REQUIRED_GATES = (
    "award_boq",
    "drawing_baseline",
    "baseline0",
    "boq_classification",
    "evidence_closure",
    "material_batch_final",
    "major_change_dossiers",
    "monthly_control",
)


@register(CapabilityManifest(id="p07.settlement_pre_audit_gate", version="1.0.0", risk="high", commercial=True))
def settlement_pre_audit_gate(db, project_id, actor, role, payload):
    gates = payload.get("gates") or {}
    missing = [name for name in _REQUIRED_GATES if name not in gates]
    if missing:
        return CapabilityResult("needs_information", {"required": [f"gates.{x}" for x in missing]})

    blockers = []
    for name in _REQUIRED_GATES:
        row = gates.get(name) or {}
        state = str(row.get("state") or "").strip().lower()
        if state not in {"closed", "success", "passed", "verified"}:
            blockers.append({"gate": name, "state": state or "unknown", "reason": row.get("reason")})

    settlement_amount = payload.get("settlement_amount")
    if settlement_amount is None:
        return CapabilityResult("needs_information", {"required": ["settlement_amount"], "blockers": blockers})

    amount = float(settlement_amount)
    if amount < 0:
        return CapabilityResult("failed", {"reason": "negative_settlement_amount_not_allowed"})

    if blockers:
        return CapabilityResult("conflict", {
            "state": "pre_audit_blocked",
            "settlement_amount": amount,
            "blocker_count": len(blockers),
            "blockers": blockers,
            "formal_settlement_allowed": False,
            "automatic_approval": False,
        })

    return CapabilityResult("success", {
        "state": "pre_audit_passed",
        "settlement_amount": amount,
        "blocker_count": 0,
        "blockers": [],
        "formal_settlement_allowed": True,
        "human_final_review_required": True,
        "automatic_approval": False,
    })
