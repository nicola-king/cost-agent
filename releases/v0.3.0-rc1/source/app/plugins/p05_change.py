from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult

@register(CapabilityManifest(id="p05.pre_change_gate", version="1.0.0", risk="high", commercial=True))
def pre_change_gate(db, project_id, actor, role, payload):
    required = ["baseline_quantity", "proposed_quantity", "boq_classification", "forecast_revenue", "forecast_cost"]
    missing = [x for x in required if payload.get(x) is None]
    if missing:
        return CapabilityResult("needs_information", {"required": missing})
    dq = float(payload["proposed_quantity"]) - float(payload["baseline_quantity"])
    profit = float(payload["forecast_revenue"]) - float(payload["forecast_cost"])
    status = "warning" if profit < 0 else "review"
    return CapabilityResult("success", {"quantity_delta": dq, "forecast_profit": profit, "decision_state": status, "note": "recommendation_only_human_approval_required"})
