# 造价 Agent v6.0 (Cost Agent)

> **版本**: 6.0.0  
> **创建时间**: 2026-04-10  
> **最后更新**: 2026-04-25  
> **作者**: 太一 AGI  
> **决策人**: SAYELF  
> **类别**: 专业领域 / 工程造价 / 自进化  

---

## 🎯 职责域

**核心功能**: 工程造价计算、定额匹配、材料价格分析、成本跟踪、变更签证管理

**适用场景**:
- 建筑工程造价计算（重庆2018计价定额）
- 装饰/安装/市政/轨道/装配式工程造价
- 材料价格波动分析
- 工程变更价款计算
- 成本自进化学习

---

## 🏗️ 架构总览

```
cost-agent/
├── core/                    # 核心引擎
│   ├── engine.py            # 造价计算引擎
│   ├── self_evolution_core.py    # 自进化框架
│   ├── self_evolution_core_v6.py # 自进化 v6
│   ├── self_evolution_impl.py    # 自进化实现 (481行)
│   └── performance_optimizer.py  # 性能优化
├── calculators/             # 计算器模块 (可独立发布)
│   ├── cost.py              # 造价计算
│   ├── historical_data.py   # 历史数据分析
│   ├── material_prices.py   # 材料价格
│   └── quota_database.py    # 定额数据库
├── knowledge/               # 知识模块 (可独立发布)
│   ├── matcher.py           # 定额匹配器 (544行)
│   ├── knowledge_graph.py   # 知识图谱 (349行)
│   ├── recommendation.py    # 推荐引擎 (216行)
│   ├── semantic_search.py   # 语义搜索 (170行)
│   ├── incremental_update.py # 增量更新 (244行)
│   └── visualizer.py        # 可视化 (294行)
├── data/quotas/             # 定额数据 (28,920条 / 42.4MB)
│   ├── building.json        # 建筑工程 (1,645条)
│   ├── decoration.json      # 装饰装修 (1,609条)
│   ├── installation.json    # 安装工程 (16,511条)
│   ├── municipal.json       # 市政工程 (4,272条)
│   ├── prefab.json          # 装配式 (368条)
│   └── transit.json         # 轨道交通 (4,515条)
├── cost_tracking/           # 成本跟踪 (可独立发布)
│   ├── self_evolution.py
│   └── self_evolution_cost_tracker_agent.py
├── change_order/            # 变更签证管理 (可独立发布)
│   ├── README.md
│   └── templates/
├── api/                     # REST API
│   └── app.py
├── web/                     # Web 界面
│   ├── app.py
│   └── templates/
├── scripts/                 # 数据转换脚本
├── tests/                   # 测试
└── reports/                 # 报告输出
```

---

## 📦 模块化发布清单

| 模块 | 路径 | 独立发布 | 依赖 |
|------|------|---------|------|
| **定额匹配器** | `knowledge/` | ✅ | 无 |
| **造价计算器** | `calculators/` | ✅ | `knowledge/` (可选) |
| **知识图谱** | `knowledge/knowledge_graph.py` | ✅ | 无 |
| **定额数据** | `data/quotas/` | ✅ | 无 |
| **成本跟踪** | `cost_tracking/` | ✅ | `calculators/` |
| **变更签证** | `change_order/` | ✅ | 无 |
| **自进化引擎** | `core/` | ✅ | `knowledge/` + `calculators/` |
| **REST API** | `api/` | ⚠️ | 全部 |
| **Web 界面** | `web/` | ⚠️ | `api/` |

---

## 🧬 自进化机制

### 三层自进化架构

```
┌─────────────────────────────────────────┐
│         self_evolution_core_v6.py       │  ← 框架层 (调度/编排)
├─────────────────────────────────────────┤
│         self_evolution_impl.py          │  ← 实现层 (481行)
│  - DataEvolutionImpl                    │
│  - KnowledgeEvolutionImpl               │
│  - PerformanceEvolutionImpl             │
├─────────────────────────────────────────┤
│  knowledge/ + calculators/ + data/      │  ← 数据层
│  - matcher.py / knowledge_graph.py      │
│  - cost.py / material_prices.py         │
│  - quotas/*.json                        │
└─────────────────────────────────────────┘
```

### 自进化能力

| 能力 | 实现 | 状态 |
|------|------|------|
| 定额数据增量更新 | `knowledge/incremental_update.py` | ✅ |
| 知识图谱自动扩展 | `knowledge/knowledge_graph.py` | ✅ |
| 材料价格学习 | `calculators/material_prices.py` | ✅ |
| 计算精度优化 | `core/performance_optimizer.py` | ✅ |
| 语义匹配进化 | `knowledge/matcher.py` | ✅ |
| 推荐策略优化 | `knowledge/recommendation.py` | ✅ |

---

## 📊 定额数据概览

| 专业 | 定额数 | 文件大小 | 数据文件 |
|------|--------|---------|---------|
| 建筑工程 | 1,645 | 1.6MB | `building.json` |
| 装饰装修 | 1,609 | 1.6MB | `decoration.json` |
| 安装工程 | 16,511 | 27.6MB | `installation.json` |
| 市政工程 | 4,272 | 5.8MB | `municipal.json` |
| 装配式 | 368 | 0.5MB | `prefab.json` |
| 轨道交通 | 4,515 | 5.2MB | `transit.json` |
| **合计** | **28,920** | **42.4MB** | **6 文件** |

**数据来源**: 重庆市2018计价定额 Access 数据库  
**更新日期**: 2026-04-24

---

## 🔌 API 接口

### REST API (`api/app.py`)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/quota/search` | POST | 定额搜索 |
| `/api/quota/match` | POST | 定额匹配 |
| `/api/cost/calculate` | POST | 造价计算 |
| `/api/material/prices` | GET | 材料价格 |
| `/api/knowledge/graph` | GET | 知识图谱 |
| `/api/evolution/status` | GET | 自进化状态 |

### Web 界面 (`web/app.py`)

- 可视化定额查询
- 交互式造价计算
- 知识图谱展示

---

## 🚀 快速开始

```python
# 导入造价 Agent
from skills._system.cost_agent.core.engine import CostEngine
from skills._system.cost_agent.knowledge.matcher import QuotaMatcher
from skills._system.cost_agent.calculators.cost import CostCalculator

# 初始化
engine = CostEngine()
matcher = QuotaMatcher()
calculator = CostCalculator()

# 定额匹配
results = matcher.match("人工平整场地", top_k=5)

# 造价计算
cost = calculator.calculate({
    "items": [
        {"name": "人工平整场地", "quantity": 100, "unit": "100m2"}
    ]
})

# 自进化
from skills._system.cost_agent.core.self_evolution_impl import DataEvolutionImpl
evolver = DataEvolutionImpl()
evolver.run_evolution_cycle()
```

---

## 📋 子模块独立 SKILL.md

每个子模块都有独立的 SKILL.md，可单独发布：

| 子模块 | SKILL.md 路径 |
|--------|--------------|
| 定额匹配器 | `knowledge/SKILL.md` |
| 造价计算器 | `calculators/SKILL.md` |
| 知识图谱 | `knowledge/SKILL.md` |
| 定额数据 | `data/quotas/SKILL.md` |
| 成本跟踪 | `cost_tracking/SKILL.md` |
| 变更签证 | `change_order/SKILL.md` |

---

## 🔗 相关模块

- **08-emerged/quota-***: 原始定额数据源（已整合，保留备份）
- **08-emerged/quota-matcher**: 原始匹配器（已整合到 knowledge/）
- **08-emerged/cost-agent**: 独立版本（已整合到主版本）

---

*太一 AGI · 造价 Agent v6.0 · OpenClaw 2026.4.25*
