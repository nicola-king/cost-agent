#!/usr/bin/env python3
"""
知识图谱模块 - 定额 ↔ 解释 ↔ 政府文件的关联图谱
"""

import os
import sys
import re
import json
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 路径配置
WORKSPACE = Path("/home/nicola/.openclaw/workspace")
QUOTA_SKILLS_DIR = WORKSPACE / "skills" / "08-emerged"
QUOTA_MD_DIR = WORKSPACE / "skills" / "07-system" / "cost-agent" / "quota_md"
DATA_DIR = Path(__file__).parent / "data"

# 定额编号正则
QUOTA_CODE_RE = re.compile(r'([A-Z]{2}\d{4})')


class KnowledgeGraph:
    """知识图谱"""

    def __init__(self):
        self.nodes: Dict[str, Dict] = {}  # node_id -> node_data
        self.edges: List[Dict] = []  # edge list
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)  # adjacency list

    def add_node(self, node_id: str, node_type: str, data: Dict):
        """添加节点"""
        self.nodes[node_id] = {
            'id': node_id,
            'type': node_type,
            'data': data
        }

    def add_edge(self, source: str, target: str, relation: str, weight: float = 1.0):
        """添加边"""
        edge = {
            'source': source,
            'target': target,
            'relation': relation,
            'weight': weight
        }
        self.edges.append(edge)
        self.adjacency[source].add(target)
        self.adjacency[target].add(source)

    def get_neighbors(self, node_id: str) -> List[str]:
        """获取邻居节点"""
        return list(self.adjacency.get(node_id, set()))

    def get_path(self, source: str, target: str) -> List[str]:
        """查找两个节点之间的路径 (BFS)"""
        if source not in self.adjacency or target not in self.adjacency:
            return []

        visited = {source}
        queue = [(source, [source])]

        while queue:
            current, path = queue.pop(0)
            if current == target:
                return path

            for neighbor in self.adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []

    def build_from_data(self):
        """从数据源构建知识图谱"""
        print("🔨 构建知识图谱...")

        # 1. 添加定额节点
        self._add_quota_nodes()

        # 2. 添加解释节点
        self._add_explanation_nodes()

        # 3. 添加政府文件节点
        self._add_gov_doc_nodes()

        # 4. 建立关联边
        self._build_edges()

        print(f"✅ 知识图谱构建完成:")
        print(f"  节点: {len(self.nodes)}")
        print(f"  边: {len(self.edges)}")

    def _add_quota_nodes(self):
        """添加定额节点"""
        skill_names = [
            'quota-building', 'quota-installation', 'quota-municipal',
            'quota-decoration', 'quota-transit', 'quota-prefab'
        ]

        for skill_name in skill_names:
            skill_dir = QUOTA_SKILLS_DIR / skill_name
            json_file = skill_dir / "quota_data.json"

            if not json_file.exists():
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 统一为列表格式
                if isinstance(data, dict) and 'prefixes' in data:
                    records = []
                    for prefix, items in data['prefixes'].items():
                        if isinstance(items, list):
                            records.extend(items)
                elif isinstance(data, list):
                    records = data
                else:
                    continue

                for record in records:
                    code = record.get('deh', '')
                    if code:
                        self.add_node(
                            f"quota:{code}",
                            'quota',
                            {
                                'code': code,
                                'name': record.get('xmmc', ''),
                                'unit': record.get('dw', ''),
                                'price': record.get('dj', 0),
                                'chapter': record.get('chapter', ''),
                                'skill': skill_name
                            }
                        )
            except Exception as e:
                print(f"⚠️ 加载 {skill_name} 失败: {e}")

    def _add_explanation_nodes(self):
        """添加解释节点"""
        qa_file = DATA_DIR / "qa_pairs.json"
        if not qa_file.exists():
            return

        try:
            with open(qa_file, 'r', encoding='utf-8') as f:
                qa_pairs = json.load(f)

            for qa in qa_pairs:
                qa_id = qa.get('id', '')
                if qa_id:
                    self.add_node(
                        f"qa:{qa_id}",
                        'qa',
                        {
                            'id': qa_id,
                            'question': qa.get('question', ''),
                            'answer': qa.get('answer', ''),
                            'source_file': qa.get('source_file', ''),
                            'related_codes': qa.get('related_codes', [])
                        }
                    )
        except Exception as e:
            print(f"⚠️ 加载 Q&A 对失败: {e}")

    def _add_gov_doc_nodes(self):
        """添加政府文件节点"""
        doc_index_file = DATA_DIR / "doc_index.json"
        if not doc_index_file.exists():
            return

        try:
            with open(doc_index_file, 'r', encoding='utf-8') as f:
                doc_index = json.load(f)

            for filename, doc_data in doc_index.items():
                doc_id = filename.replace('.md', '')
                self.add_node(
                    f"doc:{doc_id}",
                    'gov_doc',
                    {
                        'filename': filename,
                        'category': doc_data.get('category', ''),
                        'doc_numbers': doc_data.get('doc_numbers', []),
                        'keywords': doc_data.get('keywords', [])
                    }
                )
        except Exception as e:
            print(f"⚠️ 加载政府文件索引失败: {e}")

    def _build_edges(self):
        """建立关联边"""
        # 1. 定额 ↔ 解释 (通过定额编号关联)
        for node_id, node_data in self.nodes.items():
            if node_data['type'] == 'qa':
                related_codes = node_data['data'].get('related_codes', [])
                for code in related_codes:
                    quota_id = f"quota:{code}"
                    if quota_id in self.nodes:
                        self.add_edge(
                            node_id,
                            quota_id,
                            '解释',
                            weight=2.0
                        )

        # 2. 解释 ↔ 政府文件 (通过文件名关联)
        for node_id, node_data in self.nodes.items():
            if node_data['type'] == 'qa':
                source_file = node_data['data'].get('source_file', '')
                doc_id = f"doc:{source_file.replace('.md', '')}"
                if doc_id in self.nodes:
                    self.add_edge(
                        node_id,
                        doc_id,
                        '来源',
                        weight=1.5
                    )

        # 3. 定额 ↔ 政府文件 (通过关键词关联)
        quota_nodes = {k: v for k, v in self.nodes.items() if v['type'] == 'quota'}
        doc_nodes = {k: v for k, v in self.nodes.items() if v['type'] == 'gov_doc'}

        for quota_id, quota_data in quota_nodes.items():
            quota_name = quota_data['data'].get('name', '')
            quota_chapter = quota_data['data'].get('chapter', '')

            for doc_id, doc_data in doc_nodes.items():
                doc_keywords = doc_data['data'].get('keywords', [])

                # 计算关键词匹配
                match_count = 0
                for keyword in doc_keywords[:10]:  # 检查前 10 个关键词
                    if keyword in quota_name or keyword in quota_chapter:
                        match_count += 1

                if match_count >= 2:  # 至少匹配 2 个关键词
                    self.add_edge(
                        quota_id,
                        doc_id,
                        '相关',
                        weight=match_count * 0.5
                    )

        # 4. 定额 ↔ 解释 (通过关键词匹配答案)
        qa_nodes = {k: v for k, v in self.nodes.items() if v['type'] == 'qa'}

        for qa_id, qa_data in qa_nodes.items():
            qa_answer = qa_data['data'].get('answer', '')
            qa_question = qa_data['data'].get('question', '')

            for quota_id, quota_data in quota_nodes.items():
                quota_name = quota_data['data'].get('name', '')

                # 计算关键词匹配
                if quota_name in qa_answer or quota_name in qa_question:
                    self.add_edge(
                        qa_id,
                        quota_id,
                        '提及',
                        weight=1.5
                    )

    def query(self, query_text: str) -> Dict:
        """查询知识图谱"""
        result = {
            'query': query_text,
            'nodes': [],
            'paths': []
        }

        # 1. 查找匹配的节点
        for node_id, node_data in self.nodes.items():
            score = 0

            # 检查名称/内容是否匹配
            text = ''
            if node_data['type'] == 'quota':
                text = node_data['data'].get('code', '') + ' ' + node_data['data'].get('name', '') + ' ' + node_data['data'].get('chapter', '')
            elif node_data['type'] == 'qa':
                text = node_data['data'].get('question', '') + ' ' + node_data['data'].get('answer', '')
            elif node_data['type'] == 'gov_doc':
                text = ' '.join(node_data['data'].get('keywords', [])) + ' ' + node_data['data'].get('filename', '')

            if query_text in text:
                score += 3

            if score > 0:
                result['nodes'].append({
                    'id': node_id,
                    'type': node_data['type'],
                    'data': node_data['data'],
                    'score': score
                })

        # 2. 查找节点之间的路径
        result['nodes'].sort(key=lambda x: x['score'], reverse=True)
        result['nodes'] = result['nodes'][:10]

        # 3. 查找关联路径
        for i, node1 in enumerate(result['nodes'][:3]):
            for node2 in result['nodes'][i+1:4]:
                path = self.get_path(node1['id'], node2['id'])
                if path:
                    result['paths'].append(path)

        return result

    def save(self, output_path: Path = None):
        """保存知识图谱"""
        if output_path is None:
            output_path = DATA_DIR / "knowledge_graph.json"

        os.makedirs(output_path.parent, exist_ok=True)

        graph_data = {
            'nodes': self.nodes,
            'edges': self.edges
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 知识图谱已保存到 {output_path}")


def main():
    print("🔨 构建知识图谱...")

    graph = KnowledgeGraph()
    graph.build_from_data()
    graph.save()

    # 测试查询
    print("\n=== 测试查询: 混凝土 ===")
    result = graph.query('混凝土')
    print(f"  找到 {len(result['nodes'])} 个节点")
    print(f"  找到 {len(result['paths'])} 条路径")


if __name__ == '__main__':
    main()
