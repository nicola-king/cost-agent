from __future__ import annotations

from pathlib import Path

from app.adapters_historical_cost import historical_cost_file, historical_statistics, query_historical_projects
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


def _source(payload: dict) -> Path:
    return Path(payload["source_file"]).expanduser().resolve() if payload.get("source_file") else historical_cost_file()


@register(CapabilityManifest(id="p04.historical_cost_query",version="1.0.0",risk="low",reads=["historical_cost_reference"],outputs=["observation"],commercial=True))
def historical_cost_query(db, project_id, actor, role, payload):
    path = _source(payload)
    rows = query_historical_projects(project_type=str(payload.get("project_type") or ""),location=str(payload.get("location") or ""),year=str(payload.get("year") or ""),source_file=path,top_k=int(payload.get("top_k",50)))
    return CapabilityResult("success" if rows else "needs_information", {"projects":rows,"source_file":str(path),"usage":"REFERENCE_ONLY","can_overwrite_project_actuals":False})


@register(CapabilityManifest(id="p04.historical_cost_stats",version="1.0.0",risk="low",reads=["historical_cost_reference"],outputs=["observation"],commercial=True))
def historical_cost_stats(db, project_id, actor, role, payload):
    path = _source(payload)
    stats = historical_statistics(project_type=str(payload.get("project_type") or ""),location=str(payload.get("location") or ""),source_file=path)
    return CapabilityResult("success" if stats["count"] else "needs_information", {"statistics":stats,"source_file":str(path)})
