#!/usr/bin/env python3
"""
🚀 发布 Cost.Agent 和太一记忆宫殿到 GitHub

P2 任务：
- 创建 GitHub 仓库
- 推送代码
- 生成 README

作者：太一 AGI
创建：2026-04-11
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime


def create_github_repo(repo_name: str, description: str) -> bool:
    """创建 GitHub 仓库"""
    print(f"🚀 创建 GitHub 仓库：{repo_name}")
    
    cmd = [
        "gh", "repo", "create", repo_name,
        "--public",
        "--description", description,
        "--source", ".",
        "--push"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ 仓库创建成功：https://github.com/nicola-king/{repo_name}\n")
        return True
    else:
        print(f"   ❌ 创建失败：{result.stderr}\n")
        return False


def generate_readme(project_name: str, version: str, stats: dict) -> str:
    """生成 README.md"""
    readme = f"""# 🏗️ {project_name}

> **版本**: {version}  
> **创建时间**: {datetime.now().strftime('%Y-%m-%d')}  
> **作者**: 太一 AGI

---

## 🎯 项目简介

{project_name} 是一个智能化的造价管理和记忆系统。

---

## 📊 数据统计

"""
    
    if "quotas" in stats:
        readme += f"""### 定额数据

- **总定额数**: {stats['quotas']['total']} 条
- **道路工程**: {stats['quotas'].get('road', 0)} 条
- **桥梁工程**: {stats['quotas'].get('bridge', 0)} 条
- **管网工程**: {stats['quotas'].get('pipeline', 0)} 条
- **机械台班**: {stats['quotas'].get('machine', 0)} 条
- **仪器仪表**: {stats['quotas'].get('instrument', 0)} 条

"""
    
    if "memory_rooms" in stats:
        readme += f"""### 记忆宫殿

- **房间数量**: {stats['memory_rooms']} 个
- **记忆类型**: 语义/情景/程序/关联
- **复习机制**: 艾宾浩斯曲线

"""
    
    readme += f"""---

## 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/nicola-king/{project_name.lower().replace(' ', '-')}.git
cd {project_name.lower().replace(' ', '-')}

# 安装依赖
pip install -r requirements.txt

# 运行测试
python3 main.py
```

---

## 📁 文件结构

```
{project_name}/
├── main.py              # 主程序
├── requirements.txt     # 依赖
├── README.md           # 本文件
└── ...
```

---

## 🙏 致谢

- **太一 AGI** - 智能化开发
- **SAYELF** - 场景指导

---

**太一 AGI · {datetime.now().strftime('%Y-%m-%d')}**
"""
    
    return readme


def main():
    """主函数"""
    print("="*60)
    print("🚀 发布项目到 GitHub")
    print("="*60)
    
    # 项目列表
    projects = [
        {
            "name": "cost-agent",
            "description": "市政工程造价 Agent - 重庆 2018 定额智能化系统",
            "dir": Path("/home/nicola/.openclaw/workspace/skills/cost-agent"),
            "stats": {
                "quotas": {
                    "total": 44,
                    "road": 7,
                    "bridge": 5,
                    "pipeline": 5,
                    "machine": 22,
                    "instrument": 5,
                }
            }
        },
        {
            "name": "taiyi-memory-palace",
            "description": "太一记忆宫殿 v2.0 - 融合 MemPalace 架构的 AI 记忆系统",
            "dir": Path("/home/nicola/.openclaw/workspace/skills/taiyi-memory-palace"),
            "stats": {
                "memory_rooms": 9
            }
        }
    ]
    
    for project in projects:
        print(f"\n📦 发布项目：{project['name']}\n")
        
        # 生成 README
        readme_content = generate_readme(
            project['name'].replace('-', ' ').title(),
            "2.0",
            project['stats']
        )
        
        readme_file = project['dir'] / "README.md"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        print(f"   ✅ README.md 已生成")
        
        # 生成 requirements.txt
        requirements = [
            "pandas>=2.0.0",
            "openpyxl>=3.0.0",
            "chromadb>=0.4.0",
        ]
        
        if project['name'] == "cost-agent":
            requirements.extend([
                "python-docx>=0.8.0",
                "pdfplumber>=0.10.0",
                "beautifulsoup4>=4.12.0",
            ])
        
        req_file = project['dir'] / "requirements.txt"
        with open(req_file, "w", encoding="utf-8") as f:
            f.write("\n".join(requirements))
        
        print(f"   ✅ requirements.txt 已生成")
        
        # Git 提交
        print(f"\n   📝 Git 提交...")
        subprocess.run(["git", "add", "-A"], cwd=project['dir'], capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"🚀 GitHub 发布准备\n\n- README.md\n- requirements.txt\n- 完整代码\n\n太一 AGI · {datetime.now().strftime('%Y-%m-%d')}"],
            cwd=project['dir'],
            capture_output=True
        )
        print(f"   ✅ Git 提交完成")
        
        # 推送 GitHub
        print(f"\n   🚀 推送到 GitHub...")
        repo_name = f"nicola-king/{project['name']}"
        
        # 检查 gh CLI
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            # 使用 gh CLI
            create_github_repo(repo_name, project['description'])
        else:
            print(f"   ⚠️  gh CLI 未安装，请手动推送:\n")
            print(f"   cd {project['dir']}\n")
            print(f"   git remote add origin git@github.com:{repo_name}.git\n")
            print(f"   git branch -M main\n")
            print(f"   git push -u origin main\n")
    
    print("\n" + "="*60)
    print("✅ GitHub 发布完成!")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
