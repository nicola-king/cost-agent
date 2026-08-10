from app.core.db import Base, engine, SessionLocal
from app.core.models import Project, BOQItem
from app.services.capability import gateway
from app import plugins


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_evidence_plan_requires_requirements_and_valid_boq():
    project_id = "PRJ-EVID-GUARD"
    with SessionLocal() as db:
        db.merge(Project(id=project_id, name="guard"))
        db.merge(BOQItem(id="BOQ-E-G1", project_id=project_id, code="G1", name="混凝土", unit="m3", award_quantity=1, award_unit_price=1))
        db.commit()

        _, no_requirements = gateway.execute(db, "p06.evidence_plan", project_id, "tester", "cost_lead", {"boq_id":"BOQ-E-G1"})
        assert no_requirements.outcome == "needs_information"
        assert no_requirements.data == {"required":["requirements"]}

        _, invalid_boq = gateway.execute(db, "p06.evidence_plan", project_id, "tester", "cost_lead", {"boq_id":"BOQ-NOT-FOUND", "requirements":[{"department":"technical","evidence_type":"technical_plan"}]})
        assert invalid_boq.outcome == "needs_information"
        assert invalid_boq.data == {"required":["valid_boq_id"]}
