#!/usr/bin/env python3
"""
Cost Agent Web 界面 - Flask 实现
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from cost_agent_v6 import CostAgent

app = Flask(__name__)
agent = CostAgent()


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def api_query():
    """查询 API"""
    data = request.get_json()
    query = data.get('query', '')

    if not query:
        return jsonify({'error': '请输入查询内容'}), 400

    result = agent.comprehensive_query(query)
    return jsonify(result)


@app.route('/api/search', methods=['POST'])
def api_search():
    """搜索 API"""
    data = request.get_json()
    keyword = data.get('keyword', '')
    top_k = data.get('top_k', 10)

    if not keyword:
        return jsonify({'error': '请输入搜索关键词'}), 400

    results = agent.search_quota(keyword, top_k)
    return jsonify(results)


@app.route('/api/ask', methods=['POST'])
def api_ask():
    """问答 API"""
    data = request.get_json()
    question = data.get('question', '')

    if not question:
        return jsonify({'error': '请输入问题'}), 400

    result = agent.ask_quota(question)
    return jsonify(result)


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    """推荐 API"""
    data = request.get_json()
    query = data.get('query', '')
    top_k = data.get('top_k', 5)

    if not query:
        return jsonify({'error': '请输入推荐内容'}), 400

    quotas = agent.recommend_quotas(query, top_k)
    explanations = agent.recommend_explanations(query, top_k)
    docs = agent.recommend_docs(query, top_k)

    return jsonify({
        'quotas': quotas,
        'explanations': explanations,
        'documents': docs
    })


@app.route('/api/status', methods=['GET'])
def api_status():
    """状态 API"""
    status = {
        'graph_stats': agent.get_graph_stats(),
        'update_status': agent.get_update_status(),
        'evolution_status': agent.check_evolution()
    }
    return jsonify(status)


@app.route('/api/evolve', methods=['POST'])
def api_evolve():
    """进化 API"""
    success = agent.trigger_evolution()
    return jsonify({'success': success})


@app.route('/api/graph', methods=['GET'])
def api_graph():
    """图谱 API"""
    query = request.args.get('query', '')
    if query:
        result = agent.query_graph(query)
    else:
        result = agent.get_graph_stats()
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
