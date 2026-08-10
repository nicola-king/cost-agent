from __future__ import annotations

import json
import os
from pathlib import Path


def historical_cost_file() -> Path:
    configured = os.getenv("CCI_HISTORICAL_COST_FILE")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "data" / "history" / "historical_projects.json"


def load_historical_projects(source_file: Path | None = None) -> list[dict]:
    path = (source_file or historical_cost_file()).resolve()
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("projects", []) if isinstance(payload, dict) else []
    result = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        completion_date = str(row.get("completion_date") or "")
        location = str(row.get("location") or "")
        source = row.get("source") or (payload.get("_meta", {}).get("source") if isinstance(payload.get("_meta"), dict) else None)
        verified_context = bool(source and location and completion_date)
        result.append({**row,"source":source,"verified_source_context":verified_context,"usage":"REFERENCE_ONLY","can_overwrite_project_actuals":False,"source_file":str(path)})
    return result


def query_historical_projects(*, project_type: str = "", location: str = "", year: str = "", source_file: Path | None = None, top_k: int = 50) -> list[dict]:
    rows = load_historical_projects(source_file)
    if project_type:
        rows = [r for r in rows if project_type in str(r.get("type", ""))]
    if location:
        rows = [r for r in rows if location in str(r.get("location", ""))]
    if year:
        rows = [r for r in rows if str(r.get("completion_date", "")).startswith(year)]
    return rows[: max(1, min(int(top_k), 200))]


def historical_statistics(*, project_type: str = "", location: str = "", source_file: Path | None = None) -> dict:
    rows = query_historical_projects(project_type=project_type, location=location, source_file=source_file, top_k=200)
    unit_prices = []
    for row in rows:
        cost = row.get("cost") or {}
        value = cost.get("unit_price") if isinstance(cost, dict) else None
        if isinstance(value, (int, float)):
            unit_prices.append(float(value))
    return {"count":len(rows),"verified_context_count":sum(1 for r in rows if r.get("verified_source_context")),"avg_unit_price":sum(unit_prices)/len(unit_prices) if unit_prices else None,"min_unit_price":min(unit_prices) if unit_prices else None,"max_unit_price":max(unit_prices) if unit_prices else None,"usage":"REFERENCE_ONLY"}
