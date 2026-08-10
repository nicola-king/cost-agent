import json
from pathlib import Path

from app.adapters_historical_cost import historical_statistics, load_historical_projects
from app.services.capability import gateway


def _history(tmp_path: Path) -> Path:
    path = tmp_path / "history.json"
    path.write_text(json.dumps({"_meta":{"source":"已核验历史项目库"}, "projects":[
        {"id":"H1","name":"项目A","type":"房建","location":"重庆","completion_date":"2024-12-01","cost":{"unit_price":3200}},
        {"id":"H2","name":"项目B","type":"房建","location":"重庆","completion_date":"2025-10-01","cost":{"unit_price":3600}},
    ]}, ensure_ascii=False), encoding="utf-8")
    return path


def test_historical_cost_is_reference_only(tmp_path: Path):
    rows = load_historical_projects(_history(tmp_path))
    assert all(r["usage"] == "REFERENCE_ONLY" for r in rows)
    assert all(r["can_overwrite_project_actuals"] is False for r in rows)
    assert all(r["verified_source_context"] is True for r in rows)


def test_historical_statistics_are_derived(tmp_path: Path):
    stats = historical_statistics(project_type="房建", location="重庆", source_file=_history(tmp_path))
    assert stats["count"] == 2
    assert stats["avg_unit_price"] == 3400
    assert stats["usage"] == "REFERENCE_ONLY"


def test_historical_cost_capabilities_are_commercial_and_registered():
    manifests = {m.id: m for m in gateway.manifests()}
    assert manifests["p04.historical_cost_query"].commercial is True
    assert manifests["p04.historical_cost_stats"].commercial is True
