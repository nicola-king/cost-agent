from __future__ import annotations

import json
import os
from pathlib import Path


def template_manifest_file() -> Path:
    configured = os.getenv("CCI_TEMPLATE_MANIFEST")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "data" / "templates" / "manifest.json"


def load_template_catalog(manifest_file: Path | None = None) -> list[dict]:
    path = (manifest_file or template_manifest_file()).resolve()
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("templates", []) if isinstance(payload, dict) else []
    result = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("id") or not row.get("name"):
            continue
        scope = str(row.get("scope") or "project").lower()
        project_specific = bool(row.get("project_specific", scope == "project"))
        result.append({
            **row,
            "scope": scope,
            "project_specific": project_specific,
            "artifact_type": "DERIVED_TEMPLATE",
            "evidence": False,
            "rule_authority": False,
            "status": "QUARANTINED" if project_specific else "AVAILABLE",
            "manifest_file": str(path),
        })
    return result


def get_template(template_id: str, manifest_file: Path | None = None) -> dict | None:
    for row in load_template_catalog(manifest_file):
        if str(row.get("id")) == template_id:
            return row
    return None
