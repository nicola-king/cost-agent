from sqlalchemy import select
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult
from app.core.models import BOQItem

@register(CapabilityManifest(id="p02.boq_match", version="1.0.0", risk="medium"))
def boq_match(db, project_id, actor, role, payload):
    name = (payload.get("name") or "").strip().lower()
    unit = (payload.get("unit") or "").strip().lower()
    if not name:
        return CapabilityResult("needs_information", {"required": ["name"]})
    boqs = db.scalars(select(BOQItem).where(BOQItem.project_id == project_id)).all()
    exact, similar = [], []
    tokens = set(name.replace("/", " ").split())
    for b in boqs:
        bn = b.name.lower()
        if bn == name and (not unit or b.unit.lower() == unit):
            exact.append({"id": b.id, "code": b.code, "name": b.name, "unit": b.unit, "award_unit_price": b.award_unit_price})
        else:
            bt = set(bn.replace("/", " ").split())
            overlap = len(tokens & bt) / max(1, len(tokens | bt))
            if overlap >= 0.25 or name in bn or bn in name:
                similar.append({"id": b.id, "code": b.code, "name": b.name, "unit": b.unit, "award_unit_price": b.award_unit_price, "similarity_hint": round(overlap, 3)})
    if exact:
        cls = "same_boq"
    elif similar:
        cls = "similar_boq"
    else:
        cls = "no_boq"
    return CapabilityResult("success", {"classification": cls, "exact": exact, "similar": sorted(similar, key=lambda x: x["similarity_hint"], reverse=True)[:10]})
