from pathlib import Path

from app.adapters_quota import available_professions, get_quota_by_code, quota_data_dir, search_quota
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


def _root(payload):
    return Path(payload["data_dir"]).expanduser().resolve() if payload.get("data_dir") else quota_data_dir()


@register(CapabilityManifest(id="p08.quota_search", version="1.0.0", risk="low", reads=["quota_rule_pack"]))
def quota_search(db, project_id, actor, role, payload):
    keyword = str(payload.get("keyword", "")).strip()
    if not keyword:
        return CapabilityResult("needs_information", {"required": ["keyword"]})
    root = _root(payload)
    results = search_quota(keyword, top_k=int(payload.get("top_k", 10)), professions=payload.get("professions"), data_dir=root)
    return CapabilityResult(
        "success" if results else "needs_information",
        {"query": keyword, "results": results, "rule_pack": {"type": "quota", "read_only": True, "data_dir": str(root)}, "no_match_found": not results},
    )


@register(CapabilityManifest(id="p08.quota_get", version="1.0.0", risk="low", reads=["quota_rule_pack"]))
def quota_get(db, project_id, actor, role, payload):
    code = str(payload.get("code", "")).strip()
    if not code:
        return CapabilityResult("needs_information", {"required": ["code"]})
    root = _root(payload)
    item = get_quota_by_code(code, profession=payload.get("profession"), data_dir=root)
    return CapabilityResult(
        "success" if item else "needs_information",
        {"code": code, "quota": item, "rule_pack": {"type": "quota", "read_only": True, "data_dir": str(root)}, "not_found": item is None},
    )


@register(CapabilityManifest(id="p08.quota_stats", version="1.0.0", risk="low", reads=["quota_rule_pack"]))
def quota_stats(db, project_id, actor, role, payload):
    root = _root(payload)
    rows = available_professions(root)
    return CapabilityResult(
        "success" if rows else "needs_information",
        {"professions": rows, "rule_pack": {"type": "quota", "read_only": True, "data_dir": str(root)}},
    )
