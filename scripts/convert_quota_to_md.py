#!/usr/bin/env python3
"""
💰 定额转 Markdown 文件

将重庆 2018 定额 Access/Excel 文件转换为 Markdown 格式
便于阅读、维护和导入数据库

作者：太一 AGI
创建：2026-04-11
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def convert_excel_to_md(excel_file: str, output_dir: str):
    """转换 Excel 定额文件为 Markdown"""
    print(f"\n📊 转换 Excel 文件：{excel_file}")
    
    try:
        # 读取 Excel
        df = pd.read_excel(excel_file)
        print(f"   ✅ 读取成功：{len(df)} 行")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 生成 Markdown
        md_content = generate_quota_md(df, excel_file)
        
        # 保存 Markdown
        output_file = output_path / f"{Path(excel_file).stem}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        print(f"   ✅ 已保存：{output_file}")
        
        return True
    
    except Exception as e:
        print(f"   ❌ 转换失败：{e}")
        return False


def generate_quota_md(df: pd.DataFrame, source_file: str) -> str:
    """生成 Markdown 内容"""
    md = []
    
    # 标题
    md.append(f"# 💰 重庆 2018 市政定额\n")
    md.append(f"> **来源**: {source_file}\n")
    md.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append(f"> **行数**: {len(df)} 行\n")
    md.append("")
    
    # 目录
    md.append("## 📑 目录\n")
    md.append("")
    md.append("- [定额列表](#定额列表)\n")
    md.append("- [统计信息](#统计信息)\n")
    md.append("")
    
    # 定额列表
    md.append("## 定额列表\n")
    md.append("")
    md.append("| 序号 | 定额编号 | 项目名称 | 单位 | 人工费 | 材料费 | 机械费 | 基价 |\n")
    md.append("|------|----------|----------|------|--------|--------|--------|------|\n")
    
    # 遍历数据行
    for idx, row in df.iterrows():
        try:
            # 尝试获取常见列名
            code = row.get('定额编号', row.get('编号', row.get('code', '')))
            name = row.get('项目名称', row.get('名称', row.get('name', '')))
            unit = row.get('单位', row.get('unit', ''))
            labor = row.get('人工费', row.get('人工', row.get('labor', 0)))
            material = row.get('材料费', row.get('材料', row.get('material', 0)))
            machine = row.get('机械费', row.get('机械', row.get('machine', 0)))
            base_price = row.get('基价', row.get('单价', row.get('price', 0)))
            
            md.append(f"| {idx+1} | {code} | {name} | {unit} | {labor} | {material} | {machine} | {base_price} |\n")
        
        except Exception as e:
            md.append(f"| {idx+1} | - | 解析错误 | - | - | - | - | - |\n")
    
    md.append("")
    
    # 统计信息
    md.append("## 统计信息\n")
    md.append("")
    
    # 数值列统计
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols[:10]:  # 最多显示 10 列
        md.append(f"- **{col}**: 最小={df[col].min():,.2f}, 最大={df[col].max():,.2f}, 平均={df[col].mean():,.2f}\n")
    
    md.append("")
    
    # 说明
    md.append("---\n")
    md.append("\n**注意**: 本文件由程序自动生成，仅供参考。请以官方定额为准。\n")
    
    return "\n".join(md)


def main():
    """主函数"""
    print("="*60)
    print("💰 定额转 Markdown 工具")
    print("="*60)
    
    # 定额文件目录
    quota_dir = Path("/home/nicola/下载/重庆 18 定额配套文件/重庆 2018 定额 Access")
    output_dir = Path("/home/nicola/.openclaw/workspace/skills/cost-agent/quota_md")
    
    if not quota_dir.exists():
        print(f"❌ 定额目录不存在：{quota_dir}")
        return 1
    
    # 查找 Excel 文件
    excel_files = list(quota_dir.glob("*.xls*"))
    print(f"\n📂 找到 {len(excel_files)} 个 Excel 文件")
    
    # 转换
    success_count = 0
    for excel_file in excel_files:
        if convert_excel_to_md(str(excel_file), str(output_dir)):
            success_count += 1
    
    print(f"\n✅ 转换完成：{success_count}/{len(excel_files)} 个文件")
    print(f"📁 输出目录：{output_dir}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
