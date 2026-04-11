#!/usr/bin/env python3
"""
💰 使用 mdb-tools 转换 Access 数据库为 Markdown

不依赖 pyodbc，使用 mdb-export 命令

作者：太一 AGI
创建：2026-04-11
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime


def get_mdb_tables(mdb_file: str) -> list:
    """获取 Access 数据库中的所有表"""
    try:
        result = subprocess.run(
            ["mdb-tables", "-1", mdb_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            tables = [t.strip() for t in result.stdout.strip().split('\n') if t.strip()]
            return tables
    except Exception as e:
        print(f"   ⚠️  获取表列表失败：{e}")
    return []


def export_table_to_dict(mdb_file: str, table_name: str) -> list:
    """导出表数据为字典列表"""
    try:
        # 导出为 JSON
        result = subprocess.run(
            ["mdb-json", mdb_file, table_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data
    except Exception as e:
        print(f"   ⚠️  导出表数据失败：{e}")
    return []


def convert_mdb_to_md(mdb_file: str, output_dir: Path) -> bool:
    """转换 Access 数据库为 Markdown"""
    file_name = Path(mdb_file).stem
    print(f"💾 转换 Access: {file_name}")
    
    # 检查 mdb-tools
    try:
        result = subprocess.run(["which", "mdb-tables"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ❌ 需要安装 mdb-tools: sudo apt install mdbtools\n")
            return False
    except Exception as e:
        print(f"   ⚠️  检查失败：{e}\n")
        return False
    
    # 获取表列表
    tables = get_mdb_tables(mdb_file)
    if not tables:
        print(f"   ⚠️  未找到表或文件损坏\n")
        return False
    
    print(f"   找到 {len(tables)} 个表")
    
    # 生成 Markdown
    md_lines = []
    md_lines.append(f"# 💾 {file_name}\n")
    md_lines.append(f"> **来源**: {mdb_file}\n")
    md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md_lines.append(f"> **表数量**: {len(tables)} 个\n")
    md_lines.append("")
    
    for table in tables[:10]:  # 限制 10 个表
        md_lines.append(f"## 📄 表：{table}\n")
        md_lines.append("")
        
        # 导出表结构
        try:
            result = subprocess.run(
                ["mdb-schema", mdb_file, table],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                md_lines.append("### 表结构\n\n```sql\n")
                md_lines.append(result.stdout)
                md_lines.append("```\n\n")
        except:
            pass
        
        # 导出数据 (前 20 行)
        try:
            result = subprocess.run(
                ["mdb-export", "-H", "-L", "comma", mdb_file, table],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    headers = [h.strip() for h in lines[0].split(',')]
                    md_lines.append("### 数据预览 (前 20 行)\n\n")
                    md_lines.append("| " + " | ".join(headers[:15]) + " |\n")
                    md_lines.append("|" + "|".join(["---"] * min(len(headers), 15)) + "|\n")
                    
                    for line in lines[1:21]:
                        values = [v.strip()[:50] for v in line.split(',')][:15]
                        md_lines.append("| " + " | ".join(values) + " |\n")
                    
                    md_lines.append(f"\n**共 {len(lines)-1} 行数据**\n\n")
        except Exception as e:
            md_lines.append(f"⚠️ 数据导出失败：{e}\n")
        
        md_lines.append("\n")
    
    # 保存
    output_file = output_dir / f"{file_name}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    
    print(f"   ✅ 已保存：{output_file.name}\n")
    return True


def main():
    """主函数"""
    print("="*60)
    print("💰 使用 mdb-tools 转换 Access 数据库为 Markdown")
    print("="*60)
    
    # 定额目录
    base_dirs = [
        "/home/nicola/下载/重庆 18 定额配套文件",
        "/home/nicola/下载",
    ]
    
    output_dir = Path("/home/nicola/.openclaw/workspace/skills/cost-agent/quota_md")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找第一个存在的目录
    base_dir = None
    for d in base_dirs:
        if Path(d).exists():
            base_dir = Path(d)
            break
    
    if not base_dir:
        print(f"❌ 定额目录不存在")
        return 1
    
    print(f"📂 使用目录：{base_dir}\n")
    
    # 查找 MDB 文件
    mdb_files = list(base_dir.rglob("*.mdb"))
    print(f"📊 找到 {len(mdb_files)} 个 MDB 文件\n")
    
    # 转换
    success = 0
    fail = 0
    
    for f in mdb_files[:10]:
        if convert_mdb_to_md(str(f), output_dir):
            success += 1
        else:
            fail += 1
    
    print("="*60)
    print(f"✅ 转换完成：成功 {success} 个，失败 {fail} 个")
    print(f"📁 输出目录：{output_dir}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
