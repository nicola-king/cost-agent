from app.core.db import SessionLocal
from app.core.models import AuditEvent, Calculation, Evidence, Project, Relation, Rule, Source
from app.plugins.base import gateway


def test_provenance_drilldown_reaches_original_immutable_source():
    project_id = "P-PROV-1"
    source_id = "SRC-PROV-1"
    evidence_id = "EV-PROV-1"
    result_id = "RESULT-PROV-1"
    rule_id = "RULE-PROV-1"
    with SessionLocal() as db:
        if not db.get(Project, project_id):
            db.add(Project(id=project_id, name="Provenance Project", region="重庆"))
        db.add(Source(id=source_id, project_id=project_id, title="施工图A版", source_type="construction_drawing", file_path="/immutable/drawing-a.pdf", sha256="a" * 64, version="A", immutable=True))
        db.add(Evidence(id=evidence_id, project_id=project_id, source_id=source_id, evidence_type="drawing_quantity", status="verified", created_by="cost_lead"))
        db.add(Relation(id="REL-PROV-1", project_id=project_id, source_object_id=result_id, relation_type="supported_by", target_object_id=evidence_id, status="verified", created_by="cost_lead"))
        db.add(Rule(id=rule_id, title="施工图基准规则", rule_type="project_rule", source_id=source_id, region="重庆", classification="external"))
        db.add(Calculation(id="CALC-PROV-1", project_id=project_id, calculation_type="baseline_quantity", method="drawing_baseline", input_snapshot={"evidence_id": evidence_id}, rule_refs=[rule_id], output_snapshot={"result_object_id": result_id, "quantity": 100}, status="calculated", executed_by="agent"))
        db.add(AuditEvent(id="AUD-PROV-1", project_id=project_id, actor="agent", action="capability:p03.resource_control_line", object_id=result_id, details={"version": "1.0.0", "outcome": "success", "human_confirmed": True}))
        db.commit()

        _, result = gateway.execute(db, "p08.provenance_drilldown", project_id, "auditor", "cost_lead", {"object_id": result_id})

    assert result.outcome == "success"
    assert result.data["trace_complete"] is True
    assert result.data["calculations"][0]["id"] == "CALC-PROV-1"
    assert result.data["evidence"][0]["id"] == evidence_id
    assert result.data["rules"][0]["id"] == rule_id
    assert result.data["original_sources"][0]["id"] == source_id
    assert result.data["original_sources"][0]["immutable"] is True
    assert result.data["original_sources"][0]["sha256"] == "a" * 64
    assert result.data["agent_workflow"][0]["actor"] == "agent"
    assert result.data["agent_workflow"][0]["details"]["human_confirmed"] is True


def test_provenance_without_original_source_is_partial_not_verified():
    project_id = "P-PROV-2"
    result_id = "RESULT-PROV-2"
    with SessionLocal() as db:
        if not db.get(Project, project_id):
            db.add(Project(id=project_id, name="Incomplete Provenance", region="重庆"))
        db.add(AuditEvent(id="AUD-PROV-2", project_id=project_id, actor="agent", action="capability:p02.advisory_match", object_id=result_id, details={"outcome": "success"}))
        db.commit()
        _, result = gateway.execute(db, "p08.provenance_drilldown", project_id, "auditor", "cost_lead", {"object_id": result_id})

    assert result.outcome == "partial"
    assert result.data["trace_complete"] is False
    assert result.data["original_sources"] == []


def test_provenance_requires_object_id():
    with SessionLocal() as db:
        _, result = gateway.execute(db, "p08.provenance_drilldown", "P-PROV-3", "auditor", "cost_lead", {})
    assert result.outcome == "needs_information"
    assert "object_id" in result.data["required"]
