from pathlib import Path

from app.adapters_material_price import material_price_file, search_material_prices
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


@register(CapabilityManifest(id="p04.material_price_search", version="1.0.0", risk="medium", reads=["material_price_source"], commercial=True))
def material_price_search(db, project_id, actor, role, payload):
    keyword = str(payload.get("keyword", "")).strip()
    if not keyword:
        return CapabilityResult("needs_information", {"required": ["keyword"]})
    source = Path(payload["source_file"]).expanduser().resolve() if payload.get("source_file") else material_price_file()
    rows = search_material_prices(
        keyword,
        region=payload.get("region"),
        month=payload.get("month"),
        source_file=source,
        top_k=int(payload.get("top_k", 20)),
    )
    verified = [x for x in rows if x["verified_source_context"]]
    outcome = "success" if verified else "needs_information"
    return CapabilityResult(outcome, {
        "query": keyword,
        "results": rows,
        "verified_results": verified,
        "price_source": {"read_only": True, "source_file": str(source)},
        "warning": None if verified else "No price with complete source/month/region context was found.",
    })
