from app.core.db import SessionLocal
from app.core.models import Project, BOQItem, Evidence, EvidenceSubmission
from app.services.capability import gateway
from app import plugins


FULL_TYPES = [
    ("photo", "production", "construction"),
    ("video", "production", "construction"),
    ("measurement_record", "production", "surveyor"),
    ("material_test", "technical", "laboratory"),
    ("hidden_work_record", "records", "records"),
    ("material_record", "materials", "materials"),
    ("equipment_usage_record", "production", "equipment"),
    ("measure_material_photo", "production", "construction"),
    ("measure_material_video", "production", "construction"),
    ("measure_equipment_photo", "production", "equipment"),
    ("measure_equipment_video", "production", "equipment"),
]


def _seed(project_id: str, boq_id: str):
    with SessionLocal() as db:
        db.merge(Project(id=project_id, name=project_id))
        db.merge(BOQItem(id=boq_id, project_id=project_id, code="EVID-FULL", name="措施工程", unit="项", award_quantity=1, award_unit_price=1))
        db.commit()


def test_full_evidence_types_close_only_with_matching_verified_evidence():
    project_id = "PRJ-EVID-FULL-1"
    boq_id = "BOQ-EVID-FULL-1"
    _seed(project_id, boq_id)
    requirements = []
    for idx, (etype, dept, role) in enumerate(FULL_TYPES, 1):
        requirements.append({
            "task_id": f"TASK-FULL-{idx}",
            "department": dept,
            "role": role,
            "assignee": f"user-{idx}",
            "evidence_type": etype,
            "required_channel": "mobile" if "photo" in etype or "video" in etype else "web",
        })
    with SessionLocal() as db:
        _, plan = gateway.execute(db, "p06.evidence_plan", project_id, "cost", "cost_lead", {"boq_id": boq_id, "requirements": requirements})
        assert plan.outcome == "success"
        for idx, (etype, dept, role) in enumerate(FULL_TYPES, 1):
            ev_id = f"EV-FULL-{idx}"
            task_id = f"TASK-FULL-{idx}"
            db.merge(Evidence(id=ev_id, project_id=project_id, evidence_type=etype, status="verified", created_by=f"user-{idx}"))
            db.merge(EvidenceSubmission(id=f"SUB-FULL-{idx}", project_id=project_id, evidence_id=ev_id, task_id=task_id, department=dept, role=role, assignee=f"user-{idx}", source_channel="mobile" if "photo" in etype or "video" in etype else "web", verification_state="verified"))
        db.commit()
        _, closure = gateway.execute(db, "p06.evidence_closure", project_id, "cost", "cost_lead", {"boq_id": boq_id})
    assert closure.outcome == "success"
    assert closure.data["closed_requirements"] == len(FULL_TYPES)
    assert closure.data["closure_ratio"] == 1.0
    required_types = {row["required_evidence_type"] for row in closure.data["requirements"]}
    assert required_types == {x[0] for x in FULL_TYPES}


def test_wrong_verified_evidence_type_does_not_close_requirement():
    project_id = "PRJ-EVID-FULL-2"
    boq_id = "BOQ-EVID-FULL-2"
    _seed(project_id, boq_id)
    with SessionLocal() as db:
        _, plan = gateway.execute(db, "p06.evidence_plan", project_id, "cost", "cost_lead", {"boq_id": boq_id, "requirements":[{
            "task_id":"TASK-WRONG-TYPE", "department":"production", "role":"equipment", "assignee":"eq-1", "evidence_type":"equipment_usage_record"
        }]})
        assert plan.outcome == "success"
        db.merge(Evidence(id="EV-WRONG-PHOTO", project_id=project_id, evidence_type="photo", status="verified", created_by="eq-1"))
        db.merge(EvidenceSubmission(id="SUB-WRONG-PHOTO", project_id=project_id, evidence_id="EV-WRONG-PHOTO", task_id="TASK-WRONG-TYPE", department="production", role="equipment", assignee="eq-1", source_channel="mobile", verification_state="verified"))
        db.commit()
        _, closure = gateway.execute(db, "p06.evidence_closure", project_id, "cost", "cost_lead", {"boq_id": boq_id})
    assert closure.outcome == "needs_information"
    row = closure.data["requirements"][0]
    assert row["closed"] is False
    assert row["required_evidence_type"] == "equipment_usage_record"
    assert row["rejected_type_mismatch"][0]["actual_type"] == "photo"
