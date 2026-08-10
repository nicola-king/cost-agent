from app.core.db import Base, engine, SessionLocal
from app.core.models import Project, BOQItem
from app.services.capability import gateway
from app import plugins


def setup_module():
    Base.metadata.create_all(bind=engine)


def _seed_project():
    project_id = "PRJ-BOQ-CLASS"
    with SessionLocal() as db:
        db.merge(Project(id=project_id, name="boq-classification"))
        db.merge(BOQItem(id="BOQ-SAME", project_id=project_id, code="010101", name="C30混凝土", unit="m3", award_quantity=100.0, award_unit_price=900.0))
        db.merge(BOQItem(id="BOQ-SIM", project_id=project_id, code="010102", name="C35混凝土", unit="m3", award_quantity=80.0, award_unit_price=980.0))
        db.merge(BOQItem(id="BOQ-STEEL", project_id=project_id, code="020101", name="HRB400钢筋", unit="t", award_quantity=20.0, award_unit_price=4200.0))
        db.commit()
    return project_id


def test_boq_classification_same():
    project_id = _seed_project()
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p02.boq_match", project_id, "tester", "cost_lead", {"name": "C30混凝土", "unit": "m3"})
        assert result.outcome == "success"
        assert result.data["classification"] == "same_boq"
        assert result.data["exact"][0]["id"] == "BOQ-SAME"
        assert result.data["exact"][0]["award_unit_price"] == 900.0


def test_boq_classification_similar():
    project_id = _seed_project()
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p02.boq_match", project_id, "tester", "cost_lead", {"name": "C40混凝土", "unit": "m3"})
        assert result.outcome == "success"
        assert result.data["classification"] == "similar_boq"
        assert result.data["exact"] == []
        assert any(item["id"] in {"BOQ-SAME", "BOQ-SIM"} for item in result.data["similar"])


def test_boq_classification_missing():
    project_id = _seed_project()
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p02.boq_match", project_id, "tester", "cost_lead", {"name": "防火涂料", "unit": "kg"})
        assert result.outcome == "success"
        assert result.data["classification"] == "no_boq"
        assert result.data["exact"] == []
        assert result.data["similar"] == []


def test_boq_classification_requires_name():
    project_id = _seed_project()
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p02.boq_match", project_id, "tester", "cost_lead", {"unit": "m3"})
        assert result.outcome == "needs_information"
        assert result.data == {"required": ["name"]}
