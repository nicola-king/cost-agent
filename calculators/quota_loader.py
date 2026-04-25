#!/usr/bin/env python3
"""
统一定额数据加载器
=================
从 data/quotas/ 目录加载所有定额数据，提供统一接口。

支持模块:
- knowledge/matcher.py (定额匹配)
- calculators/cost.py (造价计算)
- calculators/quota_database.py (定额查询)
- core/self_evolution_impl.py (自进化)

作者：太一 AGI
创建：2026-04-25
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 定额数据目录
QUOTA_DATA_DIR = Path(__file__).parent.parent / "data" / "quotas"

# 专业映射
PROFESSION_MAP = {
    "building": "建筑工程",
    "decoration": "装饰装修",
    "installation": "安装工程",
    "municipal": "市政工程",
    "prefab": "装配式建筑",
    "transit": "轨道交通",
}

# 缓存
_quota_cache: Dict[str, dict] = {}


def get_quota_data(profession: Optional[str] = None) -> Dict[str, dict]:
    """
    获取定额数据
    
    Args:
        profession: 专业名称 (building/decoration/installation/municipal/prefab/transit)
                   如果为 None，返回所有专业数据
    
    Returns:
        {profession: {prefixes: {...}, total: int, category: str}}
    """
    if profession:
        return _load_single(profession)
    
    result = {}
    for prof in PROFESSION_MAP:
        result[prof] = _load_single(prof)
    return result


def _load_single(profession: str) -> dict:
    """加载单个专业数据（带缓存）"""
    if profession in _quota_cache:
        return _quota_cache[profession]
    
    filepath = QUOTA_DATA_DIR / f"{profession}.json"
    if not filepath.exists():
        raise FileNotFoundError(f"定额数据文件不存在: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    _quota_cache[profession] = data
    return data


def search_quota(keyword: str, top_k: int = 10, professions: Optional[List[str]] = None) -> List[dict]:
    """
    搜索定额
    
    Args:
        keyword: 搜索关键词
        top_k: 返回结果数量
        professions: 搜索的专业列表，None 表示全部
    
    Returns:
        匹配的定额列表
    """
    if professions is None:
        professions = list(PROFESSION_MAP.keys())
    
    results = []
    keyword_lower = keyword.lower()
    
    for prof in professions:
        data = get_quota_data(prof)
        for prefix, items in data.get("prefixes", {}).items():
            for item in items:
                # 多字段匹配
                score = 0
                name = item.get("xmmc", "")
                code = item.get("deh", "")
                chapter = item.get("chapter", "")
                
                if keyword_lower in name.lower():
                    score += 10
                if keyword_lower in code.lower():
                    score += 5
                if keyword_lower in chapter.lower():
                    score += 2
                
                if score > 0:
                    results.append({
                        "profession": prof,
                        "profession_name": PROFESSION_MAP[prof],
                        "prefix": prefix,
                        "score": score,
                        **item,
                    })
    
    # 按分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def get_quota_by_code(code: str, profession: Optional[str] = None) -> Optional[dict]:
    """
    按定额编号查询
    
    Args:
        code: 定额编号 (如 AA0001)
        profession: 专业，None 表示全部搜索
    
    Returns:
        定额数据或 None
    """
    if profession:
        data = get_quota_data(profession)
        return _find_by_code(data, code)
    
    for prof in PROFESSION_MAP:
        data = get_quota_data(prof)
        result = _find_by_code(data, code)
        if result:
            return result
    
    return None


def _find_by_code(data: dict, code: str) -> Optional[dict]:
    """在数据中查找定额编号"""
    for prefix, items in data.get("prefixes", {}).items():
        for item in items:
            if item.get("deh") == code:
                return item
    return None


def get_stats() -> Dict[str, dict]:
    """获取定额数据统计"""
    stats = {}
    for prof in PROFESSION_MAP:
        try:
            data = get_quota_data(prof)
            stats[prof] = {
                "name": PROFESSION_MAP[prof],
                "total": data.get("total", 0),
                "prefixes": len(data.get("prefixes", {})),
                "file_size": os.path.getsize(QUOTA_DATA_DIR / f"{prof}.json"),
            }
        except FileNotFoundError:
            stats[prof] = {"name": PROFESSION_MAP[prof], "error": "文件不存在"}
    
    return stats


def clear_cache():
    """清除缓存"""
    _quota_cache.clear()


# 便捷函数
def load_all() -> Dict[str, dict]:
    """加载所有定额数据"""
    return get_quota_data()


def get_professions() -> List[str]:
    """获取所有专业列表"""
    return list(PROFESSION_MAP.keys())


def get_profession_name(profession: str) -> str:
    """获取专业中文名称"""
    return PROFESSION_MAP.get(profession, profession)


if __name__ == "__main__":
    # 测试
    print("=== 定额数据加载器测试 ===")
    stats = get_stats()
    for prof, s in stats.items():
        if "error" not in s:
            print(f"{s['name']:12s} {s['total']:>6} 条 {s['prefixes']:>2} 章 {s['file_size']/1024/1024:.1f}MB")
    
    print("\n=== 搜索测试 ===")
    results = search_quota("人工平整场地", top_k=3)
    for r in results:
        print(f"  [{r['profession_name']}] {r['deh']} {r['xmmc']} (得分:{r['score']})")
