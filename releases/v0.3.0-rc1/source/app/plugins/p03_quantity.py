from sqlalchemy import select
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult
from app.core.models import Measurement
from app.services.reconciliation import reconcile

@register(CapabilityManifest(id="p03.quantity_reconcile", version="1.0.0", risk="medium"))
def quantity_reconcile(db, project_id, actor, role, payload):
    object_id = payload.get("object_id")
    if not object_id:
        return CapabilityResult("needs_information", {"required": ["object_id"]})
    rows = db.scalars(select(Measurement).where(Measurement.project_id == project_id, Measurement.object_id == object_id)).all()
    if len(rows) < 2:
        return CapabilityResult("needs_information", {"measurement_count": len(rows), "reason": "need_at_least_two_results"})
    r = reconcile([(f"{x.id}:{x.method}:{x.measurement_type}", x.quantity) for x in rows], tolerance=float(payload.get("tolerance", 0)))
    issues = []
    if r.status == "unresolved_difference":
        issues.append({"type": "quantity_difference", "severity": "high", "difference": r.difference, "difference_rate": r.difference_rate, "state": "unresolved_difference"})
    return CapabilityResult("conflict" if issues else "success", {"status": r.status, "min": r.min_value, "max": r.max_value, "difference": r.difference, "difference_rate": r.difference_rate, "details": r.details}, issues=issues)
