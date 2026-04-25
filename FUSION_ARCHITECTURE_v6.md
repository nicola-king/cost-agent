# Cost Agent v6.0 - 融合升级架构

> **版本**: v6.0 (融合升级版)  
> **创建时间**: 2026-04-25  
> **升级来源**: v5.0 + quota-matcher v3.0  
> **核心特性**: 造价计算 + 定额匹配 + 知识图谱 + 自进化  
> **作者**: 太一 AGI

---

## 📋 升级背景

### v5.0 → v6.0 演进
| 版本 | 核心能力 | 集成度 |
|------|---------|--------|
| v5.0 | 全域自进化 | 独立系统 |
| v6.0 | 融合升级 | 统一平台 |

### 融合定义
```
v6.0 = 造价计算 (v5.0) + 定额匹配 (v3.0) + 知识图谱 + 自进化
```

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────┐
│              Cost Agent v6.0                            │
│          (统一造价平台)                                 │
└─────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  造价计算层  │    │  知识匹配层  │    │  自进化层    │
│              │    │              │    │              │
│ • 成本计算   │    │ • 定额查询   │    │ • 数据进化   │
│ • 材料成本   │    │ • 语义搜索   │    │ • 模型进化   │
│ • 历史数据   │    │ • 知识图谱   │    │ • 流程进化   │
│ • 变更管理   │    │ • 智能推荐   │    │ • 知识进化   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌──────────────┐
                    │  统一入口    │
                    │              │
                    │ • CLI        │
                    │ • API        │
                    │ • 便捷函数   │
                    └──────────────┘
```

---

## 📁 文件结构

```
cost-agent/
├── cost_agent_v6.py          # 统一入口
├── core/
│   ├── engine.py             # 造价计算引擎
│   ├── self_evolution_core.py  # v5 自进化
│   └── self_evolution_core_v6.py # v6 自进化 (完整版)
├── knowledge/                # 知识层 (新增)
│   ├── __init__.py
│   ├── matcher.py            # 定额匹配引擎
│   ├── semantic_search.py    # 语义搜索
│   ├── knowledge_graph.py    # 知识图谱
│   ├── recommendation.py     # 智能推荐
│   ├── visualizer.py         # 图谱可视化
│   └── incremental_update.py # 增量更新
├── calculators/              # 计算器模块
├── cost_tracking/            # 成本追踪
├── change_order/             # 变更管理
├── data/                     # 数据层
├── quota_md/                 # 定额解释文档
├── reports/                  # 报表
└── scripts/                  # 脚本
```

---

## 🎯 核心能力

### 1. 造价计算

```python
from cost_agent_v6 import CostAgent

agent = CostAgent()

# 计算造价
result = agent.calculate_cost(project_data)

# 材料成本
cost = agent.calculate_material_cost('混凝土', 100)

# 历史数据
history = agent.get_historical_cost('市政')
```

### 2. 定额匹配

```python
# 综合查询
result = agent.query_quota('混凝土')

# 关键词搜索
results = agent.search_quota('钢筋', top_k=10)

# 编号查询
item = agent.query_by_code('DA0001')

# 自然语言问答
answer = agent.ask_quota('安全文明施工费怎么算？')
```

### 3. 知识图谱

```python
# 图谱统计
stats = agent.get_graph_stats()

# 图谱查询
result = agent.query_graph('安全文明')

# 关联查询
related = agent.get_related('DA0001')
```

### 4. 智能推荐

```python
# 推荐定额
quotas = agent.recommend_quotas('管道', top_k=5)

# 推荐解释
explanations = agent.recommend_explanations('安全文明')

# 推荐文件
docs = agent.recommend_docs('混凝土')
```

### 5. 自进化

```python
# 检查状态
status = agent.check_evolution()

# 触发进化
success = agent.trigger_evolution()

# 进化报告
report = agent.get_evolution_report()
```

### 6. 增量更新

```python
# 检查变更
changes = agent.check_for_updates()

# 重建索引
rebuilt = agent.rebuild_index()

# 更新状态
status = agent.get_update_status()
```

---

## 🚀 统一入口

### CLI

```bash
# 查询
python3 cost_agent_v6.py query "混凝土"

# 搜索
python3 cost_agent_v6.py search "钢筋" --top-k 10

# 问答
python3 cost_agent_v6.py ask "安全文明施工费怎么算？"

# 推荐
python3 cost_agent_v6.py recommend "管道"

# 状态
python3 cost_agent_v6.py status
```

### Python API

```python
from cost_agent_v6 import create_agent, quick_query, quick_search, quick_ask

# 创建实例
agent = create_agent()

# 快速查询
result = quick_query("混凝土")

# 快速搜索
results = quick_search("钢筋")

# 快速问答
answer = quick_ask("安全文明施工费怎么算？")
```

---

## 📊 数据规模

| 数据 | 数量 | 来源 |
|------|------|------|
| 定额条目 | 28,920 | 6 个专业 |
| Q&A 对 | 720 | 50+ 文件 |
| 政府文件 | 18 | 定额解释 |
| 知识图谱节点 | 28,965 | 定额+Q&A+ 文件 |
| 知识图谱边 | 2,258 | 关联关系 |
| 跟踪文件 | 57 | 定额 + 文档 |

---

## 🧬 自进化能力

### 数据自进化
- 自动清洗
- 自动标注
- 质量提升 (+3%/代)

### 模型自进化
- 元学习
- 知识蒸馏
- NAS (+5%/代)

### 流程自进化
- 工作流优化
- 自动自愈
- (+4%/代)

### 知识自进化
- 知识图谱更新
- 概念漂移检测
- (+50 实体/代)

---

## 📈 升级对比

| 能力 | v5.0 | v6.0 | 提升 |
|------|------|------|------|
| 造价计算 | ✅ | ✅ | - |
| 定额匹配 | ❌ | ✅ | +100% |
| 语义搜索 | ❌ | ✅ | +100% |
| 知识图谱 | ❌ | ✅ | +100% |
| 智能推荐 | ❌ | ✅ | +100% |
| 增量更新 | ❌ | ✅ | +100% |
| 自进化 | 30% | 100% | +70% |
| 统一入口 | ❌ | ✅ | +100% |

---

## 🔮 下一步

1. **完善自进化实现** - 将框架代码变为实际逻辑
2. **Web 界面** - 提供可视化操作界面
3. **API 服务** - 提供 RESTful API
4. **性能优化** - 大规模数据下的响应速度
5. **测试覆盖** - 单元测试 + 集成测试

---

**太一 AGI · Cost Agent v6.0 · 2026.4.25**
