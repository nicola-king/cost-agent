from sqlalchemy import select
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult
from app.core.models import Source, BOQItem, Measurement

@register(CapabilityManifest(id="p01.startup_health", version="1.0.0", risk="low"))
def startup_health(db, project_id, actor, role, payload):
    sources = db.scalars(select(Source).where(Source.project_id == project_id)).all()
    boqs = db.scalars(select(BOQItem).where(BOQItem.project_id == project_id)).all()
    baselines = db.scalars(select(Measurement).where(Measurement.project_id == project_id, Measurement.measurement_type == "baseline_drawing")).all()
    missing = []
    if not sources: missing.append("project_sources")
    if not boqs: missing.append("award_boq")
    if not baselines: missing.append("construction_drawing_baseline_quantity")
    return CapabilityResult("success" if not missing else "needs_information", {
        "sources": len(sources), "boq_items": len(boqs), "baseline_measurements": len(baselines), "missing": missing
    })

@register(CapabilityManifest(id="p01.baseline0_build", version="1.0.0", risk="high"))
def baseline0_build(db, project_id, actor, role, payload):
    """Build 0-ledger projection: construction-drawing quantity is baseline; award BOQ quantity is reference; award unit price is baseline price."""
    boqs = db.scalars(select(BOQItem).where(BOQItem.project_id == project_id)).all()
    if not boqs:
        return CapabilityResult("needs_information", {"required": ["award_boq"]})
    rows=[]; missing=[]
    for b in boqs:
        ms=db.scalars(select(Measurement).where(Measurement.project_id==project_id, Measurement.object_id==b.id, Measurement.measurement_type=="baseline_drawing")).all()
        if not ms:
            missing.append({"boq_id":b.id,"code":b.code,"name":b.name,"missing":"construction_drawing_baseline_quantity"}); continue
        m=sorted(ms,key=lambda x:x.created_at)[-1]
        reference=b.award_quantity
        diff=None if reference is None else m.quantity-reference
        baseline_amount=None if b.award_unit_price is None else m.quantity*b.award_unit_price
        rows.append({"boq_id":b.id,"code":b.code,"name":b.name,"unit":b.unit,"award_quantity_reference":reference,"construction_drawing_baseline_quantity":m.quantity,"quantity_difference":diff,"award_unit_price_baseline":b.award_unit_price,"baseline_amount":baseline_amount,"measurement_id":m.id})
    outcome="success" if not missing else ("partial" if rows else "needs_information")
    return CapabilityResult(outcome,{"principle":"construction_drawing_quantity_is_baseline; award_boq_quantity_is_reference; award_unit_price_is_baseline","rows":rows,"missing":missing,"summary":{"boq_items":len(boqs),"baseline_ready":len(rows),"missing":len(missing)}})
