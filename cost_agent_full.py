#!/usr/bin/env python3
"""
🏗️ Cost.Agent (造价 Agent)

人法地，地法天，天法道，道法自然。
造价有道，自然而生。

融合重庆 2018 市政定额与太一记忆宫殿
服务市政工程造价全过程

作者：太一 AGI
创建：2026-04-11
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 导入太一记忆宫殿
import sys
sys.path.insert(0, '/home/nicola/.openclaw/workspace/skills/taiyi-memory-palace')
try:
    from memory_system import TaiyiMemoryPalace
    MEMORY_PALACE_AVAILABLE = True
except:
    MEMORY_PALACE_AVAILABLE = False

# 导入定额知识库
from cost_classics import (
    get_all_quotas, get_quota_by_code, get_quota_by_name,
    get_quotas_by_category, calculate_direct_cost, calculate_total_cost,
    get_statistics, ROAD_QUOTAS, BRIDGE_QUOTAS, PIPELINE_QUOTAS, FEE_RATES
)


class CostAgent:
    """🏗️ Cost.Agent - 市政工程造价 Agent"""
    
    def __init__(self, region: str = "重庆", quota_version: str = "2018"):
        self.agent_id = "cost-agent"
        self.version = "1.0.0"
        self.region = region
        self.quota_version = quota_version
        self.created_at = datetime.now()
        
        # 太一记忆宫殿
        if MEMORY_PALACE_AVAILABLE:
            try:
                self.memory_palace = TaiyiMemoryPalace()
                print(f"   ✅ 太一记忆宫殿已加载")
            except Exception as e:
                print(f"   ⚠️  太一记忆宫殿加载失败：{e}")
                self.memory_palace = None
        else:
            self.memory_palace = None
        
        # 自进化数据
        self.evolution_data = {
            "total_projects": 0,
            "unique_users": set(),
            "breakthroughs": [],
            "project_types": {"道路": 0, "桥梁": 0, "管网": 0},
        }
        
        # 数据目录
        self.data_dir = Path(__file__).parent / "cost"
        self.data_dir.mkdir(exist_ok=True)
        
        print(f"🏗️ Cost.Agent 已启动")
        print(f"   地区：{region}")
        print(f"   定额版本：{quota_version}")
        print(f"   道法自然，造价有道。")
        print()
    
    async def quick_estimate(self, project_type: str, **kwargs) -> Dict:
        """
        投资估算 (快速估算)
        
        Args:
            project_type: 项目类型 (道路/桥梁/管网)
            **kwargs: 项目参数
        
        Returns:
            投资估算结果
        """
        print(f"\n🏗️ 投资估算")
        print(f"   项目类型：{project_type}")
        print(f"   参数：{kwargs}")
        
        # 根据项目类型估算
        if project_type == "道路":
            estimate = self._estimate_road(**kwargs)
        elif project_type == "桥梁":
            estimate = self._estimate_bridge(**kwargs)
        elif project_type == "管网":
            estimate = self._estimate_pipeline(**kwargs)
        else:
            estimate = {"error": "未知项目类型"}
        
        # 存储到记忆宫殿
        await self._store_to_memory("estimate", project_type, estimate, kwargs)
        
        return estimate
    
    def _estimate_road(self, length: float, width: float, **kwargs) -> Dict:
        """道路工程估算"""
        area = length * width
        
        # 参考指标 (元/㎡)
        unit_price_range = {
            "min": 800,   # 最低
            "max": 1500,  # 最高
            "avg": 1100,  # 平均
        }
        
        total_estimate = area * unit_price_range["avg"]
        
        return {
            "project_type": "道路工程",
            "scale": f"{length}m × {width}m = {area:,.0f}㎡",
            "unit_price": unit_price_range,
            "total_estimate": total_estimate,
            "precision": "±30%",
            "note": "类似项目造价指标估算",
        }
    
    def _estimate_bridge(self, span: float, width: float, **kwargs) -> Dict:
        """桥梁工程估算"""
        area = span * width
        
        # 参考指标 (元/㎡)
        unit_price_range = {
            "min": 3000,
            "max": 8000,
            "avg": 5000,
        }
        
        total_estimate = area * unit_price_range["avg"]
        
        return {
            "project_type": "桥梁工程",
            "scale": f"{span}m × {width}m = {area:,.0f}㎡",
            "unit_price": unit_price_range,
            "total_estimate": total_estimate,
            "precision": "±30%",
            "note": "类似项目造价指标估算",
        }
    
    def _estimate_pipeline(self, length: float, diameter: str, **kwargs) -> Dict:
        """管网工程估算"""
        # 根据管径确定单价 (元/m)
        unit_prices = {
            "DN500": 3000,
            "DN800": 5500,
            "DN1000": 8000,
            "DN1200": 12000,
        }
        
        unit_price = unit_prices.get(diameter, 5000)
        total_estimate = length * unit_price
        
        return {
            "project_type": "管网工程",
            "scale": f"{length}m ({diameter})",
            "unit_price": unit_price,
            "total_estimate": total_estimate,
            "precision": "±30%",
            "note": "类似项目造价指标估算",
        }
    
    def calculate_quantities(self, project_type: str, **kwargs) -> Dict:
        """
        工程量计算
        
        Args:
            project_type: 项目类型
            **kwargs: 项目参数
        
        Returns:
            工程量清单
        """
        print(f"\n📐 工程量计算")
        print(f"   项目类型：{project_type}")
        
        if project_type == "道路":
            quantities = self._calculate_road_quantities(**kwargs)
        elif project_type == "桥梁":
            quantities = self._calculate_bridge_quantities(**kwargs)
        elif project_type == "管网":
            quantities = self._calculate_pipeline_quantities(**kwargs)
        else:
            quantities = {"error": "未知项目类型"}
        
        return quantities
    
    def _calculate_road_quantities(self, length: float, width: float, **kwargs) -> Dict:
        """道路工程量计算"""
        area = length * width
        
        return {
            "project_type": "道路工程",
            "items": [
                {"name": "路基土石方", "quantity": length * width * 0.5, "unit": "m³"},
                {"name": "路面工程", "quantity": area, "unit": "㎡"},
                {"name": "路缘石", "quantity": length * 2, "unit": "m"},
                {"name": "人行道", "quantity": length * 3 * 2, "unit": "㎡"},
            ],
        }
    
    def _calculate_bridge_quantities(self, span: float, width: float, **kwargs) -> Dict:
        """桥梁工程量计算"""
        area = span * width
        
        return {
            "project_type": "桥梁工程",
            "items": [
                {"name": "钻孔灌注桩", "quantity": span * width * 0.3 / 10, "unit": "10m³"},
                {"name": "桥墩", "quantity": span * width * 0.2 / 10, "unit": "10m³"},
                {"name": "预应力梁", "quantity": span * width * 0.2 / 10, "unit": "10m³"},
                {"name": "桥面铺装", "quantity": area / 100, "unit": "100㎡"},
            ],
        }
    
    def _calculate_pipeline_quantities(self, length: float, diameter: str, **kwargs) -> Dict:
        """管网工程量计算"""
        return {
            "project_type": "管网工程",
            "items": [
                {"name": "沟槽开挖", "quantity": length * 1.5 * 2.5 / 1000, "unit": "1000m³"},
                {"name": f"{diameter}管道铺设", "quantity": length / 100, "unit": "100m"},
                {"name": "沟槽回填", "quantity": length * 1.2 * 2.5 / 1000, "unit": "1000m³"},
                {"name": "检查井", "quantity": max(1, int(length / 50)), "unit": "座"},
            ],
        }
    
    def apply_quota(self, item_name: str, quantity: float) -> Dict:
        """
        定额套用
        
        Args:
            item_name: 定额项目名称
            quantity: 数量
        
        Returns:
            定额计价结果
        """
        print(f"\n💰 定额套用")
        print(f"   项目：{item_name}")
        print(f"   数量：{quantity}")
        
        # 查找定额
        quotas = get_quota_by_name(item_name)
        if not quotas:
            return {"error": f"未找到定额：{item_name}"}
        
        quota = quotas[0]
        
        # 计算
        direct_cost = calculate_direct_cost(quota, quantity)
        total_info = calculate_total_cost(direct_cost)
        
        return {
            "quota_code": quota.code,
            "quota_name": quota.name,
            "unit": quota.unit,
            "quantity": quantity,
            "base_price": quota.base_price,
            "direct_cost": direct_cost,
            "total_cost": total_info["total"],
            "breakdown": total_info,
        }
    
    async def _store_to_memory(self, operation: str, project_type: str, result: Dict, params: Dict):
        """存储到太一记忆宫殿"""
        if not self.memory_palace:
            return
        
        # 存储项目记录
        record = f"[{operation}] {project_type}: {result}"
        self.memory_palace.remember(
            text=record,
            category="projects",
            metadata={"operation": operation, "project_type": project_type}
        )
        
        # 更新进化数据
        self.evolution_data["total_projects"] += 1
        self.evolution_data["unique_users"].add("default_user")
        if project_type in self.evolution_data["project_types"]:
            self.evolution_data["project_types"][project_type] += 1
    
    def get_stats(self) -> Dict:
        """获取系统统计"""
        quota_stats = get_statistics()
        
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "region": self.region,
            "quota_version": self.quota_version,
            "total_projects": self.evolution_data["total_projects"],
            "quota_stats": quota_stats,
            "memory_palace": "loaded" if self.memory_palace else "not_loaded",
        }


async def main():
    """主函数 - 演示"""
    print("="*60)
    print("🏗️ Cost.Agent (造价 Agent)")
    print("   人法地，地法天，天法道，道法自然。")
    print("   造价有道，自然而生。")
    print("="*60)
    
    agent = CostAgent(region="重庆", quota_version="2018")
    
    # 演示 1: 投资估算
    print("\n📊 演示 1: 投资估算")
    estimate = await agent.quick_estimate(
        project_type="道路",
        length=1000,
        width=20
    )
    print(f"   估算结果：¥{estimate.get('total_estimate', 0):,.2f}")
    
    # 演示 2: 工程量计算
    print("\n📐 演示 2: 工程量计算")
    quantities = agent.calculate_quantities(
        project_type="道路",
        length=1000,
        width=20
    )
    print(f"   工程项目：{len(quantities.get('items', []))} 项")
    
    # 演示 3: 定额套用
    print("\n💰 演示 3: 定额套用")
    quota_result = agent.apply_quota("路基石方", 10)
    if "error" not in quota_result:
        print(f"   定额编号：{quota_result['quota_code']}")
        print(f"   总造价：¥{quota_result['total_cost']:,.2f}")
    
    # 系统统计
    print("\n📊 系统统计:")
    stats = agent.get_stats()
    print(f"   总项目数：{stats['total_projects']}")
    print(f"   定额总数：{stats['quota_stats']['total_quotas']}")
    print(f"   记忆宫殿：{stats['memory_palace']}")
    
    print("\n✅ Cost.Agent 演示完成!")
    print("   造价有道，自然而生。")
    
    return 0


if __name__ == "__main__":
    asyncio.run(main())
