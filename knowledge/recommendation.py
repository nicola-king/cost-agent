#!/usr/bin/env python3
"""
智能推荐引擎 - 基于知识图谱的定额/解释推荐
"""

import os
import sys
import json
from typing import List, Dict, Tuple
from collections import Counter
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 路径配置
DATA_DIR = Path(__file__).parent.parent / "data"


class RecommendationEngine:
    """智能推荐引擎"""

    def __init__(self):
        self.graph = None
        self.matcher = None
        self._load_graph()
        self._load_matcher()

    def _load_graph(self):
        """加载知识图谱"""
        try:
            from knowledge_graph import KnowledgeGraph
            self.graph = KnowledgeGraph()
            graph_file = DATA_DIR / "knowledge_graph.json"
            if graph_file.exists():
                with open(graph_file, 'r', encoding='utf-8') as f:
                    graph_data = json.load(f)
                self.graph.nodes = graph_data.get('nodes', {})
                self.graph.edges = graph_data.get('edges', [])
                # 重建邻接表
                from collections import defaultdict
                self.graph.adjacency = defaultdict(set)
                for edge in self.graph.edges:
                    self.graph.adjacency[edge['source']].add(edge['target'])
                    self.graph.adjacency[edge['target']].add(edge['source'])
        except Exception as e:
            print(f"⚠️ 加载知识图谱失败: {e}")

    def _load_matcher(self):
        """加载匹配器"""
        try:
            from matcher import QuotaMatcher
            self.matcher = QuotaMatcher()
            self.matcher.load_all()
        except Exception as e:
            print(f"⚠️ 加载匹配器失败: {e}")

    def recommend_quotas(self, query: str, top_k: int = 5) -> List[Dict]:
        """推荐定额"""
        if not self.graph:
            return []

        # 1. 搜索相关节点
        search_result = self.graph.query(query)

        # 2. 过滤定额节点
        quota_nodes = [
            n for n in search_result['nodes']
            if n['type'] == 'quota'
        ]

        # 3. 基于图谱关联扩展推荐
        expanded_quotas = set()
        for node in quota_nodes[:top_k]:
            expanded_quotas.add(node['id'])
            # 获取邻居节点中的定额
            for neighbor_id in self.graph.get_neighbors(node['id']):
                if neighbor_id.startswith('quota:'):
                    expanded_quotas.add(neighbor_id)

        # 4. 构建推荐结果
        recommendations = []
        for quota_id in expanded_quotas:
            if quota_id in self.graph.nodes:
                node_data = self.graph.nodes[quota_id]
                recommendations.append({
                    'id': quota_id,
                    'code': node_data['data'].get('code', ''),
                    'name': node_data['data'].get('name', ''),
                    'unit': node_data['data'].get('unit', ''),
                    'price': node_data['data'].get('price', 0),
                    'chapter': node_data['data'].get('chapter', ''),
                    'score': next(
                        (n['score'] for n in quota_nodes if n['id'] == quota_id),
                        1.0
                    )
                })

        # 5. 排序
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:top_k]

    def recommend_explanations(self, query: str, top_k: int = 5) -> List[Dict]:
        """推荐解释"""
        if not self.matcher:
            return []

        # 使用匹配器的问答功能
        result = self.matcher.ask(query)

        if result.get('qa_answer'):
            return [{
                'id': result['qa_answer']['id'],
                'question': result['qa_answer']['question'],
                'answer': result['qa_answer']['answer'],
                'source': result['qa_answer']['source_file'],
                'score': 1.0
            }]

        return []

    def recommend_docs(self, query: str, top_k: int = 5) -> List[Dict]:
        """推荐政府文件"""
        if not self.graph:
            return []

        # 搜索相关节点
        search_result = self.graph.query(query)

        # 过滤政府文件节点
        doc_nodes = [
            n for n in search_result['nodes']
            if n['type'] == 'gov_doc'
        ]

        # 构建推荐结果
        recommendations = []
        for node in doc_nodes[:top_k]:
            recommendations.append({
                'id': node['id'],
                'filename': node['data'].get('filename', ''),
                'category': node['data'].get('category', ''),
                'doc_numbers': node['data'].get('doc_numbers', []),
                'score': node['score']
            })

        return recommendations

    def get_related(self, quota_code: str) -> Dict:
        """获取定额的关联内容"""
        result = {
            'quota': None,
            'explanations': [],
            'documents': []
        }

        if not self.graph:
            return result

        quota_id = f"quota:{quota_code}"
        if quota_id not in self.graph.nodes:
            return result

        # 获取定额信息
        result['quota'] = self.graph.nodes[quota_id]['data']

        # 获取关联的解释
        for neighbor_id in self.graph.get_neighbors(quota_id):
            if neighbor_id.startswith('qa:'):
                node_data = self.graph.nodes[neighbor_id]
                result['explanations'].append(node_data['data'])

        # 获取关联的文件
        for neighbor_id in self.graph.get_neighbors(quota_id):
            if neighbor_id.startswith('doc:'):
                node_data = self.graph.nodes[neighbor_id]
                result['documents'].append(node_data['data'])

        return result


def main():
    print("🎯 智能推荐引擎")
    print("=" * 50)

    engine = RecommendationEngine()

    # 测试推荐
    test_queries = ['混凝土', '安全文明', '管道']

    for query in test_queries:
        print(f"\n=== 查询: {query} ===")

        # 推荐定额
        quotas = engine.recommend_quotas(query, top_k=3)
        print(f"推荐定额 ({len(quotas)} 条):")
        for q in quotas:
            print(f"  {q['code']} | {q['name'][:30]} | {q['unit']} | {q['price']}元")

        # 推荐解释
        explanations = engine.recommend_explanations(query, top_k=2)
        if explanations:
            print(f"推荐解释 ({len(explanations)} 条):")
            for e in explanations:
                print(f"  Q: {e['question'][:50]}...")

        # 推荐文件
        docs = engine.recommend_docs(query, top_k=2)
        if docs:
            print(f"推荐文件 ({len(docs)} 份):")
            for d in docs:
                print(f"  {d['filename']}")


if __name__ == '__main__':
    main()
