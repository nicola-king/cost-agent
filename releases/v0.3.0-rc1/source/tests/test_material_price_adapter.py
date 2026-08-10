import json
from pathlib import Path

from app.adapters_material_price import clear_material_price_cache, search_material_prices
from app.services.capability import gateway


def test_verified_material_price_requires_source_context(tmp_path: Path):
    path = tmp_path / "prices.json"
    path.write_text(json.dumps({"records": [
        {"name":"HRB400E 钢筋 Φ20","unit":"t","price":4180,"region":"重庆","month":"2026-04","source":"官方信息价"},
        {"name":"HRB400E 钢筋 Φ25","unit":"t","price":4200}
    ]}, ensure_ascii=False), encoding="utf-8")
    clear_material_price_cache()
    rows = search_material_prices("HRB400E", source_file=path)
    assert rows[0]["verified_source_context"] is True
    assert rows[1]["verified_source_context"] is False


def test_material_price_adapter_is_read_only(tmp_path: Path):
    path = tmp_path / "prices.json"
    path.write_text(json.dumps({"records":[{"name":"C30 商品砼","price":520,"unit":"m3","region":"重庆","month":"2026-04","source":"官方信息价"}]}, ensure_ascii=False), encoding="utf-8")
    clear_material_price_cache()
    before = path.read_bytes()
    search_material_prices("C30", source_file=path)
    assert path.read_bytes() == before


def test_material_price_capability_registered():
    assert "p04.material_price_search" in {m.id for m in gateway.manifests()}
