from app.core.db import Base, engine, SessionLocal
from app.core.models import Project
from app.services.capability import gateway
from app import plugins


def setup_module():
    Base.metadata.create_all(bind=engine)


def _seed(project_id):
    with SessionLocal() as db:
        db.merge(Project(id=project_id, name="cost-plan"))
        db.commit()


def _payload():
    return {
        "forecast_revenue": 1_500_000,
        "costs": {
            "labor": 180_000,
            "material": 650_000,
            "equipment": 120_000,
            "organization_measures": 70_000,
            "technical_measures": 50_000,
            "management_fee": 90_000,
            "statutory_fee": 30_000,
            "tax": 100_000,
        },
    }


def test_cost_plan_complete_breakdown_and_margin():
    project_id = "PRJ-COST-PLAN-1"
    _seed(project_id)
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p04.cost_plan", project_id, "pm", "project_manager", _payload())
        assert result.outcome == "success"
        assert result.data["direct_cost"] == 950_000
        assert result.data["measures_cost"] == 120_000
        assert result.data["indirect_cost"] == 220_000
        assert result.data["forecast_cost"] == 1_290_000
        assert result.data["forecast_profit"] == 210_000
        assert round(result.data["forecast_margin"], 4) == 0.14
        assert result.data["classification"] == "commercial_confidential"


def test_cost_plan_requires_all_cost_components():
    project_id = "PRJ-COST-PLAN-2"
    _seed(project_id)
    payload = _payload()
    del payload["costs"]["tax"]
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p04.cost_plan", project_id, "lead", "cost_lead", payload)
        assert result.outcome == "needs_information"
        assert "tax" in result.data["required"]


def test_cost_plan_rejects_negative_cost():
    project_id = "PRJ-COST-PLAN-3"
    _seed(project_id)
    payload = _payload()
    payload["costs"]["material"] = -1
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p04.cost_plan", project_id, "lead", "cost_lead", payload)
        assert result.outcome == "failed"
        assert result.data["reason"] == "negative_cost_not_allowed"


def test_cost_plan_blocked_for_noncommercial_roles():
    project_id = "PRJ-COST-PLAN-4"
    _seed(project_id)
    for role in ("technical", "production", "records"):
        with SessionLocal() as db:
            _, result = gateway.execute(db, "p04.cost_plan", project_id, role, role, _payload())
            assert result.outcome == "failed"
            assert result.data["reason"] == "commercial_confidential"
