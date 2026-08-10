from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from typing import Iterator

_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _col_index(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def read_xlsx_rows(path: str | Path, sheet_name: str | None = None) -> Iterator[list[object]]:
    with ZipFile(Path(path)) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("a:si", _NS):
                shared.append("".join((t.text or "") for t in si.iterfind(".//a:t", _NS)))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rel_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels.findall("pr:Relationship", _NS)}
        sheets = []
        for s in wb.findall("a:sheets/a:sheet", _NS):
            rid = s.attrib[f"{{{_NS['r']}}}id"]
            target = rel_map[rid]
            if not target.startswith("xl/"):
                target = f"xl/{target.lstrip('/')}"
            sheets.append((s.attrib["name"], target))
        if not sheets:
            return
        chosen = next((x for x in sheets if sheet_name and x[0] == sheet_name), sheets[0])
        root = ET.fromstring(z.read(chosen[1]))
        for row in root.findall("a:sheetData/a:row", _NS):
            vals: dict[int, object] = {}
            max_col = -1
            for c in row.findall("a:c", _NS):
                idx = _col_index(c.attrib.get("r", "A1")); max_col = max(max_col, idx)
                typ = c.attrib.get("t"); v = c.find("a:v", _NS); inline = c.find("a:is", _NS)
                value: object = None
                if typ == "s" and v is not None and v.text is not None:
                    value = shared[int(v.text)]
                elif typ == "inlineStr" and inline is not None:
                    value = "".join((t.text or "") for t in inline.iterfind(".//a:t", _NS))
                elif v is not None and v.text is not None:
                    raw = v.text
                    try:
                        f = float(raw); value = int(f) if f.is_integer() else f
                    except ValueError:
                        value = raw
                vals[idx] = value
            if max_col >= 0:
                yield [vals.get(i) for i in range(max_col + 1)]


def normalize_header(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "").replace("\n", "")


def map_boq_rows(rows: list[list[object]], header_row: int = 1) -> list[dict]:
    if not rows or header_row < 1 or header_row > len(rows):
        return []
    headers = [normalize_header(x) for x in rows[header_row - 1]]
    aliases = {
        "code": {"项目编码", "清单编码", "编码"},
        "name": {"项目名称", "清单项目名称", "名称"},
        "description": {"项目特征描述", "项目特征", "特征描述"},
        "unit": {"计量单位", "单位"},
        "award_quantity": {"工程量", "数量", "清单工程量"},
        "award_unit_price": {"综合单价", "单价", "中标单价"},
    }
    index = {}
    for key, names in aliases.items():
        for i, h in enumerate(headers):
            if h in names:
                index[key] = i; break
    if "name" not in index or "unit" not in index:
        raise ValueError("required BOQ columns not found")
    out = []
    for row in rows[header_row:]:
        def get(key):
            i = index.get(key); return row[i] if i is not None and i < len(row) else None
        name = str(get("name") or "").strip(); unit = str(get("unit") or "").strip()
        if not name or not unit:
            continue
        def num(v):
            if v in (None, ""): return None
            return float(v)
        out.append({
            "code": str(get("code") or "").strip() or None,
            "name": name,
            "description": str(get("description") or "").strip() or None,
            "unit": unit,
            "award_quantity": num(get("award_quantity")),
            "award_unit_price": num(get("award_unit_price")),
        })
    return out
