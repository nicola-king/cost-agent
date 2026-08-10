from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path


def material_price_file() -> Path:
    configured = os.getenv("CCI_MATERIAL_PRICE_FILE")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "data" / "prices" / "material_prices.json"


@lru_cache(maxsize=8)
def _load(path_text: str) -> dict:
    path = Path(path_text)
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"invalid material price source: {path}")
    return payload


def _records(payload: dict):
    if isinstance(payload.get("records"), list):
        for row in payload["records"]:
            if isinstance(row, dict):
                yield row
        return
    meta = payload.get("_meta", {}) if isinstance(payload.get("_meta"), dict) else {}
    for category, materials in payload.items():
        if category.startswith("_") or not isinstance(materials, dict):
            continue
        for name, data in materials.items():
            if not isinstance(data, dict) or data.get("price") is None:
                continue
            yield {
                "name": name,
                "category": category,
                "unit": data.get("unit"),
                "price": data.get("price"),
                "previous_price": data.get("previous"),
                "region": data.get("region") or meta.get("region"),
                "month": data.get("month") or meta.get("month"),
                "source": data.get("source") or meta.get("source"),
            }


def search_material_prices(keyword: str, *, region: str | None = None, month: str | None = None, source_file: Path | None = None, top_k: int = 20) -> list[dict]:
    path = (source_file or material_price_file()).resolve()
    try:
        payload = _load(str(path))
    except FileNotFoundError:
        return []
    needle = (keyword or "").strip().lower()
    rows = []
    for row in _records(payload):
        name = str(row.get("name", ""))
        if needle and needle not in name.lower():
            continue
        if region and row.get("region") and row.get("region") != region:
            continue
        if month and row.get("month") and row.get("month") != month:
            continue
        verified = bool(row.get("source") and row.get("month") and row.get("region"))
        rows.append({**row, "verified_source_context": verified, "source_file": str(path)})
    rows.sort(key=lambda x: str(x.get("name", "")))
    return rows[: max(1, min(int(top_k), 100))]


def clear_material_price_cache() -> None:
    _load.cache_clear()
