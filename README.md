# 🏗️ Cost.Agent (造价 Agent)

> **人法地，地法天，天法道，道法自然。**  
> **造价有道，自然而生。**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/nicola-king/cost-agent)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-red.svg)](https://python.org)

---

## 🎯 核心理念

```
造价有道，自然而生。

融合重庆 2018 市政定额与太一记忆宫殿
服务市政工程造价全过程
提供智能造价咨询与管理
```

---

## 🌟 高价值功能 (第一阶段)

### ✅ 投资估算 (快速估算)
```
- 类似项目造价指标
- 地区造价信息
- 建设规模估算
- 精度：±30%
```

### ✅ 工程量计算 (自动计算)
```
- 道路工程 (路基/路面/人行道)
- 桥梁工程 (基础/下部/上部/桥面)
- 管网工程 (沟槽/管道/检查井)
- 自动套用计算规则
```

### ✅ 定额套用 (智能匹配)
```
- 重庆 2018 市政定额
- 智能匹配定额子目
- 自动调整换算
- 计算合价
```

### ✅ 材料价格 (实时更新)
```
- 重庆造价信息
- 市场询价
- 供应商报价
- 价格趋势分析
```

### ✅ 变更签证 (智能审核)
```
- 变更申请审核
- 变更价款计算
- 签证流程管理
- 证据链管理
```

### ✅ 结算审核 (自动核对)
```
- 竣工结算审核
- 工程量核对
- 价款调整
- 核减核增分析
```

---

## 📚 定额知识库

### 重庆 2018 市政定额
```
- 市政工程计价定额
- 机械台班定额
- 仪器仪表定额
- 费用定额
- 综合解释 (1-7 号)
```

### 核心概念
```
- 工程量计算规则
- 综合单价组成
- 费用组成 (分部分项/措施/其他/规费/税金)
- 材料价格组成
```

---

## 🚀 快速开始

### 安装
```bash
git clone https://github.com/nicola-king/cost-agent.git
cd cost-agent
pip install -r requirements.txt
```

### 使用
```python
from cost_agent import CostAgent

agent = CostAgent(region="重庆", quota_version="2018")

# 投资估算
estimate = agent.quick_estimate(
    project_type="道路工程",
    length=1000,  # 米
    width=20,     # 米
    region="重庆"
)

# 工程量计算
quantities = agent.calculate_quantities(
    project_type="道路工程",
    drawings="施工图纸.pdf"
)

# 定额套用
quota_price = agent.apply_quota(
    item_name="路基石方",
    quantity=10000,
    unit="m³"
)
```

---

## 📊 技术架构

```
Cost.Agent/
├── cost_classics.py          # 定额知识库
├── cost_knowledge_system.py  # 核心概念体系
├── cost_agent_full.py        # 主程序 (完整版)
├── quota_db/                 # 定额数据库
│   └── chongqing_2018/       # 重庆 2018 定额
├── material_prices/          # 材料价格
│   └── chongqing/            # 重庆地区
└── memory_palace/            # 太一记忆宫殿
```

---

## 🙏 致谢

- **太一 AGI** - 记忆宫殿系统
- **重庆市建设工程造价管理总站** - 2018 定额
- **所有贡献者** - 造价智能化

---

**🏗️ Cost.Agent - 造价有道，自然而生。**
