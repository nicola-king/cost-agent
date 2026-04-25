# 造价计算器 (Cost Calculator)

> **版本**: 1.0.0  
> **来源**: cost-agent v6.0 / calculators 模块  
> **独立发布**: ✅  
> **依赖**: knowledge/ (可选)  

---

## 🎯 功能

工程造价计算、历史数据分析、材料价格管理、定额数据库查询。

## 📦 文件

| 文件 | 功能 |
|------|------|
| `cost.py` | 核心造价计算 |
| `historical_data.py` | 历史数据分析 |
| `material_prices.py` | 材料价格管理 |
| `quota_database.py` | 定额数据库查询 |

## 🚀 使用

```python
from calculators.cost import CostCalculator
calc = CostCalculator()
result = calc.calculate({"items": [...]})
```

---

*太一 AGI · 造价计算器 v1.0*
