from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


_RESOURCE_TYPES = ("labor", "material", "equipment")


@register(CapabilityManifest(id="p03.resource_control_line", version="1.0.0", risk="medium"))
def resource_control_line(db, project_id, actor, role, payload):
    """Build labor/material/equipment control lines from drawing demand and quota consumption.

    Frozen business rule: for each resource, the lower of construction-drawing demand
    and quota consumption is the baseline control line. Subsequent approved construction
    changes may be represented as a delta; the original baseline remains visible.
    """
    resources = payload.get("resources") or {}
    missing: list[str] = []
    normalized: dict[str, dict] = {}

    for resource_type in _RESOURCE_TYPES:
        item = resources.get(resource_type) or {}
        drawing_qty = item.get("drawing_quantity")
        quota_qty = item.get("quota_quantity")
        if drawing_qty is None:
            missing.append(f"resources.{resource_type}.drawing_quantity")
        if quota_qty is None:
            missing.append(f"resources.{resource_type}.quota_quantity")
        if drawing_qty is None or quota_qty is None:
            continue
        try:
            drawing = float(drawing_qty)
            quota = float(quota_qty)
            delta = float(item.get("approved_change_delta", 0) or 0)
        except (TypeError, ValueError):
            return CapabilityResult("needs_information", {"reason": "quantity_must_be_numeric", "resource_type": resource_type})
        if drawing < 0 or quota < 0:
            return CapabilityResult("failed", {"reason": "negative_quantity_not_allowed", "resource_type": resource_type})

        baseline = min(drawing, quota)
        current_control = baseline + delta
        if current_control < 0:
            return CapabilityResult("failed", {"reason": "change_delta_below_zero_control_line", "resource_type": resource_type})

        normalized[resource_type] = {
            "unit": item.get("unit"),
            "drawing_quantity": drawing,
            "quota_quantity": quota,
            "baseline_control_quantity": baseline,
            "baseline_source": "drawing" if drawing < quota else "quota" if quota < drawing else "equal",
            "approved_change_delta": delta,
            "current_control_quantity": current_control,
            "state": "baseline" if delta == 0 else "adjusted",
        }

    if missing:
        return CapabilityResult("needs_information", {"required": missing, "partial": normalized})

    return CapabilityResult("success", {
        "rule": "min(drawing_quantity, quota_quantity)",
        "baseline_is_immutable": True,
        "resources": normalized,
    })
