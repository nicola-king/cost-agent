import json
from pathlib import Path

from app.adapters_quota import available_professions, clear_quota_cache, get_quota_by_code, search_quota
from app.services.capability import gateway


def make_pack(tmp_path: Path):
    root = tmp_path / "quotas"
    root.mkdir()
    payload = {
        "total": 2,
        "prefixes": {
            "AA": [
                {"deh": "AA0001", "xmmc": "人工平整场地", "chapter": "土石方工程", "dw": "m2"},
                {"deh": "AA0002", "xmmc": "机械挖土方", "chapter": "土石方工程", "dw": "m3"},
            ]
        },
    }
    (root / "building.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    clear_quota_cache()
    return root


def test_quota_adapter_search_and_code(tmp_path):
    root = make_pack(tmp_path)
    rows = search_quota("平整场地", data_dir=root)
    assert rows[0]["deh"] == "AA0001"
    assert get_quota_by_code("AA0002", data_dir=root)["xmmc"] == "机械挖土方"
    stats = available_professions(root)
    assert stats == [{
        "profession": "building", "profession_name": "建筑工程", "total": 2,
        "prefixes": 1, "source_path": str(root / "building.json")
    }]


def test_quota_adapter_is_read_only(tmp_path):
    root = make_pack(tmp_path)
    before = (root / "building.json").read_bytes()
    search_quota("土方", data_dir=root)
    get_quota_by_code("AA0001", data_dir=root)
    after = (root / "building.json").read_bytes()
    assert before == after


def test_quota_capabilities_registered():
    ids = {m.id for m in gateway.manifests()}
    assert {"p08.quota_search", "p08.quota_get", "p08.quota_stats"} <= ids
