#!/usr/bin/env python3
"""
💰 批量转换定额文件为 Markdown

将重庆 2018 定额所有 Access/Excel 文件转换为 Markdown 格式
便于阅读、维护和导入数据库

作者：太一 AGI
创建：2026-04-11
"""

import pandas as pd
import subprocess
from pathlib import Path
from datetime import datetime


def find_quota_files(base_dir: str):
    """查找所有定额文件"""
    print(f"📂 查找定额文件：{base_dir}")
    
    # 使用 pathlib 查找
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"   ❌ 目录不存在：{base_dir}")
        return []
    
    # 查找 Excel 和 Access 文件
    files = []
    files.extend(list(base_path.rglob("*.xls")))
    files.extend(list(base_path.rglob("*.xlsx")))
    files.extend(list(base_path.rglob("*.mdb")))
    files.extend(list(base_path.rglob("*.accdb")))
    
    print(f"   找到 {len(files)} 个文件\n")
    
    return [str(f) for f in files]


def convert_excel_to_md(excel_file: str, output_dir: Path):
    """转换 Excel 文件为 Markdown"""
    file_name = Path(excel_file).stem
    
    print(f"📊 转换：{file_name}")
    
    try:
        # 读取 Excel
        df = pd.read_excel(excel_file)
        print(f"   ✅ 读取成功：{len(df)} 行，{len(df.columns)} 列")
        
        # 生成 Markdown
        md_content = generate_quota_md(df, excel_file)
        
        # 保存 Markdown
        output_file = output_dir / f"{file_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        print(f"   ✅ 已保存：{output_file.name}\n")
        
        return True
    
    except Exception as e:
        print(f"   ❌ 转换失败：{e}\n")
        return False


def generate_quota_md(df: pd.DataFrame, source_file: str) -> str:
    """生成 Markdown 内容"""
    md = []
    
    # 标题
    file_name = Path(source_file).stem
    md.append(f"# 💰 {file_name}\n")
    md.append(f"> **来源**: {source_file}\n")
    md.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append(f"> **行数**: {len(df)} 行\n")
    md.append(f"> **列数**: {len(df.columns)} 列\n")
    md.append("")
    
    # 目录
    md.append("## 📑 目录\n")
    md.append("")
    md.append("- [数据预览](#数据预览)\n")
    md.append("- [完整数据](#完整数据)\n")
    md.append("- [统计信息](#统计信息)\n")
    md.append("")
    
    # 数据预览
    md.append("## 数据预览\n")
    md.append("")
    md.append("前 10 行数据：\n")
    md.append("")
    
    # 生成表格
    md.append("| 序号 |")
    for col in df.columns[:10]:  # 最多显示 10 列
        md.append(f" {col} |")
    md.append("\n")
    
    md.append("|------|")
    for _ in range(min(10, len(df.columns))):
        md.append("----------|")
    md.append("\n")
    
    # 数据行
    for idx, row in df.head(10).iterrows():
        md.append(f"| {idx+1} |")
        for col in df.columns[:10]:
            value = row.get(col, '')
            md.append(f" {value} |")
        md.append("\n")
    
    md.append("")
    
    # 完整数据
    md.append("## 完整数据\n")
    md.append("")
    md.append(f"共 {len(df)} 行数据，详见上方预览。\n")
    md.append("")
    
    # 统计信息
    md.append("## 统计信息\n")
    md.append("")
    
    # 数值列统计
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_cols) > 0:
        md.append("### 数值列统计\n")
        md.append("")
        
        for col in numeric_cols[:10]:  # 最多显示 10 列
            md.append(f"- **{col}**:\n")
            md.append(f"  - 最小值：{df[col].min():,.2f}\n")
            md.append(f"  - 最大值：{df[col].max():,.2f}\n")
            md.append(f"  - 平均值：{df[col].mean():,.2f}\n")
            md.append(f"  - 总和：{df[col].sum():,.2f}\n")
            md.append("\n")
    
    # 非数值列统计
    object_cols = df.select_dtypes(include=['object']).columns
    if len(object_cols) > 0:
        md.append("### 文本列统计\n")
        md.append("")
        
        for col in object_cols[:5]:  # 最多显示 5 列
            unique_count = df[col].nunique()
            md.append(f"- **{col}**: {unique_count} 个唯一值\n")
        md.append("\n")
    
    # 说明
    md.append("---\n")
    md.append("\n**注意**: 本文件由程序自动生成，仅供参考。请以官方定额为准。\n")
    
    return "\n".join(md)


def main():
    """主函数"""
    print("="*60)
    print("💰 批量转换定额文件为 Markdown")
    print("="*60)
    
    # 定额文件目录
    base_dirs = [
        "/home/nicola/下载/重庆 18 定额配套文件",
        "/home/nicola/下载",
    ]
    
    output_dir = Path("/home/nicola/.openclaw/workspace/skills/cost-agent/quota_md")
    output_dir.mkdir(exist_ok=True)
    
    # 查找第一个存在的目录
    base_dir = None
    for d in base_dirs:
        if Path(d).exists():
            base_dir = d
            break
    
    if not base_dir:
        print(f"❌ 定额目录不存在")
        return 1
    
    print(f"📂 使用目录：{base_dir}")
    
    # 查找文件
    files = find_quota_files(base_dir)
    
    # 转换
    success_count = 0
    fail_count = 0
    
    for file in files:
        if file.endswith(('.xls', '.xlsx')):
            if convert_excel_to_md(file, output_dir):
                success_count += 1
            else:
                fail_count += 1
    
    print(f"\n✅ 转换完成!")
    print(f"   成功：{success_count} 个")
    print(f"   失败：{fail_count} 个")
    print(f"   输出目录：{output_dir}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
