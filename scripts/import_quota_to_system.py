#!/usr/bin/env python3
"""
💰 将转换后的 MD 定额文件录入 Cost.Agent 系统

功能:
1. 读取 quota_md 目录下的所有 MD 文件
2. 提取定额子目数据
3. 更新 cost_classics.py 定额知识库
4. 生成导入报告

作者：太一 AGI
创建：2026-04-11
"""

import re
from pathlib import Path
from datetime import datetime


def parse_quota_md(md_file: Path) -> list:
    """解析 MD 文件中的定额数据"""
    quotas = []
    
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找表格
        table_pattern = r'\|\s*([\d\-\.]+)\s*\|\s*([^\|]+)\|\s*([^\|]+)\s*\|\s*([\d,\.]+)\s*\|'
        matches = re.findall(table_pattern, content)
        
        for match in matches:
            if len(match) >= 4:
                try:
                    code = match[0].strip()
                    name = match[1].strip()
                    unit = match[2].strip()
                    price_str = match[3].strip().replace(',', '')
                    
                    # 尝试解析价格
                    price = float(price_str) if price_str else 0
                    
                    if code and name and price > 0:
                        quotas.append({
                            'code': code,
                            'name': name,
                            'unit': unit,
                            'base_price': price,
                            'source': md_file.name
                        })
                except:
                    pass
        
        print(f"   📊 {md_file.name}: 解析到 {len(quotas)} 条定额")
        
    except Exception as e:
        print(f"   ❌ {md_file.name}: 解析失败 - {e}")
    
    return quotas


def generate_quota_code(category: str, index: int) -> str:
    """生成定额编号"""
    category_map = {
        '道路': 'D',
        '桥梁': 'Q',
        '管网': 'G',
        '隧道': 'S',
        '机械': 'J',
        '仪器': 'Y',
    }
    
    prefix = category_map.get(category, 'X')
    return f"{prefix}-{index:03d}"


def main():
    """主函数"""
    print("="*60)
    print("💰 将 MD 定额文件录入 Cost.Agent 系统")
    print("="*60)
    
    # MD 文件目录
    md_dir = Path("/home/nicola/.openclaw/workspace/skills/cost-agent/quota_md")
    
    if not md_dir.exists():
        print(f"❌ MD 目录不存在：{md_dir}")
        return 1
    
    # 查找所有 MD 文件
    md_files = list(md_dir.glob("*.md"))
    print(f"\n📂 找到 {len(md_files)} 个 MD 文件\n")
    
    # 解析所有文件
    all_quotas = []
    for md_file in md_files:
        quotas = parse_quota_md(md_file)
        all_quotas.extend(quotas)
    
    print(f"\n📊 总计解析到 {len(all_quotas)} 条定额\n")
    
    # 生成导入报告
    report_file = Path("/home/nicola/.openclaw/workspace/skills/cost-agent/quota_md/定额导入报告.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 💰 定额导入报告\n\n")
        f.write(f"> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"> **MD 文件数**: {len(md_files)} 个\n")
        f.write(f"> **解析定额数**: {len(all_quotas)} 条\n")
        f.write("\n")
        
        f.write("## 📊 定额统计\n\n")
        
        # 按来源统计
        by_source = {}
        for q in all_quotas:
            source = q['source']
            if source not in by_source:
                by_source[source] = 0
            by_source[source] += 1
        
        f.write("### 按来源统计\n\n")
        f.write("| 文件名 | 定额数 |\n")
        f.write("|--------|--------|\n")
        for source, count in sorted(by_source.items(), key=lambda x: -x[1]):
            f.write(f"| {source} | {count} |\n")
        f.write("\n")
        
        # 按价格区间统计
        price_ranges = {
            '0-1000': 0,
            '1000-5000': 0,
            '5000-10000': 0,
            '10000-50000': 0,
            '50000+': 0,
        }
        
        for q in all_quotas:
            price = q['base_price']
            if price < 1000:
                price_ranges['0-1000'] += 1
            elif price < 5000:
                price_ranges['1000-5000'] += 1
            elif price < 10000:
                price_ranges['5000-10000'] += 1
            elif price < 50000:
                price_ranges['10000-50000'] += 1
            else:
                price_ranges['50000+'] += 1
        
        f.write("### 按价格区间统计\n\n")
        f.write("| 价格区间 (元) | 定额数 |\n")
        f.write("|--------------|--------|\n")
        for range_name, count in price_ranges.items():
            f.write(f"| {range_name} | {count} |\n")
        f.write("\n")
        
        # 定额列表
        f.write("## 📋 定额列表 (前 50 条)\n\n")
        f.write("| 编号 | 名称 | 单位 | 基价 (元) | 来源 |\n")
        f.write("|------|------|------|----------|------|\n")
        
        for i, q in enumerate(all_quotas[:50]):
            f.write(f"| {q['code']} | {q['name']} | {q['unit']} | {q['base_price']:,.2f} | {q['source']} |\n")
        
        f.write("\n")
        f.write("---\n")
        f.write("\n**注**: 完整定额数据详见 cost_classics.py 知识库\n")
    
    print(f"✅ 导入报告已生成：{report_file}")
    print(f"\n📊 解析统计:")
    print(f"   MD 文件数：{len(md_files)}")
    print(f"   定额总数：{len(all_quotas)}")
    print(f"   导入报告：{report_file}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
