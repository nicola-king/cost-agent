#!/usr/bin/env python3
"""
Cost Agent RESTful API 服务
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from cost_agent_v6 import CostAgent

app = Flask(__name__)
CORS(app)
agent = CostAgent()


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'healthy', 'version': '6.0'})


@app.route('/api/v1/quota/query', methods=['POST'])
def quota_query():
    """综合查询"""
    data = request.get_json()
    query = data.get('query', '')

    if not query:
        return jsonify({'error': 'query is required'}), 400

    result = agent.comprehensive_query(query)
    return jsonify(result)


@app.route('/api/v1/quota/search', methods=['POST'])
def quota_search():
    """关键词搜索"""
    data = request.get_json()
    keyword = data.get('keyword', '')
    top_k = data.get('top_k', 10)

    if not keyword:
        return jsonify({'error': 'keyword is required'}), 400

    results = agent.search_quota(keyword, top_k)
    return jsonify(results)


@app.route('/api/v1/quota/code/<code>', methods=['GET'])
def quota_by_code(code):
    """按编号查询"""
    result = agent.query_by_code(code)
    return jsonify(result)


@app.route('/api/v1/quota/ask', methods=['POST'])
def quota_ask():
    """自然语言问答"""
    data = request.get_json()
    question = data.get('question', '')

    if not question:
        return jsonify({'error': 'question is required'}), 400

    result = agent.ask_quota(question)
    return jsonify(result)


@app.route('/api/v1/recommend/quotas', methods=['POST'])
def recommend_quotas():
    """推荐定额"""
    data = request.get_json()
    query = data.get('query', '')
    top_k = data.get('top_k', 5)

    if not query:
        return jsonify({'error': 'query is required'}), 400

    quotas = agent.recommend_quotas(query, top_k)
    return jsonify({'quotas': quotas})


@app.route('/api/v1/recommend/explanations', methods=['POST'])
def recommend_explanations():
    """推荐解释"""
    data = request.get_json()
    query = data.get('query', '')
    top_k = data.get('top_k', 5)

    if not query:
        return jsonify({'error': 'query is required'}), 400

    explanations = agent.recommend_explanations(query, top_k)
    return jsonify({'explanations': explanations})


@app.route('/api/v1/recommend/docs', methods=['POST'])
def recommend_docs():
    """推荐政府文件"""
    data = request.get_json()
    query = data.get('query', '')
    top_k = data.get('top_k', 5)

    if not query:
        return jsonify({'error': 'query is required'}), 400

    docs = agent.recommend_docs(query, top_k)
    return jsonify({'documents': docs})


@app.route('/api/v1/graph/stats', methods=['GET'])
def graph_stats():
    """图谱统计"""
    stats = agent.get_graph_stats()
    return jsonify(stats)


@app.route('/api/v1/graph/query', methods=['POST'])
def graph_query():
    """图谱查询"""
    data = request.get_json()
    query = data.get('query', '')

    if not query:
        return jsonify({'error': 'query is required'}), 400

    result = agent.query_graph(query)
    return jsonify(result)


@app.route('/api/v1/evolution/status', methods=['GET'])
def evolution_status():
    """进化状态"""
    status = agent.check_evolution()
    return jsonify(status)


@app.route('/api/v1/evolution/trigger', methods=['POST'])
def evolution_trigger():
    """触发进化"""
    success = agent.trigger_evolution()
    return jsonify({'success': success})


@app.route('/api/v1/update/check', methods=['GET'])
def update_check():
    """检查更新"""
    changes = agent.check_for_updates()
    return jsonify({'changes': changes})


@app.route('/api/v1/update/rebuild', methods=['POST'])
def update_rebuild():
    """重建索引"""
    rebuilt = agent.rebuild_index()
    return jsonify({'rebuilt': rebuilt})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
