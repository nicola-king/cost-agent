from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult

@register(CapabilityManifest(id="p04.forecast_margin", version="1.0.0", risk="high", commercial=True))
def forecast_margin(db, project_id, actor, role, payload):
    q = payload.get("quantity")
    revenue_price = payload.get("revenue_unit_price")
    resource_cost = payload.get("resource_cost")
    other_cost = float(payload.get("other_cost", 0))
    if q is None or revenue_price is None or resource_cost is None:
        return CapabilityResult("needs_information", {"required": ["quantity", "revenue_unit_price", "resource_cost"]})
    revenue = float(q) * float(revenue_price)
    cost = float(resource_cost) + other_cost
    profit = revenue - cost
    margin = None if revenue == 0 else profit / revenue
    return CapabilityResult("success", {"classification": "commercial_confidential", "forecast_revenue": revenue, "forecast_cost": cost, "forecast_profit": profit, "forecast_margin": margin, "state": "forecast"})
