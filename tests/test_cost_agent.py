#!/usr/bin/env python3
"""
Cost Agent 单元测试
"""

import os
import sys
import unittest
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from cost_agent_v6 import CostAgent
from knowledge.matcher import QuotaMatcher
from knowledge.knowledge_graph import KnowledgeGraph
from knowledge.recommendation import RecommendationEngine
from knowledge.incremental_update import IncrementalUpdater
from core.self_evolution_impl import SelfEvolutionManager
from core.performance_optimizer import CacheManager, PerformanceOptimizer


class TestCostAgent(unittest.TestCase):
    """Cost Agent 测试"""

    def setUp(self):
        """测试前准备"""
        self.agent = CostAgent()

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.matcher)
        self.assertIsNotNone(self.agent.graph)
        self.assertIsNotNone(self.agent.recommender)

    def test_query_quota(self):
        """测试定额查询"""
        result = self.agent.query_quota('混凝土')
        self.assertIsInstance(result, dict)
        self.assertIn('type', result)

    def test_search_quota(self):
        """测试关键词搜索"""
        result = self.agent.search_quota('钢筋', top_k=5)
        self.assertIsInstance(result, dict)
        self.assertIn('quota_matches', result)

    def test_query_by_code(self):
        """测试编号查询"""
        result = self.agent.query_by_code('DA0001')
        self.assertIsInstance(result, dict)
        self.assertIn('quota', result)

    def test_ask_quota(self):
        """测试自然语言问答"""
        result = self.agent.ask_quota('安全文明施工费怎么算？')
        self.assertIsInstance(result, dict)

    def test_comprehensive_query(self):
        """测试综合查询"""
        result = self.agent.comprehensive_query('管道')
        self.assertIsInstance(result, dict)
        self.assertIn('quota_matches', result)
        self.assertIn('explanations', result)
        self.assertIn('documents', result)


class TestQuotaMatcher(unittest.TestCase):
    """定额匹配器测试"""

    def setUp(self):
        """测试前准备"""
        self.matcher = QuotaMatcher()
        self.matcher.load_all()

    def test_load_all(self):
        """测试加载所有数据"""
        self.assertTrue(self.matcher._loaded)
        self.assertGreater(len(self.matcher.quota_data), 0)

    def test_search(self):
        """测试搜索"""
        result = self.matcher.search('混凝土')
        self.assertIsInstance(result, dict)
        self.assertIn('quota_matches', result)

    def test_query_by_code(self):
        """测试编号查询"""
        result = self.matcher.query_by_code('DA0001')
        self.assertIsInstance(result, dict)
        self.assertIn('quota', result)

    def test_ask(self):
        """测试问答"""
        result = self.matcher.ask('安全文明施工费怎么算？')
        self.assertIsInstance(result, dict)


class TestKnowledgeGraph(unittest.TestCase):
    """知识图谱测试"""

    def setUp(self):
        """测试前准备"""
        self.graph = KnowledgeGraph()

    def test_build_from_data(self):
        """测试构建图谱"""
        self.graph.build_from_data()
        self.assertGreater(len(self.graph.nodes), 0)
        self.assertGreater(len(self.graph.edges), 0)

    def test_query(self):
        """测试查询"""
        self.graph.build_from_data()
        result = self.graph.query('安全文明')
        self.assertIsInstance(result, dict)
        self.assertIn('nodes', result)

    def test_get_neighbors(self):
        """测试获取邻居"""
        self.graph.build_from_data()
        if self.graph.nodes:
            first_node = list(self.graph.nodes.keys())[0]
            neighbors = self.graph.get_neighbors(first_node)
            self.assertIsInstance(neighbors, list)


class TestRecommendationEngine(unittest.TestCase):
    """推荐引擎测试"""

    def setUp(self):
        """测试前准备"""
        self.engine = RecommendationEngine()

    def test_recommend_quotas(self):
        """测试推荐定额"""
        quotas = self.engine.recommend_quotas('混凝土', top_k=3)
        self.assertIsInstance(quotas, list)

    def test_recommend_explanations(self):
        """测试推荐解释"""
        explanations = self.engine.recommend_explanations('安全文明')
        self.assertIsInstance(explanations, list)

    def test_recommend_docs(self):
        """测试推荐文件"""
        docs = self.engine.recommend_docs('管道')
        self.assertIsInstance(docs, list)


class TestIncrementalUpdater(unittest.TestCase):
    """增量更新测试"""

    def setUp(self):
        """测试前准备"""
        self.updater = IncrementalUpdater()

    def test_check_for_changes(self):
        """测试检查变更"""
        changes = self.updater.check_for_changes()
        self.assertIsInstance(changes, list)

    def test_get_status(self):
        """测试获取状态"""
        status = self.updater.get_status()
        self.assertIsInstance(status, dict)
        self.assertIn('trackedFiles', status)


class TestSelfEvolutionManager(unittest.TestCase):
    """自进化管理器测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = SelfEvolutionManager()

    def test_evolve(self):
        """测试进化"""
        status = self.manager.evolve()
        self.assertIsInstance(status, dict)
        self.assertIn('generation', status)

    def test_get_status(self):
        """测试获取状态"""
        status = self.manager.get_status()
        self.assertIsInstance(status, dict)

    def test_generate_report(self):
        """测试生成报告"""
        report = self.manager.generate_report()
        self.assertIsInstance(report, dict)


class TestPerformanceOptimizer(unittest.TestCase):
    """性能优化器测试"""

    def setUp(self):
        """测试前准备"""
        self.optimizer = PerformanceOptimizer()

    def test_measure_time(self):
        """测试时间测量"""
        @self.optimizer.measure_time
        def test_func():
            import time
            time.sleep(0.01)
            return True

        result = test_func()
        self.assertTrue(result)

        metrics = self.optimizer.get_metrics()
        self.assertIn('test_func', metrics)

    def test_cache(self):
        """测试缓存"""
        cache_manager = CacheManager()
        cache_manager.set('test_data', 'test_key', ttl=60)
        cached = cache_manager.get('test_key')
        self.assertEqual(cached, 'test_data')


if __name__ == '__main__':
    unittest.main()
