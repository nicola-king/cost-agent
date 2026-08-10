from app.core.db import Base, engine, SessionLocal
from app.core.models import Project, BOQItem, Measurement
from app.services.capability import gateway
from app import plugins

def setup_module():
    Base.metadata.create_all(bind=engine)

def test_boq_three_way_match():
    with SessionLocal() as db:
        db.merge(Project(id="PRJ-TEST", name="test"))
        db.merge(BOQItem(id="BOQ-T1", project_id="PRJ-TEST", code="0101", name="C30混凝土", unit="m3", award_quantity=100, award_unit_price=900)); db.commit()
        _,r=gateway.execute(db,"p02.boq_match","PRJ-TEST","tester","cost_lead",{"name":"C30混凝土","unit":"m3"})
        assert r.data["classification"] == "same_boq"
        _,r=gateway.execute(db,"p02.boq_match","PRJ-TEST","tester","cost_lead",{"name":"C35混凝土","unit":"m3"})
        assert r.data["classification"] in {"similar_boq","no_boq"}

def test_quantity_reconcile_flags_difference():
    with SessionLocal() as db:
        db.merge(Project(id="PRJ-Q", name="q"))
        db.merge(Measurement(id="M-Q1",project_id="PRJ-Q",object_id="BOQ-Q",measurement_type="baseline_drawing",quantity=318.256,unit="m3",method="cad"))
        db.merge(Measurement(id="M-Q2",project_id="PRJ-Q",object_id="BOQ-Q",measurement_type="baseline_drawing",quantity=316.842,unit="m3",method="bim")); db.commit()
        _,r=gateway.execute(db,"p03.quantity_reconcile","PRJ-Q","tester","cost_lead",{"object_id":"BOQ-Q"})
        assert r.outcome == "conflict" and r.data["status"] == "unresolved_difference"

def test_commercial_capability_denied_to_technical():
    with SessionLocal() as db:
        db.merge(Project(id="PRJ-C", name="c")); db.commit()
        _,r=gateway.execute(db,"p04.forecast_margin","PRJ-C","tester","technical",{"quantity":10,"revenue_unit_price":100,"resource_cost":700})
        assert r.outcome == "failed" and r.data["reason"] == "commercial_confidential"
