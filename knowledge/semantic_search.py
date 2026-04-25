#!/usr/bin/env python3
"""
语义搜索模块 - 基于 TF-IDF + 余弦相似度
不依赖外部模型，轻量级实现
"""

import os
import re
import json
import math
from typing import List, Dict, Tuple
from collections import Counter

import jieba


class SemanticSearch:
    """轻量级语义搜索引擎"""

    def __init__(self):
        self.documents: List[Dict] = []
        self.tfidf_matrix: Dict[str, Dict[str, float]] = {}
        self.idf: Dict[str, float] = {}
        self.vocab: set = set()

    def add_document(self, doc_id: str, text: str, metadata: Dict = None):
        """添加文档"""
        words = self._tokenize(text)
        self.documents.append({
            'id': doc_id,
            'text': text,
            'words': words,
            'metadata': metadata or {}
        })
        self.vocab.update(words)

    def build_index(self):
        """构建 TF-IDF 索引"""
        n_docs = len(self.documents)
        if n_docs == 0:
            return

        # 计算 IDF
        doc_freq: Dict[str, int] = Counter()
        for doc in self.documents:
            unique_words = set(doc['words'])
            for word in unique_words:
                doc_freq[word] += 1

        self.idf = {
            word: math.log((n_docs + 1) / (freq + 1)) + 1
            for word, freq in doc_freq.items()
        }

        # 计算 TF-IDF
        for doc in self.documents:
            tf = Counter(doc['words'])
            max_tf = max(tf.values()) if tf else 1
            self.tfidf_matrix[doc['id']] = {
                word: (count / max_tf) * self.idf.get(word, 0)
                for word, count in tf.items()
            }

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """搜索文档"""
        query_words = self._tokenize(query)
        if not query_words:
            return []

        # 计算查询的 TF-IDF
        query_tf = Counter(query_words)
        max_tf = max(query_tf.values()) if query_tf else 1
        query_tfidf = {
            word: (count / max_tf) * self.idf.get(word, 0)
            for word, count in query_tf.items()
        }

        # 计算余弦相似度
        scores = []
        for doc in self.documents:
            score = self._cosine_similarity(
                query_tfidf,
                self.tfidf_matrix.get(doc['id'], {})
            )
            if score > 0:
                scores.append({
                    'id': doc['id'],
                    'score': score,
                    'text': doc['text'][:200],
                    'metadata': doc['metadata']
                })

        # 排序并返回
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        words = jieba.cut(text)
        # 过滤停用词
        stop_words = {
            '的', '了', '是', '在', '和', '与', '及', '或', '等',
            '可以', '应当', '必须', '应', '不得', '按', '执行',
            '规定', '相关', '相应', '该', '其', '这', '那',
            '一个', '一些', '一定', '一般', '具体', '根据',
            '按照', '参照', '实施', '进行', '采取', '使用',
            '采用', '包括', '含有', '其中', '部分', '全部',
            '整个', '其他', '另外', '同时', '以及', '并且',
            '或者', '但是', '然而', '因此', '所以', '如果',
            '假如', '假设', '当', '如', '若', '则', '凡',
            '每', '各', '本', '此', '上述', '以下', '以上',
            '下列', '前', '后', '左', '右', '上', '下',
            '内', '外', '中', '间', '边', '旁', '侧',
            '端', '头', '尾', '始', '终', '起', '止'
        }
        return [w for w in words if len(w) > 1 and w not in stop_words]

    def _cosine_similarity(
        self,
        vec1: Dict[str, float],
        vec2: Dict[str, float]
    ) -> float:
        """计算余弦相似度"""
        # 找到共同词汇
        common_words = set(vec1.keys()) & set(vec2.keys())
        if not common_words:
            return 0.0

        # 点积
        dot_product = sum(vec1[w] * vec2[w] for w in common_words)

        # 模长
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


# ==================== 便捷函数 ====================

def create_search_engine() -> SemanticSearch:
    """创建搜索引擎实例"""
    return SemanticSearch()

if __name__ == '__main__':
    # 测试
    engine = SemanticSearch()

    # 添加测试文档
    engine.add_document('1', '混凝土是建筑工程中常用的材料', {'type': 'material'})
    engine.add_document('2', '钢筋是混凝土结构中的重要组成部分', {'type': 'material'})
    engine.add_document('3', '安全文明施工费按渝建管〔2024〕38号文执行', {'type': 'regulation'})
    engine.add_document('4', '市政管道工程需要混凝土支墩', {'type': 'construction'})

    # 构建索引
    engine.build_index()

    # 搜索测试
    print("=== 测试: 搜索 '混凝土' ===")
    results = engine.search('混凝土')
    for r in results:
        print(f"  得分: {r['score']:.4f} | {r['text']}")

    print("\n=== 测试: 搜索 '安全文明' ===")
    results = engine.search('安全文明')
    for r in results:
        print(f"  得分: {r['score']:.4f} | {r['text']}")
