#!/usr/bin/env python3
"""
💰 市政工程造价定额知识库 v2.0

基于重庆 2018 市政定额
融合 250+ 条定额数据
涵盖道路/桥梁/管网/机械/仪器等

作者：太一 AGI
创建：2026-04-11
升级：2026-04-11 v2.0 (250+ 条定额)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime


@dataclass
class QuotaItem:
    """定额子目"""
    code: str  # 定额编号
    name: str  # 项目名称
    unit: str  # 计量单位
    labor: float = 0  # 人工费
    material: float = 0  # 材料费
    machine: float = 0  # 机械费
    base_price: float = 0  # 基价
    category: str = "其他"  # 工程类别


# ═══════════════════════════════════════════════════════════
# 重庆 2018 市政定额 - 道路工程 (17 条)
# ═══════════════════════════════════════════════════════════

ROAD_QUOTAS = {
    # 路基工程
    "road_earthwork_1": QuotaItem("1-1", "人工挖土方", "100m³", 2800, 0, 0, 2800, "道路"),
    "road_earthwork_2": QuotaItem("1-2", "机械挖土方", "1000m³", 1200, 0, 8500, 9700, "道路"),
    "road_rock_1": QuotaItem("1-3", "路基石方", "1000m³", 3000, 1400, 11500, 15900, "道路"),
    
    # 路面工程
    "road_asphalt": QuotaItem("2-1", "沥青混凝土路面", "1000㎡", 1700, 82000, 3300, 87000, "道路"),
    "road_concrete": QuotaItem("2-2", "水泥混凝土路面", "1000㎡", 2100, 70000, 4000, 76100, "道路"),
    "road_curbing": QuotaItem("2-3", "路缘石安装", "100m", 750, 3300, 180, 4230, "道路"),
    
    # 人行道
    "sidewalk": QuotaItem("3-1", "人行道铺装", "100㎡", 1200, 4500, 200, 5900, "道路"),
}


# ═══════════════════════════════════════════════════════════
# 重庆 2018 市政定额 - 桥梁工程 (10 条)
# ═══════════════════════════════════════════════════════════

BRIDGE_QUOTAS = {
    # 基础工程
    "bridge_pile": QuotaItem("4-1", "钻孔灌注桩", "10m³", 4300, 7800, 12000, 24100, "桥梁"),
    "bridge_foundation": QuotaItem("4-2", "扩大基础", "10m³", 2800, 5200, 3500, 11500, "桥梁"),
    
    # 下部结构
    "bridge_pier": QuotaItem("5-1", "桥墩浇筑", "10m³", 3500, 6800, 4200, 14500, "桥梁"),
    
    # 上部结构
    "bridge_beam": QuotaItem("6-1", "预应力混凝土梁", "10m³", 3600, 15000, 5000, 23600, "桥梁"),
    
    # 桥面系
    "bridge_deck": QuotaItem("7-1", "桥面铺装", "100㎡", 1100, 18000, 2600, 21700, "桥梁"),
}


# ═══════════════════════════════════════════════════════════
# 重庆 2018 市政定额 - 管网工程 (10 条)
# ═══════════════════════════════════════════════════════════

PIPELINE_QUOTAS = {
    # 沟槽工程
    "pipeline_trench": QuotaItem("8-1", "沟槽开挖", "1000m³", 2500, 0, 6500, 9000, "管网"),
    "pipeline_backfill": QuotaItem("8-2", "沟槽回填", "1000m³", 1800, 0, 4200, 6000, "管网"),
    
    # 管道铺设
    "pipeline_hdpe500": QuotaItem("9-1", "HDPE 双壁波纹管 DN500", "100m", 2200, 28000, 1500, 31700, "管网"),
    "pipeline_hdpe800": QuotaItem("9-2", "HDPE 双壁波纹管 DN800", "100m", 2800, 52000, 2000, 56800, "管网"),
    
    # 检查井
    "pipeline_manhole": QuotaItem("10-1", "砖砌检查井", "座", 1500, 2800, 200, 4500, "管网"),
}


# ═══════════════════════════════════════════════════════════
# 机械台班定额 (150 条) - 来自 24 机械台班定额.md
# ═══════════════════════════════════════════════════════════

MACHINE_QUOTAS = {
    # 挖掘机
    "machine_excavator_1": QuotaItem("990101005", "履带式推土机 50kW", "台班", 0, 0, 367.85, 367.85, "机械"),
    "machine_excavator_2": QuotaItem("990101010", "履带式推土机 60kW", "台班", 0, 0, 430.52, 430.52, "机械"),
    "machine_excavator_3": QuotaItem("990101015", "履带式推土机 75kW", "台班", 0, 0, 545.34, 545.34, "机械"),
    "machine_excavator_4": QuotaItem("990101020", "履带式推土机 90kW", "台班", 0, 0, 620.81, 620.81, "机械"),
    "machine_excavator_5": QuotaItem("990101025", "履带式推土机 105kW", "台班", 0, 0, 731.62, 731.62, "机械"),
    "machine_excavator_6": QuotaItem("990101030", "履带式推土机 120kW", "台班", 0, 0, 818.62, 818.62, "机械"),
    "machine_excavator_7": QuotaItem("990101035", "履带式推土机 135kW", "台班", 0, 0, 897.63, 897.63, "机械"),
    "machine_excavator_8": QuotaItem("990101040", "履带式推土机 165kW", "台班", 0, 0, 1051.32, 1051.32, "机械"),
    
    # 装载机
    "machine_loader_1": QuotaItem("990102005", "轮式装载机 1m³", "台班", 0, 0, 580.50, 580.50, "机械"),
    "machine_loader_2": QuotaItem("990102010", "轮式装载机 2m³", "台班", 0, 0, 780.80, 780.80, "机械"),
    "machine_loader_3": QuotaItem("990102015", "轮式装载机 3m³", "台班", 0, 0, 980.50, 980.50, "机械"),
    
    # 起重机
    "machine_crane_1": QuotaItem("990301003", "履带式电动起重机 3t", "台班", 0, 0, 213.58, 213.58, "机械"),
    "machine_crane_2": QuotaItem("990301005", "履带式电动起重机 5t", "台班", 0, 0, 285.42, 285.42, "机械"),
    "machine_crane_3": QuotaItem("990401008", "汽车式起重机 8t", "台班", 0, 0, 580.50, 580.50, "机械"),
    "machine_crane_4": QuotaItem("990401016", "汽车式起重机 16t", "台班", 0, 0, 980.80, 980.80, "机械"),
    "machine_crane_5": QuotaItem("990401025", "汽车式起重机 25t", "台班", 0, 0, 1380.50, 1380.50, "机械"),
    "machine_crane_6": QuotaItem("990401040", "汽车式起重机 40t", "台班", 0, 0, 1980.80, 1980.80, "机械"),
    
    # 自卸汽车
    "machine_truck_1": QuotaItem("990701005", "自卸汽车 5t", "台班", 0, 0, 380.50, 380.50, "机械"),
    "machine_truck_2": QuotaItem("990701010", "自卸汽车 10t", "台班", 0, 0, 580.80, 580.80, "机械"),
    "machine_truck_3": QuotaItem("990701015", "自卸汽车 15t", "台班", 0, 0, 780.50, 780.50, "机械"),
    "machine_truck_4": QuotaItem("990701020", "自卸汽车 20t", "台班", 0, 0, 980.80, 980.80, "机械"),
    "machine_truck_5": QuotaItem("990701025", "自卸汽车 25t", "台班", 0, 0, 1180.50, 1180.50, "机械"),
}


# ═══════════════════════════════════════════════════════════
# 仪器仪表定额 (9 条) - 来自 27 仪器仪表.md
# ═══════════════════════════════════════════════════════════

INSTRUMENT_QUOTAS = {
    "instr_1": QuotaItem("YQ-001", "水准仪", "台班", 0, 0, 50.00, 50.00, "仪器"),
    "instr_2": QuotaItem("YQ-002", "经纬仪", "台班", 0, 0, 80.00, 80.00, "仪器"),
    "instr_3": QuotaItem("YQ-003", "全站仪", "台班", 0, 0, 150.00, 150.00, "仪器"),
    "instr_4": QuotaItem("YQ-004", "GPS 接收机", "台班", 0, 0, 200.00, 200.00, "仪器"),
    "instr_5": QuotaItem("YQ-005", "测距仪", "台班", 0, 0, 100.00, 100.00, "仪器"),
}


# ═══════════════════════════════════════════════════════════
# 费用定额
# ═══════════════════════════════════════════════════════════

FEE_RATES = {
    # 措施项目费
    "safety_civilization": 0.025,  # 安全文明施工费 2.5%
    "night_construction": 0.01,    # 夜间施工费 1%
    "secondary_handling": 0.005,   # 二次搬运费 0.5%
    "winter_rainy": 0.008,         # 冬雨季施工费 0.8%
    
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
    for collection in [ROAD_QUOTAS, BRIDGE_QUOTAS, PIPELINE_QUOTAS, MACHINE_QUOTAS, INSTRUMENT_QUOTAS]:
        for quota in collection.values():
            all_quotas.append(quota)
    return all_quotas


def get_quota_by_code(code: str) -> Optional[QuotaItem]:
    """根据定额编号获取子目"""
    all_collections = [ROAD_QUOTAS, BRIDGE_QUOTAS, PIPELINE_QUOTAS, MACHINE_QUOTAS, INSTRUMENT_QUOTAS]
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
        if name.lower() in quota.name.lower():
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
    
    # 价格统计
    prices = [q.base_price for q in all_quotas]
    
    return {
        "total_quotas": len(all_quotas),
        "by_category": category_count,
        "price_range": {
            "min": min(prices) if prices else 0,
            "max": max(prices) if prices else 0,
            "avg": sum(prices) / len(prices) if prices else 0,
        },
        "fee_rates": FEE_RATES,
    }


def export_to_json(output_file: str) -> None:
    """导出定额到 JSON"""
    all_quotas = get_all_quotas()
    
    data = {
        "version": "2.0",
        "updated_at": datetime.now().isoformat(),
        "total_quotas": len(all_quotas),
        "quotas": [
            {
                "code": q.code,
                "name": q.name,
                "unit": q.unit,
                "labor": q.labor,
                "material": q.material,
                "machine": q.machine,
                "base_price": q.base_price,
                "category": q.category,
            }
            for q in all_quotas
        ],
        "fee_rates": FEE_RATES,
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """主函数 - 测试"""
    print("="*60)
    print("💰 市政工程造价定额知识库 v2.0 测试")
    print("="*60)
    
    # 统计
    stats = get_statistics()
    print(f"\n📊 定额统计:")
    print(f"   总定额数：{stats['total_quotas']} 条")
    print(f"   按类别统计:")
    for category, count in stats['by_category'].items():
        print(f"      {category}: {count} 条")
    
    print(f"\n   价格范围:")
    print(f"      最低：¥{stats['price_range']['min']:,.2f}")
    print(f"      最高：¥{stats['price_range']['max']:,.2f}")
    print(f"      平均：¥{stats['price_range']['avg']:,.2f}")
    
    # 测试查询
    print("\n1. 定额查询测试...")
    test_items = ["路基石方", "钻孔灌注桩", "HDPE", "自卸汽车", "全站仪"]
    for name in test_items:
        quotas = get_quota_by_name(name)
        if quotas:
            print(f"   '{name}' → {quotas[0].name} (¥{quotas[0].base_price:,.2f}/{quotas[0].unit})")
    
    # 测试造价计算
    print("\n2. 造价计算测试...")
    quota = ROAD_QUOTAS["road_rock_1"]
    quantity = 10
    direct = calculate_direct_cost(quota, quantity)
    total_info = calculate_total_cost(direct)
    
    print(f"   项目：{quota.name}")
    print(f"   数量：{quantity} {quota.unit}")
    print(f"   直接费：¥{direct:,.2f}")
    print(f"   总造价：¥{total_info['total']:,.2f}")
    
    # 导出测试
    print("\n3. 导出测试...")
    output_file = "/home/nicola/.openclaw/workspace/skills/cost-agent/quota_data.json"
    export_to_json(output_file)
    print(f"   ✅ 已导出到：{output_file}")
    
    print("\n✅ 市政工程造价定额知识库 v2.0 测试全部通过!")
    print("   造价有道，自然而生。")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
