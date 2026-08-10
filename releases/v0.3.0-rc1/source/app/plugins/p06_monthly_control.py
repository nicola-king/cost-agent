from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


@register(CapabilityManifest(id="p06.monthly_control_gate", version="1.0.0", risk="high", commercial=True))
def monthly_control_gate(db, project_id, actor, role, payload):
    """Monthly commercial snapshot -> declaration -> briefing -> signed responsibility closure.

    This is a calculation/workflow gate only. It does not create a second source of truth.
    All figures must come from backend capabilities or verified project sources upstream.
    """
    month = (payload.get("month") or "").strip()
    if not month:
        return CapabilityResult("needs_information", {"required": ["month"]})

    snapshot = payload.get("snapshot") or {}
    required_snapshot = [
        "forecast_revenue",
        "forecast_cost",
        "forecast_profit",
        "change_amount",
        "risk_amount",
        "evidence_gap_count",
        "material_batch_conflict_count",
        "open_responsibility_count",
    ]
    missing_snapshot = [key for key in required_snapshot if snapshot.get(key) is None]
    if missing_snapshot:
        return CapabilityResult("needs_information", {
            "state": "snapshot_incomplete",
            "required": [f"snapshot.{key}" for key in missing_snapshot],
        })

    declared = bool(payload.get("declared", False))
    if not declared:
        return CapabilityResult("partial", {
            "month": month,
            "state": "snapshot_ready_for_declaration",
            "snapshot": snapshot,
            "next_required": ["declared=true"],
        })

    briefing = payload.get("briefing") or {}
    if not briefing.get("held"):
        return CapabilityResult("partial", {
            "month": month,
            "state": "declared_waiting_for_briefing",
            "snapshot": snapshot,
            "next_required": ["briefing.held=true", "briefing.date", "briefing.presenter"],
        })
    missing_briefing = [key for key in ("date", "presenter") if not briefing.get(key)]
    if missing_briefing:
        return CapabilityResult("needs_information", {
            "state": "briefing_incomplete",
            "required": [f"briefing.{key}" for key in missing_briefing],
        })

    responsibilities = payload.get("responsibilities") or []
    if not responsibilities:
        return CapabilityResult("needs_information", {
            "state": "responsibility_register_required",
            "required": ["responsibilities"],
        })

    rows = []
    unsigned = 0
    for idx, item in enumerate(responsibilities, start=1):
        required = ["department", "assignee", "action", "due_date"]
        missing = [key for key in required if not item.get(key)]
        if missing:
            return CapabilityResult("needs_information", {
                "state": "responsibility_incomplete",
                "responsibility_index": idx - 1,
                "required": [f"responsibilities[{idx - 1}].{key}" for key in missing],
            })
        signed = bool(item.get("signed", False))
        if not signed:
            unsigned += 1
        rows.append({
            "department": item["department"],
            "assignee": item["assignee"],
            "action": item["action"],
            "due_date": item["due_date"],
            "signed": signed,
            "sign_time": item.get("sign_time"),
        })

    if unsigned:
        return CapabilityResult("partial", {
            "month": month,
            "state": "briefed_waiting_for_signatures",
            "snapshot": snapshot,
            "briefing": briefing,
            "responsibilities": rows,
            "unsigned_count": unsigned,
        })

    return CapabilityResult("success", {
        "month": month,
        "state": "monthly_control_closed",
        "snapshot": snapshot,
        "briefing": briefing,
        "responsibilities": rows,
        "declaration_completed": True,
        "briefing_completed": True,
        "all_responsibilities_signed": True,
        "next_month_follow_up_required": True,
        "automatic_approval": False,
    })
