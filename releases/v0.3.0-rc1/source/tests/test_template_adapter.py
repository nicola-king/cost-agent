import json
from pathlib import Path

from app.adapters_templates import get_template, load_template_catalog
from app.services.capability import gateway


def _manifest(tmp_path: Path) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"templates": [
        {"id":"TPL-CHANGE-01","name":"变更证据链清单","category":"change","scope":"global","project_specific":False,"source":"legacy/change_order/templates"},
        {"id":"TPL-PROJECT-01","name":"某项目变更管理细则","category":"change","scope":"project","project_specific":True,"source":"legacy/change_order/project.md"},
    ]}, ensure_ascii=False), encoding="utf-8")
    return path


def test_project_specific_template_is_quarantined(tmp_path: Path):
    rows = load_template_catalog(_manifest(tmp_path))
    project = [r for r in rows if r["id"] == "TPL-PROJECT-01"][0]
    assert project["status"] == "QUARANTINED"
    assert project["evidence"] is False
    assert project["rule_authority"] is False


def test_global_template_remains_derived_not_evidence(tmp_path: Path):
    row = get_template("TPL-CHANGE-01", _manifest(tmp_path))
    assert row["status"] == "AVAILABLE"
    assert row["artifact_type"] == "DERIVED_TEMPLATE"
    assert row["evidence"] is False


def test_template_capabilities_registered():
    ids = {m.id for m in gateway.manifests()}
    assert "p05.template_catalog" in ids
    assert "p05.template_get" in ids
