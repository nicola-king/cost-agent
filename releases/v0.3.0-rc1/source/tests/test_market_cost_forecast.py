from app.core.db import SessionLocal
from app.plugins.base import gateway


def _payload():
    return {
        "forecast_revenue": 100000,
        "resources": {
            "labor": {"unit":"工日","control_quantity":100,"market_unit_price":300,"source":"market-survey-a","region":"Chongqing","month":"2026-08"},
            "material": {"unit":"t","control_quantity":50,"market_unit_price":600,"source":"market-survey-b","region":"Chongqing","month":"2026-08"},
            "equipment": {"unit":"台班","control_quantity":10,"market_unit_price":1000,"source":"market-survey-c","region":"Chongqing","month":"2026-08"},
        },
        "other_costs": {
            "organization_measures": 5000,
            "technical_measures": 3000,
            "management_fee": 4000,
            "statutory_fee": 2000,
            "tax": 1000,
        },
    }


def test_verified_market_context_builds_forecast_for_cost_lead():
    with SessionLocal() as db:
        _, result = gateway.execute(db,"p04.market_cost_forecast","P-MKT-1","cost","cost_lead",_payload())
    assert result.outcome == "success"
    assert result.data["price_basis"] == "verified_market_reference"
    assert result.data["resource_cost"] == 70000
    assert result.data["other_cost"] == 15000
    assert result.data["forecast_cost"] == 85000
    assert result.data["forecast_profit"] == 15000
    assert round(result.data["forecast_margin"], 4) == 0.15


def test_missing_source_region_or_month_is_not_accepted_as_market_basis():
    payload = _payload()
    payload["resources"]["material"]["source"] = ""
    with SessionLocal() as db:
        _, result = gateway.execute(db,"p04.market_cost_forecast","P-MKT-2","cost","cost_lead",payload)
    assert result.outcome == "needs_information"
    assert "resources.material.source" in result.data["required"]


def test_non_commercial_role_cannot_read_profit_forecast():
    with SessionLocal() as db:
        _, result = gateway.execute(db,"p04.market_cost_forecast","P-MKT-3","tech","technical",_payload())
    assert result.outcome == "failed"
    assert result.data == {"reason":"commercial_confidential"}


def test_project_manager_can_read_market_forecast():
    with SessionLocal() as db:
        _, result = gateway.execute(db,"p04.market_cost_forecast","P-MKT-4","pm","project_manager",_payload())
    assert result.outcome == "success"
    assert result.data["classification"] == "commercial_confidential"
