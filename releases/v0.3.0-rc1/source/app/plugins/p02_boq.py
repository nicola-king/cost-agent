import re
from sqlalchemy import select
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult
from app.core.models import BOQItem


def _normalize_spec_name(value: str) -> str:
    """Remove common grade/spec markers for advisory similarity only.

    Exact SAME classification is still based on the original normalized name/unit.
    This helper is only used to find SIMILAR candidates such as C30/C35/C40 concrete
    or HRB400/HRB500 rebar.
    """
    text = (value or "").strip().lower()
    text = re.sub(r"(?:hrb|hpb|crb|c)\s*\d+(?:\.\d+)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\s/_\-]+", "", text)
    return text


@register(CapabilityManifest(id="p02.boq_match", version="1.0.1", risk="medium"))
def boq_match(db, project_id, actor, role, payload):
    name = (payload.get("name") or "").strip().lower()
    unit = (payload.get("unit") or "").strip().lower()
    if not name:
        return CapabilityResult("needs_information", {"required": ["name"]})

    boqs = db.scalars(select(BOQItem).where(BOQItem.project_id == project_id)).all()
    exact, similar = [], []
    tokens = set(name.replace("/", " ").split())
    normalized_name = _normalize_spec_name(name)

    for b in boqs:
        bn = b.name.lower()
        bunit = (b.unit or "").lower()
        if bn == name and (not unit or bunit == unit):
            exact.append({
                "id": b.id,
                "code": b.code,
                "name": b.name,
                "unit": b.unit,
                "award_unit_price": b.award_unit_price,
            })
            continue

        bt = set(bn.replace("/", " ").split())
        overlap = len(tokens & bt) / max(1, len(tokens | bt))
        normalized_boq = _normalize_spec_name(bn)
        same_family = bool(normalized_name and normalized_boq) and (
            normalized_name == normalized_boq
            or normalized_name in normalized_boq
            or normalized_boq in normalized_name
        )
        unit_compatible = not unit or bunit == unit

        if unit_compatible and (overlap >= 0.25 or name in bn or bn in name or same_family):
            similarity_hint = overlap
            if same_family:
                similarity_hint = max(similarity_hint, 0.8)
            similar.append({
                "id": b.id,
                "code": b.code,
                "name": b.name,
                "unit": b.unit,
                "award_unit_price": b.award_unit_price,
                "similarity_hint": round(similarity_hint, 3),
                "match_basis": "normalized_family" if same_family else "text_overlap",
            })

    if exact:
        cls = "same_boq"
    elif similar:
        cls = "similar_boq"
    else:
        cls = "no_boq"

    return CapabilityResult("success", {
        "classification": cls,
        "exact": exact,
        "similar": sorted(similar, key=lambda x: x["similarity_hint"], reverse=True)[:10],
    })
