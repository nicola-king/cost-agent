# 成本跟踪 (Cost Tracking)

> **版本**: 1.0.0  
> **来源**: cost-agent v6.0 / cost_tracking 模块  
> **独立发布**: ✅  
> **依赖**: calculators/  

---

## 🎯 功能

工程成本实时跟踪、自进化成本分析、偏差预警。

## 📦 文件

| 文件 | 功能 |
|------|------|
| `self_evolution.py` | 成本自进化核心 |
| `self_evolution_cost_tracker_agent.py` | 成本跟踪 Agent |

## 🚀 使用

```python
from cost_tracking.self_evolution import CostEvolution
tracker = CostEvolution()
tracker.track(project_data)
```

---

*太一 AGI · 成本跟踪 v1.0*
