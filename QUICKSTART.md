# 🏗️ Cost.Agent 快速开始指南

> **版本**: 2.0  
> **最后更新**: 2026-04-11  
> **定额数据**: 44 条 (道路 7/桥梁 5/管网 5/机械 22/仪器 5)

---

## 🎯 快速开始

### 1. 安装依赖

```bash
# 基础依赖
pip install pandas openpyxl --break-system-packages

# 可选：文档转换
pip install python-docx pdfplumber beautifulsoup4 --break-system-packages

# 可选：Access 数据库
pip install pyodbc --break-system-packages
```

### 2. 测试运行

```bash
cd /home/nicola/.openclaw/workspace/skills/cost-agent

# 测试定额知识库
python3 cost_classics_v2.py

# 测试主程序
python3 cost_agent_full.py
```

### 3. 使用示例

```python
from cost_classics_v2 import (
    get_quota_by_name,
    get_quota_by_code,
    calculate_direct_cost,
    calculate_total_cost,
    get_statistics
)

# 查询定额
quotas = get_quota_by_name("路基石方")
print(f"找到 {len(quotas)} 条定额")
print(f"名称：{quotas[0].name}")
print(f"单价：¥{quotas[0].base_price:,.2f}/{quotas[0].unit}")

# 计算造价
direct_cost = calculate_direct_cost(quotas[0], quantity=10)
total_info = calculate_total_cost(direct_cost)
print(f"直接费：¥{direct_cost:,.2f}")
print(f"总造价：¥{total_info['total']:,.2f}")

# 查看统计
stats = get_statistics()
print(f"总定额数：{stats['total_quotas']}")
print(f"价格范围：¥{stats['price_range']['min']:,.2f} - ¥{stats['price_range']['max']:,.2f}")
```

---

## 📊 定额数据

### 道路工程 (7 条)

| 编号 | 名称 | 单位 | 基价 (元) |
|------|------|------|----------|
| 1-1 | 人工挖土方 | 100m³ | 2,800 |
| 1-2 | 机械挖土方 | 1000m³ | 9,700 |
| 1-3 | 路基石方 | 1000m³ | 15,900 |
| 2-1 | 沥青混凝土路面 | 1000㎡ | 87,000 |
| 2-2 | 水泥混凝土路面 | 1000㎡ | 76,100 |
| 2-3 | 路缘石安装 | 100m | 4,230 |
| 3-1 | 人行道铺装 | 100㎡ | 5,900 |

### 桥梁工程 (5 条)

| 编号 | 名称 | 单位 | 基价 (元) |
|------|------|------|----------|
| 4-1 | 钻孔灌注桩 | 10m³ | 24,100 |
| 4-2 | 扩大基础 | 10m³ | 11,500 |
| 5-1 | 桥墩浇筑 | 10m³ | 14,500 |
| 6-1 | 预应力混凝土梁 | 10m³ | 23,600 |
| 7-1 | 桥面铺装 | 100㎡ | 21,700 |

### 管网工程 (5 条)

| 编号 | 名称 | 单位 | 基价 (元) |
|------|------|------|----------|
| 8-1 | 沟槽开挖 | 1000m³ | 9,000 |
| 8-2 | 沟槽回填 | 1000m³ | 6,000 |
| 9-1 | HDPE 双壁波纹管 DN500 | 100m | 31,700 |
| 9-2 | HDPE 双壁波纹管 DN800 | 100m | 56,800 |
| 10-1 | 砖砌检查井 | 座 | 4,500 |

### 机械台班 (22 条)

| 类型 | 规格范围 | 单价范围 (元/台班) |
|------|---------|------------------|
| 推土机 | 50-165kW | 368-1,051 |
| 装载机 | 1-3m³ | 581-981 |
| 起重机 | 3-40t | 214-1,981 |
| 自卸汽车 | 5-25t | 381-1,181 |

### 仪器仪表 (5 条)

| 名称 | 单价 (元/台班) |
|------|--------------|
| 水准仪 | 50 |
| 经纬仪 | 80 |
| 全站仪 | 150 |
| GPS 接收机 | 200 |
| 测距仪 | 100 |

---

## 💰 费用标准

### 措施项目费

| 项目 | 费率 | 计算基数 |
|------|------|---------|
| 安全文明施工费 | 2.5% | 分部分项工程费 |
| 夜间施工费 | 1.0% | 分部分项工程费 |
| 二次搬运费 | 0.5% | 分部分项工程费 |
| 冬雨季施工费 | 0.8% | 分部分项工程费 |

### 规费

| 项目 | 费率 | 计算基数 |
|------|------|---------|
| 社会保险费 | 18% | 人工费 |
| 住房公积金 | 10% | 人工费 |
| **合计** | **28%** | **人工费** |

### 税金

| 项目 | 税率 | 计算基数 |
|------|------|---------|
| 增值税 | 9% | 税前造价 |

---

## 🛠️ 工具脚本

### 批量转换定额为 MD

```bash
python3 scripts/convert_all_quota_to_md.py
```

支持格式：
- Excel (.xls/.xlsx) → Markdown
- Word (.doc/.docx) → Markdown
- PDF (.pdf) → Markdown
- HTML (.html/.htm) → Markdown

### 导入 MD 定额到系统

```bash
python3 scripts/import_quota_to_system.py
```

功能：
- 解析 MD 文件中的定额数据
- 生成导入报告
- 统计定额数量和价格区间

---

## 📁 文件结构

```
cost-agent/
├── README.md                      # 项目说明
├── QUICKSTART.md                  # 快速开始 (本文件)
├── cost_classics_v2.py            # 定额知识库 v2.0 (44 条)
├── cost_agent_full.py             # 主程序 (完整版)
├── quota_data.json                # 导出的 JSON 数据
├── scripts/
│   ├── convert_all_quota_to_md.py # 批量转换脚本
│   ├── import_quota_to_system.py  # 导入系统脚本
│   ├── convert_all_quotas.py      # 定额转换
│   └── convert_all_docs.py        # 文档转换
└── quota_md/
    ├── 42 个 MD 文件                # 已转换定额
    ├── 定额导入报告.md              # 导入报告
    └── 其他文档                    # 配套文件
```

---

## 📈 数据统计

### 定额统计

```
总定额数：44 条
- 道路工程：7 条 (16%)
- 桥梁工程：5 条 (11%)
- 管网工程：5 条 (11%)
- 机械台班：22 条 (50%)
- 仪器仪表：5 条 (11%)

价格范围:
- 最低：¥50.00 (水准仪)
- 最高：¥87,000.00 (沥青混凝土路面)
- 平均：¥9,607.73
```

### 文件统计

```
已转换 MD 文件：42 个
已解析定额：250 条
已录入系统：44 条
```

---

## 🚀 下一步计划

### 本周 (2026-04-11 ~ 04-17)
- [ ] 扩展定额数据到 100+ 条
- [ ] 转换 Access 数据库 (4 个.mdb)
- [ ] 完善造价计算功能

### 下周 (2026-04-17 ~ 04-24)
- [ ] 录入建筑工程定额
- [ ] 录入安装工程定额
- [ ] 录入轨道工程定额

### 月底 (2026-04-24 ~ 04-30)
- [ ] 完成所有定额录入 (500+ 条)
- [ ] GitHub 发布
- [ ] 创建 Web 界面

---

## 🙏 致谢

- **重庆市建设工程造价管理总站** - 2018 定额编制
- **太一 AGI** - 智能化转换与录入
- **SAYELF** - 市政造价场景指导

---

**🏗️ Cost.Agent - 造价有道，自然而生。**

**太一 AGI · 2026-04-11**
