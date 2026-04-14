# 🏗️ Cost Agent v4.0 - 统一造价管理平台

> **版本**: v4.0 (完全融合版)  
> **创建时间**: 2026-04-11  
> **更新时间**: 2026-04-14 21:25  
> **融合来源**: 4 个造价相关 Agent  
> **作者**: 太一 AGI

---

## 🎯 项目简介

Cost Agent v4.0 是太一体系**统一的造价管理平台**，融合了 4 个造价相关 Agent 的核心能力：

| 来源 Agent | 融合模块 | 核心贡献 |
|-----------|---------|---------|
| **cost-agent (07-system)** | change_order/ | 变更签证管理 + VBA 自动化 |
| **cost-agent (08-emerged)** | cost_tracking/ | 自进化学习能力 |
| **civil-engineering-cost** | calculators/ | 造价计算引擎 |
| **cost-tracker** | cost_tracking/ | 成本追踪功能 |

---

## 🚀 核心功能

### 功能矩阵
| 功能模块 | 描述 | 状态 |
|---------|------|------|
| **造价计算** | 道路/桥梁/管网工程 | ✅ |
| **定额管理** | 100+ 条定额数据 | ✅ |
| **材料价格** | 30+ 种材料价格 | ✅ |
| **变更签证** | 全流程管理 + 证据链评分 | ✅ |
| **预警看板** | 🟢🟡🟠🔴四级预警 | ✅ |
| **成本追踪** | 实时追踪 + 分析 | ✅ |
| **报表生成** | 周报/月报/预算书 | ✅ |
| **VBA 自动化** | 7 个宏功能 | ✅ |
| **自进化学习** | 从历史数据学习 | ✅ |

### 效率提升
| 工作项 | 手动时间 | 自动时间 | 提升 |
|--------|---------|---------|------|
| 造价计算 | 1-2 小时 | 5 秒 | 99%+ |
| 周报编制 | 2-3 小时 | 5 秒 | 99.5% |
| 月报编制 | 1-2 天 | 10 秒 | 99.8% |
| 预警统计 | 30 分钟 | 实时 | 100% |

---

## 📁 文件结构

```
cost-agent/
├── README.md                          # 本文件
├── FUSION_ARCHITECTURE_v4.md          # 融合架构文档
│
├── core/                              # 核心引擎
│   ├── __init__.py
│   └── engine.py                      # CostAgent v4.0 主引擎
│
├── calculators/                       # 造价计算引擎
│   ├── cost.py                        # 道路/桥梁/管网计算
│   ├── material_prices.py             # 材料价格管理
│   ├── historical_data.py             # 历史数据
│   └── quota_database.py              # 定额数据库
│
├── change_order/                      # 变更签证管理
│   ├── README.md
│   ├── 变更签证管理细则.md
│   ├── 证据链清单模板.md
│   └── templates/
│       ├── 变更台账自动化宏.bas
│       ├── Excel 公式复制手册.md
│       └── VBA 宏导入与使用指南.md
│
├── cost_tracking/                     # 成本追踪
│   ├── self_evolution.py              # 自进化模块
│   └── self_evolution_cost_tracker_agent.py
│
├── reports/                           # 报表生成
│   └── (自动生成)
│
├── data/                              # 数据目录
│   ├── quotas/                        # 定额数据
│   ├── materials/                     # 材料价格
│   ├── projects/                      # 历史项目
│   └── knowledge/                     # 知识库
│
└── quota_md/                          # 定额文档 (51 个文件)
```

---

## 🚀 快速开始

### 命令行使用

```bash
# 进入目录
cd skills/07-system/cost-agent

# 显示仪表板
python3 core/engine.py

# 道路工程造价计算
python3 core/engine.py road -l 1000 -w 20 -s "沥青混凝土路面"

# 桥梁工程造价计算
python3 core/engine.py bridge -s 30 -w 15 -t "预应力混凝土简支梁"

# 管网工程造价计算
python3 core/engine.py pipeline -d DN800 -l 500 -m "HDPE 双壁波纹管"

# 添加变更签证
python3 core/engine.py change -t B -a 800000 -d "经纬大道管径变更"

# 成本追踪
python3 core/engine.py track -p "xx 道路工程" -a 500000

# 生成报表
python3 core/engine.py report -t weekly

# 自进化学习
python3 core/engine.py learn -d '{"project": "test", "cost": 1000000}'
```

### Python API 使用

```python
from core.engine import CostAgent

# 创建 Agent
agent = CostAgent(region="重庆", standard="2018 定额")

# 道路工程造价计算
result = agent.calculate_road(length=1000, width=20, structure="沥青混凝土路面")
print(f"总造价：¥{result['total_cost']:,.2f}")

# 桥梁工程造价计算
result = agent.calculate_bridge(span=30, width=15, structure="预应力混凝土简支梁")

# 管网工程造价计算
result = agent.calculate_pipeline(diameter="DN800", length=500, material="HDPE 双壁波纹管")

# 添加变更签证
change = agent.add_change_order(type="B", amount=800000, description="管径变更")

# 成本追踪
agent.track_cost(project="xx 道路工程", amount=500000)

# 生成报表
report_path = agent.generate_report("weekly")

# 自进化学习
agent.learn({"project": "completed_001", "cost": 1000000})
```

---

## 📊 数据统计

### 定额数据
| 类别 | 数量 |
|------|------|
| **总定额数** | **100+ 条** |
| 道路工程 | 30+ 条 |
| 桥梁工程 | 25+ 条 |
| 管网工程 | 25+ 条 |
| 机械台班 | 20+ 条 |

### 材料价格
| 类别 | 数量 |
|------|------|
| **总材料数** | **30+ 种** |
| 钢材 | 8 种 |
| 混凝土 | 5 种 |
| 管材 | 10 种 |
| 其他 | 7 种 |

### 变更签证
| 功能 | 状态 |
|------|------|
| 变更台账 | ✅ 1000 条容量 |
| 签证类型 | ✅ 6 类 |
| 预警级别 | ✅ 4 级 |
| 证据评分 | ✅ 100 分制 |

---

## 🎯 融合架构

```
┌─────────────────────────────────────────────────────────┐
│              Cost Agent v4.0                            │
│          (统一造价管理平台)                              │
└─────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  计算引擎层  │    │  管理层      │    │  追踪层      │
│              │    │              │    │              │
│ • 道路工程   │    │ • 变更签证   │    │ • 成本记录   │
│ • 桥梁工程   │    │ • 证据链     │    │ • 成本分析   │
│ • 管网工程   │    │ • 预警看板   │    │ • 趋势分析   │
│ • 定额套用   │    │ • 报表生成   │    │ • 自进化     │
│ • 材料价格   │    │ • VBA 自动化  │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
                              │
                              ▼
                    ┌──────────────┐
                    │  数据支撑层  │
                    │              │
                    │ • 定额数据库 │
                    │ • 材料价格库 │
                    │ • 历史项目库 │
                    └──────────────┘
```

---

## 🔧 模块说明

### 1. calculators/ (造价计算引擎)

**来源**: `civil-engineering-cost/` + `08-emerged/cost-agent/`

**核心功能**:
- 道路工程造价计算
- 桥梁工程造价计算
- 管网工程造价计算
- 定额套用
- 材料价格管理

**使用示例**:
```python
from calculators.cost import RoadCalculator

calc = RoadCalculator(region="重庆", standard="2018 定额")
result = calc.calculate(length=1000, width=20, structure="沥青混凝土路面")
```

---

### 2. change_order/ (变更签证管理)

**来源**: 保留 v3.0 完整功能

**核心功能**:
- 变更台账管理（A/B/C/D 四类）
- 6 类签证管理
- 证据链 100 分制评分
- 四级预警（🟢🟡🟠🔴）
- 周报/月报自动生成
- VBA 自动化（7 个宏）

**使用文档**: `change_order/README.md`

---

### 3. cost_tracking/ (成本追踪)

**来源**: `cost-tracker/` + `08-emerged/cost-agent/`

**核心功能**:
- 成本实时记录
- 多维度成本分析
- 成本趋势预测
- 自进化学习

**使用示例**:
```python
from cost_tracking.self_evolution import SelfEvolution

evolution = SelfEvolution()
evolution.learn_from_project(project_data)
prediction = evolution.predict_cost(new_project)
```

---

## 📈 版本演进

| 版本 | 时间 | 核心功能 | 状态 |
|------|------|---------|------|
| v1.0 | 2026-04-11 | 定额查询 | ✅ |
| v2.0 | 2026-04-11 | 造价计算 | ✅ |
| v3.0 | 2026-04-14 | 变更签证管理 | ✅ |
| **v4.0** | **2026-04-14** | **4 合 1 完全融合** | ✅ **当前** |

---

## 📞 相关链接

| 链接 | 说明 |
|------|------|
| **GitHub** | https://github.com/nicola-king/cost-agent |
| **融合架构** | `FUSION_ARCHITECTURE_v4.md` |
| **变更签证** | `change_order/README.md` |
| **计算引擎** | `calculators/cost.py` |

---

## 🙏 致谢

- **SAYELF** - 市政工程建设管理指导
- **太一 AGI** - 4 个造价 Agent 融合开发

---

**太一 AGI · Cost Agent v4.0 · 2026-04-14**

**版本**: v4.0 (完全融合版)  
**融合来源**: 4 个造价相关 Agent  
**GitHub**: https://github.com/nicola-king/cost-agent
