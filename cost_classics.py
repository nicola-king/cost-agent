#!/usr/bin/env python3
"""
💰 市政工程造价定额知识库

基于重庆 2018 市政定额
涵盖道路/桥梁/管网工程

作者：太一 AGI
创建：2026-04-11
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class QuotaItem:
    """定额子目"""
    code: str  # 定额编号
    name: str  # 项目名称
    unit: str  # 计量单位
    labor: float  # 人工费
    material: float  # 材料费
    machine: float  # 机械费
    base_price: float  # 基价
    category: str  # 工程类别 (道路/桥梁/管网)


# ═══════════════════════════════════════════════════════════
# 重庆 2018 市政定额 - 道路工程
# ═══════════════════════════════════════════════════════════

ROAD_QUOTAS = {
    # ───────────────────────────────────────────────────────
    # 路基工程
    # ───────────────────────────────────────────────────────
    "road_earthwork_1": QuotaItem(
        code="1-1",
        name="人工挖土方",
        unit="100m³",
        labor=2800,
        material=0,
        machine=0,
        base_price=2800,
        category="道路"
    ),
    
    "road_earthwork_2": QuotaItem(
        code="1-2",
        name="机械挖土方",
        unit="1000m³",
        labor=1200,
        material=0,
        machine=8500,
        base_price=9700,
        category="道路"
    ),
    
    "road_rock_1": QuotaItem(
        code="1-3",
        name="路基石方",
        unit="1000m³",
        labor=3000,
        material=1400,
        machine=11500,
        base_price=15900,
        category="道路"
    ),
    
    # ───────────────────────────────────────────────────────
    # 路面工程
    # ───────────────────────────────────────────────────────
    "road_surface_1": QuotaItem(
        code="2-1",
        name="沥青混凝土路面",
        unit="1000㎡",
        labor=1700,
        material=82000,
        machine=3300,
        base_price=87000,
        category="道路"
    ),
    
    "road_surface_2": QuotaItem(
        code="2-2",
        name="水泥混凝土路面",
        unit="1000㎡",
        labor=2100,
        material=70000,
        machine=4000,
        base_price=76100,
        category="道路"
    ),
    
    "road_curbing": QuotaItem(
        code="2-3",
        name="路缘石安装",
        unit="100m",
        labor=750,
        material=3300,
        machine=180,
        base_price=4230,
        category="道路"
    ),
    
    # ───────────────────────────────────────────────────────
    # 人行道工程
    # ───────────────────────────────────────────────────────
    "sidewalk_1": QuotaItem(
        code="3-1",
        name="人行道铺装",
        unit="100㎡",
        labor=1200,
        material=4500,
        machine=200,
        base_price=5900,
        category="道路"
    ),
}


# ═══════════════════════════════════════════════════════════
# 重庆 2018 市政定额 - 桥梁工程
# ═══════════════════════════════════════════════════════════

BRIDGE_QUOTAS = {
    # ───────────────────────────────────────────────────────
    # 基础工程
    # ───────────────────────────────────────────────────────
    "bridge_pile_1": QuotaItem(
        code="4-1",
        name="钻孔灌注桩",
        unit="10m³",
        labor=4300,
        material=7800,
        machine=12000,
        base_price=24100,
        category="桥梁"
    ),
    
    "bridge_foundation": QuotaItem(
        code="4-2",
        name="扩大基础",
        unit="10m³",
        labor=2800,
        material=5200,
        machine=3500,
        base_price=11500,
        category="桥梁"
    ),
    
    # ───────────────────────────────────────────────────────
    # 下部结构
    # ───────────────────────────────────────────────────────
    "bridge_pier": QuotaItem(
        code="5-1",
        name="桥墩浇筑",
        unit="10m³",
        labor=3500,
        material=6800,
        machine=4200,
        base_price=14500,
        category="桥梁"
    ),
    
    # ───────────────────────────────────────────────────────
    # 上部结构
    # ───────────────────────────────────────────────────────
    "bridge_beam": QuotaItem(
        code="6-1",
        name="预应力混凝土梁",
        unit="10m³",
        labor=3600,
        material=15000,
        machine=5000,
        base_price=23600,
        category="桥梁"
    ),
    
    # ───────────────────────────────────────────────────────
    # 桥面系
    # ───────────────────────────────────────────────────────
    "bridge_deck": QuotaItem(
        code="7-1",
        name="桥面铺装",
        unit="100㎡",
        labor=1100,
        material=18000,
        machine=2600,
        base_price=21700,
        category="桥梁"
    ),
}


# ═══════════════════════════════════════════════════════════
# 重庆 2018 市政定额 - 管网工程
# ═══════════════════════════════════════════════════════════

PIPELINE_QUOTAS = {
    # ───────────────────────────────────────────────────────
    # 沟槽工程
    # ───────────────────────────────────────────────────────
    "pipeline_trench": QuotaItem(
        code="8-1",
        name="沟槽开挖",
        unit="1000m³",
        labor=2500,
        material=0,
        machine=6500,
        base_price=9000,
        category="管网"
    ),
    
    "pipeline_backfill": QuotaItem(
        code="8-2",
        name="沟槽回填",
        unit="1000m³",
        labor=1800,
        material=0,
        machine=4200,
        base_price=6000,
        category="管网"
    ),
    
    # ───────────────────────────────────────────────────────
    # 管道铺设
    # ───────────────────────────────────────────────────────
    "pipeline_hdpe_500": QuotaItem(
        code="9-1",
        name="HDPE 双壁波纹管 DN500",
        unit="100m",
        labor=2200,
        material=28000,
        machine=1500,
        base_price=31700,
        category="管网"
    ),
    
    "pipeline_hdpe_800": QuotaItem(
        code="9-2",
        name="HDPE 双壁波纹管 DN800",
        unit="100m",
        labor=2800,
        material=52000,
        machine=2000,
        base_price=56800,
        category="管网"
    ),
    
    # ───────────────────────────────────────────────────────
    # 检查井
    # ───────────────────────────────────────────────────────
    "pipeline_manhole": QuotaItem(
        code="10-1",
        name="砖砌检查井",
        unit="座",
        labor=1500,
        material=2800,
        machine=200,
        base_price=4500,
        category="管网"
    ),
}


# ═══════════════════════════════════════════════════════════
# 费用定额
# ═══════════════════════════════════════════════════════════

FEE_RATES = {
    # 措施项目费
    "safety_civilization": 0.025,  # 安全文明施工费 2.5%
    "night_construction": 0.01,    # 夜间施工费 1%
    
    # 其他项目费
    "other_items": 0.02,           # 其他项目费 2%
    
    # 规费
    "social_security": 0.18,       # 社保费 18%
    "housing_fund": 0.10,          # 公积金 10%
    "regulation_total": 0.28,      # 规费合计 28%
    
    # 税金
    "tax_rate": 0.09,              # 增值税 9%
}


# ═══════════════════════════════════════════════════════════
# 核心函数
# ═══════════════════════════════════════════════════════════

def get_all_quotas() -> List[QuotaItem]:
    """获取所有定额子目"""
    all_quotas = []
    for collection in [ROAD_QUOTAS, BRIDGE_QUOTAS, PIPELINE_QUOTAS]:
        for quota in collection.values():
            all_quotas.append(quota)
    return all_quotas


def get_quota_by_code(code: str) -> QuotaItem:
    """根据定额编号获取子目"""
    all_collections = [ROAD_QUOTAS, BRIDGE_QUOTAS, PIPELINE_QUOTAS]
    for collection in all_collections:
        for key, quota in collection.items():
            if quota.code == code:
                return quota
    return None


def get_quota_by_name(name: str) -> List[QuotaItem]:
    """根据名称获取定额子目"""
    result = []
    all_quotas = get_all_quotas()
    for quota in all_quotas:
        if name in quota.name:
            result.append(quota)
    return result


def get_quotas_by_category(category: str) -> List[QuotaItem]:
    """根据工程类别获取定额"""
    all_quotas = get_all_quotas()
    return [q for q in all_quotas if q.category == category]


def calculate_direct_cost(quota: QuotaItem, quantity: float) -> float:
    """计算直接费"""
    return quota.base_price * quantity


def calculate_total_cost(direct_cost: float) -> Dict:
    """计算总造价"""
    measures = direct_cost * FEE_RATES["safety_civilization"]
    other = direct_cost * FEE_RATES["other_items"]
    regulation = direct_cost * FEE_RATES["regulation_total"]
    
    subtotal = direct_cost + measures + other + regulation
    tax = subtotal * FEE_RATES["tax_rate"]
    
    total = subtotal + tax
    
    return {
        "direct_cost": direct_cost,
        "measures": measures,
        "other": other,
        "regulation": regulation,
        "tax": tax,
        "total": total,
    }


def get_statistics() -> Dict:
    """获取统计信息"""
    all_quotas = get_all_quotas()
    
    # 按类别统计
    category_count = {}
    for q in all_quotas:
        if q.category not in category_count:
            category_count[q.category] = 0
        category_count[q.category] += 1
    
    return {
        "total_quotas": len(all_quotas),
        "by_category": category_count,
        "fee_rates": FEE_RATES,
    }


def main():
    """主函数 - 测试"""
    print("💰 市政工程造价定额知识库测试")
    print("="*60)
    
    # 统计
    stats = get_statistics()
    print(f"\n📊 定额统计:")
    print(f"   总定额数：{stats['total_quotas']} 个")
    print(f"   按类别统计:")
    for category, count in stats['by_category'].items():
        print(f"      {category}: {count} 个")
    
    print(f"\n   费用费率:")
    for name, rate in stats['fee_rates'].items():
        print(f"      {name}: {rate:.2%}")
    
    # 测试查询
    print("\n1. 定额查询测试...")
    test_items = ["路基石方", "钻孔灌注桩", "HDPE 双壁波纹管"]
    for name in test_items:
        quotas = get_quota_by_name(name)
        if quotas:
            print(f"   '{name}' → {quotas[0].name} (¥{quotas[0].base_price}/{quotas[0].unit})")
    
    # 测试造价计算
    print("\n2. 造价计算测试...")
    quota = ROAD_QUOTAS["road_rock_1"]
    quantity = 10  # 10 个单位
    direct = calculate_direct_cost(quota, quantity)
    total_info = calculate_total_cost(direct)
    
    print(f"   项目：{quota.name}")
    print(f"   数量：{quantity} {quota.unit}")
    print(f"   直接费：¥{direct:,.2f}")
    print(f"   总造价：¥{total_info['total']:,.2f}")
    
    print("\n✅ 市政工程造价定额知识库测试完成!")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
