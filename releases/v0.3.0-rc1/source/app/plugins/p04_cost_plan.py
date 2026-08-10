from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


_REQUIRED_COST_KEYS = (
    "labor",
    "material",
    "equipment",
    "organization_measures",
    "technical_measures",
    "management_fee",
    "statutory_fee",
    "tax",
)


@register(CapabilityManifest(id="p04.cost_plan", version="1.0.0", risk="high", commercial=True))
def cost_plan(db, project_id, actor, role, payload):
    costs = payload.get("costs") or {}
    missing = [key for key in _REQUIRED_COST_KEYS if costs.get(key) is None]
    revenue = payload.get("forecast_revenue")
    if revenue is None:
        missing.append("forecast_revenue")
    if missing:
        return CapabilityResult("needs_information", {"required": missing})

    normalized = {}
    for key in _REQUIRED_COST_KEYS:
        try:
            value = float(costs[key])
        except (TypeError, ValueError):
            return CapabilityResult("needs_information", {"required_numeric": [key]})
        if value < 0:
            return CapabilityResult("failed", {"reason": "negative_cost_not_allowed", "field": key})
        normalized[key] = value

    try:
        forecast_revenue = float(revenue)
    except (TypeError, ValueError):
        return CapabilityResult("needs_information", {"required_numeric": ["forecast_revenue"]})
    if forecast_revenue < 0:
        return CapabilityResult("failed", {"reason": "negative_revenue_not_allowed"})

    direct_cost = normalized["labor"] + normalized["material"] + normalized["equipment"]
    measures_cost = normalized["organization_measures"] + normalized["technical_measures"]
    indirect_cost = normalized["management_fee"] + normalized["statutory_fee"] + normalized["tax"]
    total_cost = direct_cost + measures_cost + indirect_cost
    forecast_profit = forecast_revenue - total_cost
    forecast_margin = None if forecast_revenue == 0 else forecast_profit / forecast_revenue

    return CapabilityResult("success", {
        "classification": "commercial_confidential",
        "state": "forecast",
        "costs": normalized,
        "direct_cost": direct_cost,
        "measures_cost": measures_cost,
        "indirect_cost": indirect_cost,
        "forecast_revenue": forecast_revenue,
        "forecast_cost": total_cost,
        "forecast_profit": forecast_profit,
        "forecast_margin": forecast_margin,
    })
