#!/usr/bin/env python3
"""
市政工程造价计算器 (Civil Engineering Cost Calculator)

功能:
1. 道路工程造价计算
2. 桥梁工程造价计算
3. 管网工程造价计算
4. 定额套用与价格分析
5. 造价预算书生成

地区：重庆
定额：2018/2020 版
作者：太一 AGI
创建：2026-04-10
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class CostResult:
    """造价计算结果"""
    project_type: str
    total_cost: float
    unit_price: float
    breakdown: Dict[str, float]
    quantities: Dict[str, float]
    currency: str = "CNY"
    region: str = ""
    standard: str = ""
    calculated_at: str = ""
    
    def __post_init__(self):
        if not self.calculated_at:
            self.calculated_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "project_type": self.project_type,
            "total_cost": round(self.total_cost, 2),
            "unit_price": round(self.unit_price, 2),
            "breakdown": {k: round(v, 2) for k, v in self.breakdown.items()},
            "quantities": {k: round(v, 2) for k, v in self.quantities.items()},
            "currency": self.currency,
            "region": self.region,
            "standard": self.standard,
            "calculated_at": self.calculated_at
        }


# ═══════════════════════════════════════════════════════════
# 定额数据库 (重庆地区 2018/2020 版)
# ═══════════════════════════════════════════════════════════

QUOTAS = {
    "road": {
        # 2018 定额
        "路基土方": {"unit": "1000m³", "labor": 2400, "material": 0, "machine": 8000},
        "路基石方": {"unit": "1000m³", "labor": 3000, "material": 1400, "machine": 11500},
        "沥青混凝土路面": {"unit": "1000㎡", "labor": 1700, "material": 82000, "machine": 3300},
        "水泥混凝土路面": {"unit": "1000㎡", "labor": 2100, "material": 70000, "machine": 4000},
        "路缘石": {"unit": "100m", "labor": 750, "material": 3300, "machine": 180},
        # 2020 定额 (备用)
        "路基土方_2020": {"unit": "1000m³", "labor": 2500, "material": 0, "machine": 8500},
        "沥青混凝土路面_2020": {"unit": "1000㎡", "labor": 1800, "material": 85000, "machine": 3500},
    },
    "bridge": {
        # 2018 定额
        "钻孔灌注桩": {"unit": "10m³", "labor": 4300, "material": 7800, "machine": 12000},
        "预应力混凝土简支梁": {"unit": "10m³", "labor": 3600, "material": 15000, "machine": 5000},
        "预应力混凝土梁": {"unit": "10m³", "labor": 3600, "material": 15000, "machine": 5000},
        "桥面铺装": {"unit": "100㎡", "labor": 1100, "material": 18000, "machine": 2600},
        # 2020 定额 (备用)
        "钻孔灌注桩_2020": {"unit": "10m³", "labor": 4500, "material": 8200, "machine": 12500},
    },
    "pipeline": {
        # 2018 定额
        "HDPE 双壁波纹管 DN500": {"unit": "100m", "labor": 2600, "material": 33000, "machine": 4200},
        "HDPE 双壁波纹管 DN800": {"unit": "100m", "labor": 3300, "material": 55000, "machine": 5800},
        "HDPE 管道 DN500": {"unit": "100m", "labor": 2600, "material": 33000, "machine": 4200},
        "HDPE 管道 DN800": {"unit": "100m", "labor": 3300, "material": 55000, "machine": 5800},
        "检查井": {"unit": "座", "labor": 1700, "material": 3000, "machine": 750},
        # 2020 定额 (备用)
        "HDPE 管道 DN800_2020": {"unit": "100m", "labor": 3500, "material": 58000, "machine": 6200},
    }
}


# ═══════════════════════════════════════════════════════════
# 计算器核心
# ═══════════════════════════════════════════════════════════

class CostCalculator:
    """工程造价计算器"""
    
    def __init__(self, region: str = "重庆", standard: str = "2018 定额"):
        self.region = region
        self.standard = standard
        # 重庆地区费用标准
        self.tax_rate = 0.09  # 增值税 9%
        self.regulation_rate = 0.28  # 规费 28%(人工费)
        self.measure_rate = 0.025  # 措施费 2.5%(市政工程)
        self.safety_rate = 0.025  # 安全文明施工费 2.5%
        
        # 地区调整系数
        self.region_factors = {
            "重庆": {"labor": 1.05, "material": 1.02, "machine": 1.08},
            "上海": {"labor": 1.15, "material": 1.05, "machine": 1.10},
            "北京": {"labor": 1.12, "material": 1.03, "machine": 1.08},
            "广州": {"labor": 1.10, "material": 1.04, "machine": 1.06},
            "成都": {"labor": 1.00, "material": 1.00, "machine": 1.00},
        }
    
    def calculate_road(self, length: float, width: float, structure: str, grade: str = "城市主干路") -> CostResult:
        """计算道路工程造价"""
        area = length * width
        
        quantities = {
            "路基土石方": length * width * 0.5 / 1000,
            structure: area / 1000,
            "路缘石": length * 2 / 100,
        }
        
        direct_cost = self._calculate_direct_cost(quantities, "road")
        breakdown = self._calculate_breakdown(direct_cost)
        total_cost = sum(breakdown.values())
        
        return CostResult(
            project_type="道路工程",
            total_cost=total_cost,
            unit_price=total_cost / area if area > 0 else 0,
            breakdown=breakdown,
            quantities=quantities,
            region=self.region,
            standard=self.standard
        )
    
    def calculate_bridge(self, span: float, width: float, structure: str, foundation: str = "钻孔灌注桩") -> CostResult:
        """计算桥梁工程造价"""
        area = span * width
        
        quantities = {
            foundation: span * width * 0.3 / 10,
            structure: span * width * 0.2 / 10,
            "桥面铺装": area / 100,
        }
        
        direct_cost = self._calculate_direct_cost(quantities, "bridge")
        breakdown = self._calculate_breakdown(direct_cost)
        total_cost = sum(breakdown.values())
        
        return CostResult(
            project_type="桥梁工程",
            total_cost=total_cost,
            unit_price=total_cost / area if area > 0 else 0,
            breakdown=breakdown,
            quantities=quantities,
            region=self.region,
            standard=self.standard
        )
    
    def calculate_pipeline(self, diameter: str, length: float, material: str, depth: float = 2.5) -> CostResult:
        """计算管网工程造价"""
        quantities = {
            f"{material} {diameter}": length / 100,
            "沟槽土石方": length * 1.5 * depth / 1000,
            "回填": length * 1.2 * depth / 1000,
            "检查井": max(1, int(length / 50)),
        }
        
        direct_cost = self._calculate_direct_cost(quantities, "pipeline")
        breakdown = self._calculate_breakdown(direct_cost)
        total_cost = sum(breakdown.values())
        
        return CostResult(
            project_type="管网工程",
            total_cost=total_cost,
            unit_price=total_cost / length if length > 0 else 0,
            breakdown=breakdown,
            quantities=quantities,
            region=self.region,
            standard=self.standard
        )
    
    def _calculate_direct_cost(self, quantities: Dict[str, float], category: str) -> float:
        """计算直接工程费"""
        direct_cost = 0
        factor = self.region_factors.get(self.region, {"labor": 1.0, "material": 1.0, "machine": 1.0})
        
        for item, qty in quantities.items():
            quota_key = item
            if quota_key not in QUOTAS.get(category, {}) and f"{item}_2020" in QUOTAS.get(category, {}):
                quota_key = f"{item}_2020"
            
            if quota_key in QUOTAS.get(category, {}):
                quota = QUOTAS[category][quota_key]
                unit_price = (
                    quota["labor"] * factor["labor"] +
                    quota["material"] * factor["material"] +
                    quota["machine"] * factor["machine"]
                )
                direct_cost += qty * unit_price
        
        return direct_cost
    
    def _calculate_breakdown(self, direct_cost: float) -> Dict[str, float]:
        """计算费用组成 (重庆地区标准)"""
        breakdown = {
            "分部分项工程费": direct_cost,
            "措施项目费": direct_cost * self.measure_rate,
            "安全文明施工费": direct_cost * self.safety_rate,
            "其他项目费": direct_cost * 0.02,
            "规费": direct_cost * self.regulation_rate,
        }
        subtotal = sum(breakdown.values())
        breakdown["税金"] = subtotal * self.tax_rate
        return breakdown


# ═══════════════════════════════════════════════════════════
# 输出格式化
# ═══════════════════════════════════════════════════════════

class OutputFormatter:
    """输出格式化器"""
    
    @staticmethod
    def format_console(result: CostResult) -> str:
        """控制台格式"""
        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║  📊 市政工程造价预算书                                    ║",
            f"║  工程类型：{result.project_type:<24}║",
            f"║  地区：{result.region:<28}║",
            f"║  定额标准：{result.standard:<24}║",
            "╠═══════════════════════════════════════════════════════════╣",
        ]
        
        for item, value in result.breakdown.items():
            lines.append(f"║  {item:<20}¥ {value:>12,.2f}                   ║")
        
        lines.extend([
            "╠═══════════════════════════════════════════════════════════╣",
            f"║  总造价                ¥ {result.total_cost:>12,.2f}                   ║",
            f"║  单位造价              ¥ {result.unit_price:>12,.2f} /单位                  ║",
            "╚═══════════════════════════════════════════════════════════╝",
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_json(result: CostResult, indent: int = 2) -> str:
        """JSON 格式"""
        return json.dumps(result.to_dict(), indent=indent, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="📊 市政工程造价计算器")
    parser.add_argument("--type", "-t", required=True, choices=["road", "bridge", "pipeline"], help="工程类型")
    parser.add_argument("--output", "-o", default="console", choices=["console", "json"], help="输出格式")
    parser.add_argument("--region", "-r", default="重庆", help="地区")
    parser.add_argument("--standard", "-s", default="2018 定额", help="定额标准")
    
    # 道路工程参数
    parser.add_argument("--length", "-l", type=float, help="长度 (米)")
    parser.add_argument("--width", "-w", type=float, help="宽度 (米)")
    parser.add_argument("--structure", type=str, help="结构类型")
    parser.add_argument("--grade", type=str, default="城市主干路", help="道路等级")
    
    # 桥梁工程参数
    parser.add_argument("--span", type=float, help="跨径 (米)")
    parser.add_argument("--foundation", type=str, default="钻孔灌注桩", help="基础类型")
    
    # 管网工程参数
    parser.add_argument("--diameter", type=str, help="管径 (DNxxx)")
    parser.add_argument("--material", type=str, default="HDPE 双壁波纹管", help="管材类型")
    parser.add_argument("--depth", type=float, default=2.5, help="埋深 (米)")
    
    args = parser.parse_args()
    
    calc = CostCalculator(region=args.region, standard=args.standard)
    
    if args.type == "road":
        if not all([args.length, args.width, args.structure]):
            print("❌ 道路工程需要 --length, --width, --structure 参数")
            return 1
        result = calc.calculate_road(args.length, args.width, args.structure, args.grade)
    
    elif args.type == "bridge":
        if not all([args.span, args.width, args.structure]):
            print("❌ 桥梁工程需要 --span, --width, --structure 参数")
            return 1
        result = calc.calculate_bridge(args.span, args.width, args.structure, args.foundation)
    
    elif args.type == "pipeline":
        if not all([args.diameter, args.length]):
            print("❌ 管网工程需要 --diameter, --length 参数")
            return 1
        result = calc.calculate_pipeline(args.diameter, args.length, args.material, args.depth)
    
    if args.output == "json":
        print(OutputFormatter.format_json(result))
    else:
        print(OutputFormatter.format_console(result))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
