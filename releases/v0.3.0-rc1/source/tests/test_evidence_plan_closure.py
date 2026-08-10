from datetime import datetime, timezone

from app.core.db import Base, engine, SessionLocal
from app.core.models import Project, BOQItem, Evidence, EvidenceSubmission
from app.services.capability import gateway
from app import plugins


def setup_module():
    Base.metadata.create_all(bind=engine)


def _seed():
    project_id = "PRJ-EVID-PLAN"
    with SessionLocal() as db:
        db.merge(Project(id=project_id, name="evidence-plan"))
        db.merge(BOQItem(id="BOQ-E1", project_id=project_id, code="0101", name="地下室防水", unit="m2", award_quantity=1000, award_unit_price=80))
        db.commit()
    return project_id


def test_evidence_plan_assigns_departments_people_due_dates_and_required_media():
    project_id = _seed()
    due = datetime(2026, 8, 20, tzinfo=timezone.utc)
    requirements = [
        {"task_id":"TASK-E-TECH","department":"technical","role":"technical_lead","assignee":"tech-a","evidence_type":"technical_plan","due_at":due},
        {"task_id":"TASK-E-MEAS","department":"production","role":"surveyor","assignee":"survey-a","evidence_type":"measurement_record","due_at":due},
        {"task_id":"TASK-E-LAB","department":"technical","role":"laboratory","assignee":"lab-a","evidence_type":"material_test","due_at":due},
        {"task_id":"TASK-E-HIDDEN","department":"records","role":"records","assignee":"records-a","evidence_type":"hidden_work_record","due_at":due},
        {"task_id":"TASK-E-PHOTO","department":"production","role":"construction","assignee":"site-a","evidence_type":"photo","required_channel":"mobile","due_at":due},
        {"task_id":"TASK-E-VIDEO","department":"production","role":"construction","assignee":"site-a","evidence_type":"video","required_channel":"mobile","due_at":due},
    ]
    with SessionLocal() as db:
        _, result = gateway.execute(db,"p06.evidence_plan",project_id,"tester","cost_lead",{"boq_id":"BOQ-E1","requirements":requirements})
        assert result.outcome == "success"
        assert len(result.data["requirements"]) == 6
        photo = next(x for x in result.data["requirements"] if x["evidence_type"] == "photo")
        assert photo["department"] == "production"
        assert photo["assignee"] == "site-a"
        assert photo["required_channel"] == "mobile"
        assert photo["due_at"].startswith("2026-08-20")


def test_evidence_closure_counts_only_verified_evidence_and_keeps_task_responsibility():
    project_id = _seed()
    with SessionLocal() as db:
        _, plan = gateway.execute(db,"p06.evidence_plan",project_id,"tester","cost_lead",{"boq_id":"BOQ-E1","requirements":[
            {"task_id":"TASK-E-C1","department":"production","role":"construction","assignee":"site-a","evidence_type":"photo"},
            {"task_id":"TASK-E-C2","department":"technical","role":"laboratory","assignee":"lab-a","evidence_type":"material_test"},
        ]})
        assert plan.outcome == "success"
        db.merge(Evidence(id="EV-E-C1",project_id=project_id,evidence_type="photo",status="verified",created_by="site-a"))
        db.merge(EvidenceSubmission(id="SUB-E-C1",project_id=project_id,evidence_id="EV-E-C1",task_id="TASK-E-C1",department="production",role="construction",assignee="site-a",source_channel="mobile",verification_state="verified"))
        db.commit()
        _, closure = gateway.execute(db,"p06.evidence_closure",project_id,"tester","cost_lead",{"boq_id":"BOQ-E1"})
        assert closure.outcome == "partial"
        assert closure.data["total_requirements"] == 2
        assert closure.data["closed_requirements"] == 1
        assert closure.data["closure_ratio"] == 0.5
        open_row = next(x for x in closure.data["requirements"] if x["task_id"] == "TASK-E-C2")
        assert open_row["department"] == "technical"
        assert open_row["assignee"] == "lab-a"
        assert open_row["closed"] is False


def test_evidence_closure_rejects_unverified_submission_as_closed():
    project_id = _seed()
    with SessionLocal() as db:
        _, plan = gateway.execute(db,"p06.evidence_plan",project_id,"tester","cost_lead",{"boq_id":"BOQ-E1","requirements":[{"task_id":"TASK-E-U1","department":"records","role":"records","assignee":"records-a","evidence_type":"hidden_work_record"}]})
        assert plan.outcome == "success"
        db.merge(Evidence(id="EV-E-U1",project_id=project_id,evidence_type="hidden_work_record",status="candidate",created_by="records-a"))
        db.merge(EvidenceSubmission(id="SUB-E-U1",project_id=project_id,evidence_id="EV-E-U1",task_id="TASK-E-U1",department="records",role="records",assignee="records-a",source_channel="web",verification_state="candidate"))
        db.commit()
        _, closure = gateway.execute(db,"p06.evidence_closure",project_id,"tester","cost_lead",{"boq_id":"BOQ-E1"})
        assert closure.outcome == "needs_information"
        assert closure.data["closed_requirements"] == 0
        assert closure.data["closure_ratio"] == 0.0
