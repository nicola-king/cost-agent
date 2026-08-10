from __future__ import annotations

from pathlib import Path

from app.adapters_templates import get_template, load_template_catalog, template_manifest_file
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


def _manifest(payload: dict) -> Path:
    return Path(payload["manifest_file"]).expanduser().resolve() if payload.get("manifest_file") else template_manifest_file()


@register(CapabilityManifest(
    id="p05.template_catalog",
    version="1.0.0",
    risk="low",
    reads=["derived_template_manifest"],
    outputs=["observation"],
))
def template_catalog(db, project_id, actor, role, payload):
    path = _manifest(payload)
    rows = load_template_catalog(path)
    category = str(payload.get("category") or "").strip().lower()
    if category:
        rows = [r for r in rows if str(r.get("category", "")).lower() == category]
    return CapabilityResult("success" if rows else "needs_information", {
        "templates": rows,
        "manifest_file": str(path),
        "templates_are_evidence": False,
        "templates_are_rules": False,
    })


@register(CapabilityManifest(
    id="p05.template_get",
    version="1.0.0",
    risk="low",
    reads=["derived_template_manifest"],
    outputs=["observation"],
))
def template_get(db, project_id, actor, role, payload):
    template_id = str(payload.get("template_id") or "").strip()
    if not template_id:
        return CapabilityResult("needs_information", {"required": ["template_id"]})
    path = _manifest(payload)
    row = get_template(template_id, path)
    return CapabilityResult("success" if row else "needs_information", {
        "template": row,
        "not_found": row is None,
        "manifest_file": str(path),
    })
