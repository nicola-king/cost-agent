from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


_RESOURCE_TYPES = ("labor", "material", "equipment")


@register(CapabilityManifest(id="p04.market_cost_forecast", version="1.0.0", risk="high", commercial=True))
def market_cost_forecast(db, project_id, actor, role, payload):
    """Forecast cost and margin from verified market-price context.

    Every resource price must include source, region and month. Unverified or incomplete
    market context is rejected instead of silently falling back to a default price.
    """
    resources = payload.get("resources") or {}
    missing: list[str] = []
    result_rows: dict[str, dict] = {}

    for resource_type in _RESOURCE_TYPES:
        item = resources.get(resource_type) or {}
        quantity = item.get("control_quantity")
        unit_price = item.get("market_unit_price")
        source = str(item.get("source") or "").strip()
        region = str(item.get("region") or "").strip()
        month = str(item.get("month") or "").strip()

        if quantity is None:
            missing.append(f"resources.{resource_type}.control_quantity")
        if unit_price is None:
            missing.append(f"resources.{resource_type}.market_unit_price")
        if not source:
            missing.append(f"resources.{resource_type}.source")
        if not region:
            missing.append(f"resources.{resource_type}.region")
        if not month:
            missing.append(f"resources.{resource_type}.month")
        if quantity is None or unit_price is None or not source or not region or not month:
            continue

        try:
            q = float(quantity)
            p = float(unit_price)
        except (TypeError, ValueError):
            return CapabilityResult("needs_information", {"reason": "quantity_and_price_must_be_numeric", "resource_type": resource_type})
        if q < 0 or p < 0:
            return CapabilityResult("failed", {"reason": "negative_quantity_or_price_not_allowed", "resource_type": resource_type})

        amount = q * p
        result_rows[resource_type] = {
            "control_quantity": q,
            "market_unit_price": p,
            "market_amount": amount,
            "unit": item.get("unit"),
            "source": source,
            "region": region,
            "month": month,
            "verified_source_context": True,
        }

    if missing:
        return CapabilityResult("needs_information", {"required": missing, "partial": result_rows})

    other_costs = payload.get("other_costs") or {}
    normalized_other = {}
    for key in ("organization_measures", "technical_measures", "management_fee", "statutory_fee", "tax"):
        try:
            value = float(other_costs.get(key, 0) or 0)
        except (TypeError, ValueError):
            return CapabilityResult("needs_information", {"required_numeric": [f"other_costs.{key}"]})
        if value < 0:
            return CapabilityResult("failed", {"reason": "negative_cost_not_allowed", "field": key})
        normalized_other[key] = value

    try:
        forecast_revenue = float(payload.get("forecast_revenue"))
    except (TypeError, ValueError):
        return CapabilityResult("needs_information", {"required": ["forecast_revenue"]})
    if forecast_revenue < 0:
        return CapabilityResult("failed", {"reason": "negative_revenue_not_allowed"})

    resource_cost = sum(row["market_amount"] for row in result_rows.values())
    other_cost = sum(normalized_other.values())
    forecast_cost = resource_cost + other_cost
    forecast_profit = forecast_revenue - forecast_cost
    forecast_margin = None if forecast_revenue == 0 else forecast_profit / forecast_revenue

    return CapabilityResult("success", {
        "classification": "commercial_confidential",
        "state": "forecast",
        "price_basis": "verified_market_reference",
        "resources": result_rows,
        "other_costs": normalized_other,
        "resource_cost": resource_cost,
        "other_cost": other_cost,
        "forecast_revenue": forecast_revenue,
        "forecast_cost": forecast_cost,
        "forecast_profit": forecast_profit,
        "forecast_margin": forecast_margin,
    })
