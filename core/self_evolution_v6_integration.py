#!/usr/bin/env python3
"""
造价 Agent 自进化集成模块
=======================
将所有子模块整合为自进化系统：
- 定额数据 → knowledge/matcher → 知识图谱 → 推荐引擎
- 材料价格 → 历史分析 → 价格预测
- 造价计算 → 成本跟踪 → 偏差预警
- 变更签证 → 证据链 → 价款计算

自进化循环：
1. 数据层：增量更新定额数据
2. 知识层：扩展知识图谱
3. 计算层：优化计算精度
4. 应用层：改进推荐策略

作者：太一 AGI
创建：2026-04-25
版本：v6.0
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge.matcher import QuotaMatcher
from knowledge.knowledge_graph import KnowledgeGraph
from knowledge.incremental_update import IncrementalUpdater
from knowledge.recommendation import RecommendationEngine
from calculators.cost import CostCalculator
from calculators.material_prices import MaterialPriceAnalyzer
from calculators.quota_loader import get_quota_data, search_quota, get_stats


class CostAgentSelfEvolution:
    """造价 Agent 自进化引擎 v6.0"""
    
    def __init__(self):
        self.matcher = QuotaMatcher()
        self.graph = KnowledgeGraph()
        self.updater = IncrementalUpdater()
        self.recommender = RecommendationEngine()
        self.calculator = CostCalculator()
        self.price_analyzer = MaterialPriceAnalyzer()
        self.evolution_log = []
        
    def run_evolution_cycle(self) -> Dict:
        """
        运行完整自进化循环
        
        Returns:
            进化报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "version": "6.0.0",
            "cycles": {},
        }
        
        # 1. 数据层进化
        report["cycles"]["data"] = self._evolve_data()
        
        # 2. 知识层进化
        report["cycles"]["knowledge"] = self._evolve_knowledge()
        
        # 3. 计算层进化
        report["cycles"]["calculation"] = self._evolve_calculation()
        
        # 4. 应用层进化
        report["cycles"]["application"] = self._evolve_application()
        
        # 5. 生成进化报告
        report["summary"] = self._generate_summary(report)
        
        self.evolution_log.append(report)
        return report
    
    def _evolve_data(self) -> Dict:
        """数据层进化：增量更新定额数据"""
        result = {"status": "ok", "updated": 0}
        
        try:
            stats = get_stats()
            total_quotas = sum(s.get("total", 0) for s in stats.values() if "error" not in s)
            result["total_quotas"] = total_quotas
            result["professions"] = len([s for s in stats.values() if "error" not in s])
            
            # 增量更新知识图谱
            self.updater.update_from_quotas()
            result["updated"] = 1
            
        except Exception as e:
            result["status"] = f"error: {str(e)}"
        
        return result
    
    def _evolve_knowledge(self) -> Dict:
        """知识层进化：扩展知识图谱"""
        result = {"status": "ok"}
        
        try:
            # 构建知识图谱
            self.graph.build_from_matcher(self.matcher)
            result["nodes"] = self.graph.node_count
            result["edges"] = self.graph.edge_count
            
            # 更新推荐策略
            self.recommender.update_strategy()
            result["strategy_updated"] = True
            
        except Exception as e:
            result["status"] = f"error: {str(e)}"
        
        return result
    
    def _evolve_calculation(self) -> Dict:
        """计算层进化：优化计算精度"""
        result = {"status": "ok"}
        
        try:
            # 材料价格分析
            price_stats = self.price_analyzer.analyze_trends()
            result["price_trends"] = price_stats
            
            # 计算精度验证
            accuracy = self.calculator.validate_accuracy()
            result["accuracy"] = accuracy
            
        except Exception as e:
            result["status"] = f"error: {str(e)}"
        
        return result
    
    def _evolve_application(self) -> Dict:
        """应用层进化：改进推荐策略"""
        result = {"status": "ok"}
        
        try:
            # 推荐效果评估
            evaluation = self.recommender.evaluate()
            result["evaluation"] = evaluation
            
            # 策略优化
            self.recommender.optimize()
            result["optimized"] = True
            
        except Exception as e:
            result["status"] = f"error: {str(e)}"
        
        return result
    
    def _generate_summary(self, report: Dict) -> Dict:
        """生成进化摘要"""
        cycles = report.get("cycles", {})
        return {
            "data_status": cycles.get("data", {}).get("status", "unknown"),
            "knowledge_status": cycles.get("knowledge", {}).get("status", "unknown"),
            "calculation_status": cycles.get("calculation", {}).get("status", "unknown"),
            "application_status": cycles.get("application", {}).get("status", "unknown"),
            "total_evolution_cycles": len(self.evolution_log),
        }
    
    def get_evolution_history(self, limit: int = 10) -> List[Dict]:
        """获取进化历史"""
        return self.evolution_log[-limit:]
    
    def save_evolution_log(self, filepath: Optional[str] = None):
        """保存进化日志"""
        if filepath is None:
            filepath = str(Path(__file__).parent.parent / "reports" / "evolution_log.json")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.evolution_log, f, ensure_ascii=False, indent=2)


# 便捷函数
def run_evolution() -> Dict:
    """运行自进化循环（便捷函数）"""
    agent = CostAgentSelfEvolution()
    return agent.run_evolution_cycle()


def get_agent_status() -> Dict:
    """获取 Agent 状态"""
    agent = CostAgentSelfEvolution()
    return {
        "version": "6.0.0",
        "modules": {
            "matcher": "ok",
            "knowledge_graph": "ok",
            "incremental_updater": "ok",
            "recommendation": "ok",
            "cost_calculator": "ok",
            "material_prices": "ok",
            "quota_loader": "ok",
        },
        "quota_stats": get_stats(),
    }


if __name__ == "__main__":
    print("=== 造价 Agent 自进化引擎 v6.0 ===")
    print()
    
    # 获取状态
    status = get_agent_status()
    print(f"版本: {status['version']}")
    print(f"模块状态: {', '.join(f'{k}: {v}' for k, v in status['modules'].items())}")
    print()
    
    # 定额数据概览
    print("定额数据:")
    for prof, s in status["quota_stats"].items():
        if "error" not in s:
            print(f"  {s['name']:12s} {s['total']:>6} 条 {s['prefixes']:>2} 章")
    print()
    
    # 运行进化循环
    print("运行自进化循环...")
    agent = CostAgentSelfEvolution()
    report = agent.run_evolution_cycle()
    print(f"进化报告: {json.dumps(report['summary'], ensure_ascii=False, indent=2)}")
