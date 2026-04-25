#!/usr/bin/env python3
"""
Cost Agent v6.0 - 统一造价平台
融合造价计算 + 定额匹配 + 知识图谱 + 自进化

作者：太一 AGI
版本：v6.0
日期：2026-04-25
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import CostAgent as CostEngine
from core.self_evolution_core_v6 import SelfEvolutionCore
from knowledge.matcher import QuotaMatcher
from knowledge.knowledge_graph import KnowledgeGraph
from knowledge.recommendation import RecommendationEngine
from knowledge.incremental_update import IncrementalUpdater


class CostAgent:
    """统一造价平台"""

    def __init__(self):
        """初始化"""
        self.engine = CostEngine()
        self.evolution = SelfEvolutionCore()
        self.matcher = QuotaMatcher()
        self.graph = KnowledgeGraph()
        self.recommender = RecommendationEngine()
        self.updater = IncrementalUpdater()

        # 加载数据
        self._load_data()

    def _load_data(self):
        """加载数据"""
        try:
            self.matcher.load_all()
            self.graph.build_from_data()
            print("✅ 数据加载完成")
        except Exception as e:
            print(f"⚠️ 数据加载失败: {e}")

    # ==================== 造价计算 ====================

    def calculate_cost(self, project_data: Dict) -> Dict:
        """计算造价"""
        return self.engine.calculate(project_data)

    def calculate_material_cost(self, material_name: str, quantity: float) -> Dict:
        """计算材料成本"""
        return self.engine.calculate_material(material_name, quantity)

    def get_historical_cost(self, project_type: str) -> List[Dict]:
        """获取历史成本数据"""
        return self.engine.get_historical_data(project_type)

    # ==================== 定额匹配 ====================

    def query_quota(self, query: str) -> Dict:
        """查询定额（综合查询）"""
        return self.matcher.query(query)

    def search_quota(self, keyword: str, top_k: int = 10) -> Dict:
        """关键词搜索定额"""
        return self.matcher.search(keyword, top_k)

    def query_by_code(self, code: str) -> Dict:
        """按编号查询定额"""
        return self.matcher.query_by_code(code)

    def ask_quota(self, question: str) -> Dict:
        """自然语言问答"""
        return self.matcher.ask(question)

    # ==================== 知识图谱 ====================

    def get_graph_stats(self) -> Dict:
        """获取图谱统计"""
        return {
            'nodes': len(self.graph.nodes),
            'edges': len(self.graph.edges)
        }

    def query_graph(self, query: str) -> Dict:
        """查询知识图谱"""
        return self.graph.query(query)

    def get_related(self, quota_code: str) -> Dict:
        """获取定额关联内容"""
        return self.graph.get_related(quota_code)

    # ==================== 智能推荐 ====================

    def recommend_quotas(self, query: str, top_k: int = 5) -> List[Dict]:
        """推荐定额"""
        return self.recommender.recommend_quotas(query, top_k)

    def recommend_explanations(self, query: str, top_k: int = 5) -> List[Dict]:
        """推荐解释"""
        return self.recommender.recommend_explanations(query, top_k)

    def recommend_docs(self, query: str, top_k: int = 5) -> List[Dict]:
        """推荐政府文件"""
        return self.recommender.recommend_docs(query, top_k)

    # ==================== 自进化 ====================

    def check_evolution(self) -> Dict:
        """检查进化状态"""
        return self.evolution.get_status()

    def trigger_evolution(self) -> bool:
        """触发进化"""
        return self.evolution.evolve()

    def get_evolution_report(self) -> Dict:
        """获取进化报告"""
        return self.evolution.generate_report()

    # ==================== 增量更新 ====================

    def check_for_updates(self) -> List[Dict]:
        """检查文件变更"""
        return self.updater.check_for_changes()

    def rebuild_index(self) -> bool:
        """重建索引"""
        return self.updater.rebuild_if_needed()

    def get_update_status(self) -> Dict:
        """获取更新状态"""
        return self.updater.get_status()

    # ==================== 综合查询 ====================

    def comprehensive_query(self, query: str) -> Dict:
        """综合查询（推荐入口）"""
        result = {
            'query': query,
            'quota_matches': [],
            'explanations': [],
            'documents': [],
            'related_quotas': []
        }

        # 1. 定额匹配
        quota_result = self.matcher.query(query)
        if quota_result.get('data', {}).get('quota_matches'):
            result['quota_matches'] = quota_result['data']['quota_matches'][:5]

        # 2. 解释推荐
        explanations = self.recommend_explanations(query, top_k=3)
        result['explanations'] = explanations

        # 3. 文档推荐
        docs = self.recommend_docs(query, top_k=3)
        result['documents'] = docs

        # 4. 相关定额
        if quota_result.get('data', {}).get('quota'):
            code = quota_result['data']['quota']['data'].get('deh', '')
            if code:
                related = self.get_related(code)
                result['related_quotas'] = related.get('explanations', [])[:3]

        return result


# ==================== 便捷函数 ====================

def create_agent() -> CostAgent:
    """创建造价 Agent 实例"""
    return CostAgent()

def quick_query(query: str) -> Dict:
    """快速查询"""
    agent = CostAgent()
    return agent.comprehensive_query(query)

def quick_search(keyword: str) -> List[Dict]:
    """快速搜索"""
    agent = CostAgent()
    return agent.search_quota(keyword)

def quick_ask(question: str) -> Dict:
    """快速问答"""
    agent = CostAgent()
    return agent.ask_quota(question)


# ==================== CLI ====================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Cost Agent v6.0 - 统一造价平台')
    parser.add_argument('command', choices=['query', 'search', 'ask', 'recommend', 'status'],
                       help='命令类型')
    parser.add_argument('query', nargs='?', help='查询内容')
    parser.add_argument('--top-k', type=int, default=5, help='返回数量')

    args = parser.parse_args()

    agent = CostAgent()

    if args.command == 'query':
        result = agent.comprehensive_query(args.query)
        print(f"查询: {args.query}")
        print(f"定额匹配: {len(result['quota_matches'])} 条")
        print(f"解释推荐: {len(result['explanations'])} 条")
        print(f"文档推荐: {len(result['documents'])} 份")

    elif args.command == 'search':
        results = agent.search_quota(args.query, args.top_k)
        print(f"搜索: {args.query}")
        for r in results.get('quota_matches', [])[:args.top_k]:
            q = r['data']
            print(f"  {q.get('deh')} | {q.get('xmmc')[:30]} | {q.get('dw')} | {q.get('dj')}元")

    elif args.command == 'ask':
        result = agent.ask_quota(args.query)
        if result.get('qa_answer'):
            qa = result['qa_answer']
            print(f"问题：{qa['question']}")
            print(f"答案：{qa['answer']}")
            print(f"来源：{qa['source_file']}")

    elif args.command == 'recommend':
        quotas = agent.recommend_quotas(args.query, args.top_k)
        print(f"推荐: {args.query}")
        for q in quotas:
            print(f"  {q['code']} | {q['name'][:30]} | {q['unit']} | {q['price']}元")

    elif args.command == 'status':
        print("=== Cost Agent v6.0 状态 ===")
        print(f"图谱节点：{len(agent.graph.nodes)}")
        print(f"图谱边：{len(agent.graph.edges)}")
        print(f"跟踪文件：{agent.updater.get_status()['trackedFiles']}")
        print(f"进化状态：{agent.evolution.get_status()}")


if __name__ == '__main__':
    main()
