# 定额数据 (Quota Data)

> **版本**: 1.0.0  
> **来源**: cost-agent v6.0 / data/quotas 模块  
> **独立发布**: ✅  
> **依赖**: 无（纯数据）  

---

## 🎯 内容

重庆市2018计价定额完整数据集，共 **28,920 条**定额记录。

## 📦 数据文件

| 文件 | 专业 | 定额数 | 大小 |
|------|------|--------|------|
| `building.json` | 建筑工程 | 1,645 | 1.6MB |
| `decoration.json` | 装饰装修 | 1,609 | 1.6MB |
| `installation.json` | 安装工程 | 16,511 | 27.6MB |
| `municipal.json` | 市政工程 | 4,272 | 5.8MB |
| `prefab.json` | 装配式 | 368 | 0.5MB |
| `transit.json` | 轨道交通 | 4,515 | 5.2MB |
| **合计** | **6 专业** | **28,920** | **42.4MB** |

## 📋 数据结构

```json
{
  "prefixes": {
    "AA": [
      {
        "deh": "AA0001",
        "xmmc": "人工平整场地",
        "dw": "100m2",
        "dj": 409.19,
        "rgf": 357.9,
        "clf": 0.0,
        "jxf": 0.0,
        "chapter": "A.1 土方工程",
        "materials": [...]
      }
    ]
  },
  "total": 1645,
  "category": "建筑工程"
}
```

## 🚀 使用

```python
import json
data = json.load(open("data/quotas/building.json"))
for prefix, items in data["prefixes"].items():
    print(f"{prefix}: {len(items)} 条")
```

---

*太一 AGI · 定额数据 v1.0 · 重庆2018计价定额*
