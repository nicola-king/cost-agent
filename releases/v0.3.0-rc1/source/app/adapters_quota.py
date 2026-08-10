from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Iterable

PROFESSION_MAP = {
    "building": "建筑工程",
    "decoration": "装饰装修",
    "installation": "安装工程",
    "municipal": "市政工程",
    "prefab": "装配式建筑",
    "transit": "轨道交通",
}


def quota_data_dir() -> Path:
    """Return the configured read-only quota rule-pack directory.

    The adapter never mutates this directory. CCI_QUOTA_DATA_DIR may point to the
    legacy cost-agent/data/quotas directory or to a separately versioned rule pack.
    """
    configured = os.getenv("CCI_QUOTA_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "data" / "rulepacks" / "quotas"


@lru_cache(maxsize=12)
def _load_profession(path_text: str, profession: str) -> dict:
    path = Path(path_text) / f"{profession}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("prefixes", {}), dict):
        raise ValueError(f"invalid quota rule pack: {path}")
    return data


def available_professions(data_dir: Path | None = None) -> list[dict]:
    root = (data_dir or quota_data_dir()).resolve()
    out = []
    for key, label in PROFESSION_MAP.items():
        path = root / f"{key}.json"
        if path.is_file():
            data = _load_profession(str(root), key)
            out.append({
                "profession": key,
                "profession_name": label,
                "total": int(data.get("total", 0) or 0),
                "prefixes": len(data.get("prefixes", {})),
                "source_path": str(path),
            })
    return out


def _iter_items(data: dict) -> Iterable[tuple[str, dict]]:
    for prefix, items in data.get("prefixes", {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                yield prefix, item


def search_quota(keyword: str, top_k: int = 10, professions: list[str] | None = None, data_dir: Path | None = None) -> list[dict]:
    root = (data_dir or quota_data_dir()).resolve()
    selected = professions or list(PROFESSION_MAP)
    needle = (keyword or "").strip().lower()
    if not needle:
        return []
    results = []
    for profession in selected:
        if profession not in PROFESSION_MAP:
            continue
        try:
            data = _load_profession(str(root), profession)
        except FileNotFoundError:
            continue
        for prefix, item in _iter_items(data):
            name = str(item.get("xmmc", ""))
            code = str(item.get("deh", ""))
            chapter = str(item.get("chapter", ""))
            score = 0
            if needle in name.lower(): score += 10
            if needle in code.lower(): score += 5
            if needle in chapter.lower(): score += 2
            if score:
                results.append({
                    "profession": profession,
                    "profession_name": PROFESSION_MAP[profession],
                    "prefix": prefix,
                    "score": score,
                    **item,
                })
    results.sort(key=lambda row: (-row["score"], str(row.get("deh", ""))))
    return results[: max(1, min(int(top_k), 100))]


def get_quota_by_code(code: str, profession: str | None = None, data_dir: Path | None = None) -> dict | None:
    root = (data_dir or quota_data_dir()).resolve()
    selected = [profession] if profession else list(PROFESSION_MAP)
    for prof in selected:
        if prof not in PROFESSION_MAP:
            continue
        try:
            data = _load_profession(str(root), prof)
        except FileNotFoundError:
            continue
        for prefix, item in _iter_items(data):
            if str(item.get("deh", "")) == code:
                return {
                    "profession": prof,
                    "profession_name": PROFESSION_MAP[prof],
                    "prefix": prefix,
                    **item,
                }
    return None


def clear_quota_cache() -> None:
    _load_profession.cache_clear()
