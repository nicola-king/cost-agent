from __future__ import annotations

from sqlalchemy import select

from app.core.models import AuditEvent, Calculation, Evidence, Relation, Rule, Source
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


@register(CapabilityManifest(id="p08.provenance_drilldown", version="1.0.0", risk="low"))
def provenance_drilldown(db, project_id, actor, role, payload):
    object_id = (payload.get("object_id") or "").strip()
    if not object_id:
        return CapabilityResult("needs_information", {"required": ["object_id"]})

    relations = db.scalars(
        select(Relation).where(
            Relation.project_id == project_id,
            (Relation.source_object_id == object_id) | (Relation.target_object_id == object_id),
        )
    ).all()
    related_ids = {object_id}
    for rel in relations:
        related_ids.add(rel.source_object_id)
        related_ids.add(rel.target_object_id)

    calculations = db.scalars(select(Calculation).where(Calculation.project_id == project_id)).all()
    matched_calculations = []
    rule_ids = set()
    for calc in calculations:
        snapshot_text = repr(calc.input_snapshot) + repr(calc.output_snapshot)
        if calc.id in related_ids or any(rid in snapshot_text for rid in related_ids):
            matched_calculations.append(calc)
            rule_ids.update(calc.rule_refs or [])

    evidence = db.scalars(select(Evidence).where(Evidence.project_id == project_id)).all()
    matched_evidence = [ev for ev in evidence if ev.id in related_ids or ev.source_id in related_ids]
    source_ids = {ev.source_id for ev in matched_evidence if ev.source_id}

    rules = db.scalars(select(Rule).where(Rule.id.in_(rule_ids))).all() if rule_ids else []
    source_ids.update(r.source_id for r in rules if r.source_id)
    sources = db.scalars(select(Source).where(Source.id.in_(source_ids))).all() if source_ids else []

    audits = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.project_id == project_id)
        .order_by(AuditEvent.created_at.asc())
    ).all()
    matched_audits = [a for a in audits if a.object_id in related_ids or object_id in repr(a.details)]

    trace = {
        "result_object_id": object_id,
        "calculations": [
            {
                "id": c.id,
                "type": c.calculation_type,
                "method": c.method,
                "rule_refs": c.rule_refs,
                "status": c.status,
                "executed_by": c.executed_by,
                "executed_at": c.executed_at.isoformat() if c.executed_at else None,
            }
            for c in matched_calculations
        ],
        "relations": [
            {
                "id": r.id,
                "source_object_id": r.source_object_id,
                "relation_type": r.relation_type,
                "target_object_id": r.target_object_id,
                "status": r.status,
            }
            for r in relations
        ],
        "evidence": [
            {
                "id": e.id,
                "type": e.evidence_type,
                "status": e.status,
                "source_id": e.source_id,
            }
            for e in matched_evidence
        ],
        "rules": [
            {"id": r.id, "title": r.title, "source_id": r.source_id, "classification": r.classification}
            for r in rules
        ],
        "original_sources": [
            {
                "id": s.id,
                "title": s.title,
                "source_type": s.source_type,
                "sha256": s.sha256,
                "immutable": s.immutable,
                "version": s.version,
            }
            for s in sources
        ],
        "agent_workflow": [
            {
                "audit_id": a.id,
                "actor": a.actor,
                "action": a.action,
                "object_id": a.object_id,
                "details": a.details,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in matched_audits
        ],
    }

    has_origin = bool(trace["original_sources"])
    has_decision_path = bool(trace["calculations"] or trace["relations"] or trace["evidence"])
    outcome = "success" if has_origin and has_decision_path else "partial"
    trace["trace_complete"] = outcome == "success"
    trace["required_chain"] = "Result -> Calculation / Decision -> Evidence / Rule -> Original Source"
    return CapabilityResult(outcome, trace)
