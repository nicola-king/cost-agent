#!/usr/bin/env python3
"""
图谱可视化模块 - 生成知识图谱的 HTML 可视化
"""

import os
import sys
import json
from typing import Dict, List
from pathlib import Path

# 路径配置
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


class GraphVisualizer:
    """知识图谱可视化器"""

    def __init__(self):
        self.graph_data: Dict = {}

    def load_graph(self, graph_file: Path = None):
        """加载知识图谱数据"""
        if graph_file is None:
            graph_file = DATA_DIR / "knowledge_graph.json"

        if graph_file.exists():
            with open(graph_file, 'r', encoding='utf-8') as f:
                self.graph_data = json.load(f)
        else:
            print(f"⚠️ 图谱文件不存在: {graph_file}")

    def generate_html(self, output_file: Path = None, max_nodes: int = 500):
        """生成 HTML 可视化"""
        if output_file is None:
            output_file = OUTPUT_DIR / "knowledge_graph.html"

        os.makedirs(output_file.parent, exist_ok=True)

        # 限制节点数量
        nodes = list(self.graph_data.get('nodes', {}).values())[:max_nodes]
        edges = self.graph_data.get('edges', [])

        # 构建节点和边的列表
        node_list = []
        for i, node in enumerate(nodes):
            node_list.append({
                'id': node['id'],
                'type': node['type'],
                'label': self._get_node_label(node),
                'color': self._get_node_color(node['type'])
            })

        edge_list = []
        for edge in edges:
            # 只包含存在的节点
            source_exists = any(n['id'] == edge['source'] for n in node_list)
            target_exists = any(n['id'] == edge['target'] for n in node_list)
            if source_exists and target_exists:
                edge_list.append({
                    'source': edge['source'],
                    'target': edge['target'],
                    'relation': edge['relation'],
                    'width': edge.get('weight', 1.0)
                })

        # 生成 HTML
        html_content = self._generate_html_template(node_list, edge_list)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ 可视化已生成: {output_file}")
        return output_file

    def _get_node_label(self, node: Dict) -> str:
        """获取节点标签"""
        if node['type'] == 'quota':
            return f"{node['data'].get('code', '')} - {node['data'].get('name', '')[:20]}"
        elif node['type'] == 'qa':
            return f"Q: {node['data'].get('question', '')[:30]}..."
        elif node['type'] == 'gov_doc':
            return node['data'].get('filename', '')[:40]
        return node['id']

    def _get_node_color(self, node_type: str) -> str:
        """获取节点颜色"""
        colors = {
            'quota': '#4CAF50',  # 绿色
            'qa': '#2196F3',     # 蓝色
            'gov_doc': '#FF9800' # 橙色
        }
        return colors.get(node_type, '#9E9E9E')

    def _generate_html_template(self, nodes: List[Dict], edges: List[Dict]) -> str:
        """生成 HTML 模板"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>定额知识图谱可视化</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            font-family: 'Microsoft YaHei', sans-serif;
            background: #1a1a2e;
            color: #eee;
        }}
        #graph {{
            width: 100vw;
            height: 100vh;
        }}
        .legend {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 8px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .controls {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 8px;
        }}
        input[type="text"] {{
            padding: 8px;
            border: none;
            border-radius: 4px;
            background: #333;
            color: #fff;
            width: 200px;
        }}
        .stats {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div id="graph"></div>

    <div class="legend">
        <h3>图例</h3>
        <div class="legend-item">
            <div class="legend-color" style="background: #4CAF50"></div>
            <span>定额条目</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #2196F3"></div>
            <span>解释 Q&A</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #FF9800"></div>
            <span>政府文件</span>
        </div>
    </div>

    <div class="controls">
        <h3>搜索</h3>
        <input type="text" id="search" placeholder="输入关键词搜索..." onkeyup="searchNodes(this.value)">
    </div>

    <div class="stats">
        <h3>统计</h3>
        <p>节点: {len(nodes)}</p>
        <p>边: {len(edges)}</p>
    </div>

    <script>
        const nodes = {json.dumps(nodes)};
        const edges = {json.dumps(edges)};

        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(edges).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = svg.append("g")
            .selectAll("line")
            .data(edges)
            .enter().append("line")
            .attr("stroke", "#666")
            .attr("stroke-width", d => d.width);

        const node = svg.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("r", 5)
            .attr("fill", d => d.color)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        const label = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .text(d => d.label)
            .attr("font-size", 10)
            .attr("fill", "#ccc")
            .attr("dx", 10)
            .attr("dy", 5);

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        function searchNodes(query) {{
            const filtered = nodes.filter(n =>
                n.label.toLowerCase().includes(query.toLowerCase())
            );
            node.attr("opacity", d => filtered.includes(d) ? 1 : 0.1);
            label.attr("opacity", d => filtered.includes(d) ? 1 : 0.1);
        }}
    </script>
</body>
</html>"""


def main():
    print("📊 知识图谱可视化生成器")
    print("=" * 50)

    visualizer = GraphVisualizer()
    visualizer.load_graph()

    # 生成可视化
    output_file = visualizer.generate_html(max_nodes=200)
    print(f"✅ 已生成: {output_file}")


if __name__ == '__main__':
    main()
