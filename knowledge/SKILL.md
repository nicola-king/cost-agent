# 定额匹配器 (Quota Matcher)

> **版本**: 1.0.0  
> **来源**: cost-agent v6.0 / knowledge 模块  
> **独立发布**: ✅  
> **依赖**: 无（纯算法）  

---

## 🎯 功能

基于语义的定额智能匹配器，支持模糊搜索、多字段匹配、相似度排序。

## 📦 文件

| 文件 | 行数 | 功能 |
|------|------|------|
| `matcher.py` | 544 | 核心匹配引擎 |
| `knowledge_graph.py` | 349 | 知识图谱构建 |
| `recommendation.py` | 216 | 推荐策略 |
| `semantic_search.py` | 170 | 语义搜索 |
| `incremental_update.py` | 244 | 增量更新 |
| `visualizer.py` | 294 | 可视化 |

## 🚀 使用

```python
from knowledge.matcher import QuotaMatcher
matcher = QuotaMatcher()
results = matcher.match("人工平整场地", top_k=5)
```

---

*太一 AGI · 定额匹配器 v1.0*
