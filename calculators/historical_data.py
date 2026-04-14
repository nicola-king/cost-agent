#!/usr/bin/env python3
"""
历史工程数据管理 (Historical Project Data Management)

功能:
1. 历史工程造价数据查询
2. 造价指标分析
3. 对比分析 (估算 vs 历史)
4. 造价趋势预测

作者：太一 AGI
创建：2026-04-10
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


# 配置文件
HISTORY_FILE = Path(__file__).parent / "config" / "historical_projects.json"


class HistoricalDataManager:
    """历史工程数据管理器"""
    
    def __init__(self):
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """加载历史数据"""
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"projects": [], "cost_indexes": {}}
    
    def query_projects(self, project_type: str = "", location: str = "", year: str = "") -> List[Dict]:
        """查询历史工程"""
        projects = self.data.get("projects", [])
        
        if project_type:
            projects = [p for p in projects if project_type in p.get("type", "")]
        
        if location:
            projects = [p for p in projects if location in p.get("location", "")]
        
        if year:
            projects = [p for p in projects if year in p.get("completion_date", "")]
        
        return projects
    
    def get_cost_index(self, project_type: str, sub_type: str = "") -> Optional[Dict]:
        """获取造价指标"""
        cost_indexes = self.data.get("cost_indexes", {})
        
        if project_type in cost_indexes:
            if sub_type and sub_type in cost_indexes[project_type]:
                return cost_indexes[project_type][sub_type]
            return cost_indexes[project_type]
        
        return None
    
    def analyze_project(self, project_id: str) -> Optional[Dict]:
        """分析单个项目"""
        projects = self.data.get("projects", [])
        project = next((p for p in projects if p["id"] == project_id), None)
        
        if not project:
            return None
        
        analysis = {
            "basic_info": {
                "name": project["name"],
                "type": project["type"],
                "location": project["location"],
                "completion_date": project["completion_date"]
            },
            "cost_analysis": {
                "total_cost": project["cost"]["total"],
                "unit_price": project["cost"]["unit_price"],
                "cost_breakdown": project["cost"]["breakdown"]
            },
            "material_analysis": {
                "materials": project.get("materials", {})
            },
            "comparison": self._compare_with_average(project)
        }
        
        return analysis
    
    def _compare_with_average(self, project: Dict) -> Dict:
        """与平均水平对比"""
        project_type = project.get("type", "")
        projects = self.data.get("projects", [])
        same_type_projects = [p for p in projects if p.get("type") == project_type]
        
        if not same_type_projects:
            return {}
        
        avg_unit_price = sum(p["cost"]["unit_price"] for p in same_type_projects) / len(same_type_projects)
        
        return {
            "average_unit_price": avg_unit_price,
            "project_unit_price": project["cost"]["unit_price"],
            "difference": project["cost"]["unit_price"] - avg_unit_price,
            "difference_rate": (project["cost"]["unit_price"] - avg_unit_price) / avg_unit_price * 100 if avg_unit_price > 0 else 0
        }
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        projects = self.data.get("projects", [])
        
        if not projects:
            return {}
        
        by_type = {}
        for project in projects:
            ptype = project.get("type", "未知")
            if ptype not in by_type:
                by_type[ptype] = []
            by_type[ptype].append(project)
        
        stats = {
            "total_projects": len(projects),
            "by_type": {},
            "by_year": {}
        }
        
        for ptype, type_projects in by_type.items():
            stats["by_type"][ptype] = {
                "count": len(type_projects),
                "avg_unit_price": sum(p["cost"]["unit_price"] for p in type_projects) / len(type_projects),
                "total_cost": sum(p["cost"]["total"] for p in type_projects)
            }
        
        for project in projects:
            year = project.get("completion_date", "")[:4]
            if year not in stats["by_year"]:
                stats["by_year"][year] = 0
            stats["by_year"][year] += 1
        
        return stats
    
    def export_report(self, output_file: str = "") -> str:
        """导出分析报告"""
        stats = self.get_statistics()
        
        report = f"""# 重庆地区历史工程造价分析报告

> **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
> **数据来源**: 重庆市建设工程造价管理总站

---

## 📊 总体统计

| 指标 | 数值 |
|------|------|
| 总项目数 | {stats.get('total_projects', 0)} 个 |

---

## 📈 按工程类型统计

| 工程类型 | 项目数 | 平均单位造价 | 总造价 |
|---------|--------|-------------|--------|
"""
        
        for ptype, data in stats.get("by_type", {}).items():
            report += f"| {ptype} | {data['count']} | ¥{data['avg_unit_price']:,.2f} | ¥{data['total_cost']:,.2f} |\n"
        
        report += """
---

## 📅 按年度统计

| 年度 | 项目数 |
|------|--------|
"""
        
        for year, count in sorted(stats.get("by_year", {}).items()):
            report += f"| {year} | {count} |\n"
        
        report += """
---

## 📋 造价指标参考

### 道路工程
| 道路等级 | 单位造价范围 | 平均 |
|---------|-------------|------|
"""
        
        road_index = self.get_cost_index("道路工程")
        if road_index:
            for sub_type, data in road_index.items():
                report += f"| {sub_type} | ¥{data['min']}-{data['max']} | ¥{data['avg']} |\n"
        
        report += """
### 桥梁工程
| 桥梁类型 | 单位造价范围 | 平均 |
|---------|-------------|------|
"""
        
        bridge_index = self.get_cost_index("桥梁工程")
        if bridge_index:
            for sub_type, data in bridge_index.items():
                report += f"| {sub_type} | ¥{data['min']}-{data['max']} | ¥{data['avg']} |\n"
        
        report += """
### 管网工程
| 管径 | 单位造价范围 | 平均 |
|------|-------------|------|
"""
        
        pipeline_index = self.get_cost_index("管网工程")
        if pipeline_index:
            for sub_type, data in pipeline_index.items():
                report += f"| {sub_type} | ¥{data['min']}-{data['max']} | ¥{data['avg']} |\n"
        
        report += f"""
---

*报告生成：太一 AGI · 历史工程数据管理系统*  
*生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="📊 历史工程数据管理")
    parser.add_argument("--action", "-a", required=True,
                       choices=["query", "analyze", "index", "stats", "report"],
                       help="操作类型")
    parser.add_argument("--type", "-t", help="工程类型")
    parser.add_argument("--location", "-l", help="地区")
    parser.add_argument("--year", "-y", help="年份")
    parser.add_argument("--project-id", "-p", help="项目 ID")
    parser.add_argument("--output", "-o", help="输出文件")
    
    args = parser.parse_args()
    
    manager = HistoricalDataManager()
    
    if args.action == "query":
        projects = manager.query_projects(args.type, args.location, args.year)
        print(f"📋 历史工程 ({len(projects)} 个):")
        for p in projects[:10]:
            print(f"  - {p['name']} ({p['location']}, {p['completion_date']})")
            print(f"    单位造价：¥{p['cost']['unit_price']:,.2f}")
        if len(projects) > 10:
            print(f"  ... 还有 {len(projects) - 10} 个")
    
    elif args.action == "analyze":
        if not args.project_id:
            print("❌ 需要指定项目 ID --project-id")
            return 1
        
        analysis = manager.analyze_project(args.project_id)
        if analysis:
            print(f"📊 {analysis['basic_info']['name']} 分析:")
            print(f"   类型：{analysis['basic_info']['type']}")
            print(f"   地点：{analysis['basic_info']['location']}")
            print(f"   竣工：{analysis['basic_info']['completion_date']}")
            print(f"   总造价：¥{analysis['cost_analysis']['total_cost']:,.2f}")
            print(f"   单位造价：¥{analysis['cost_analysis']['unit_price']:,.2f}")
            
            if analysis['comparison']:
                comp = analysis['comparison']
                print(f"   平均造价：¥{comp['average_unit_price']:,.2f}")
                print(f"   差异：¥{comp['difference']:,.2f} ({comp['difference_rate']:+.2f}%)")
        else:
            print(f"❌ 未找到项目：{args.project_id}")
    
    elif args.action == "index":
        if not args.type:
            print("❌ 需要指定工程类型 --type")
            return 1
        
        index = manager.get_cost_index(args.type)
        if index:
            print(f"📊 {args.type} 造价指标:")
            for sub_type, data in index.items():
                print(f"   {sub_type}: ¥{data['min']}-{data['max']} (平均：¥{data['avg']})")
        else:
            print(f"❌ 未找到造价指标：{args.type}")
    
    elif args.action == "stats":
        stats = manager.get_statistics()
        print(f"📊 历史工程统计:")
        print(f"   总项目数：{stats.get('total_projects', 0)} 个")
        for ptype, data in stats.get("by_type", {}).items():
            print(f"   {ptype}: {data['count']} 个，平均 ¥{data['avg_unit_price']:,.2f}")
    
    elif args.action == "report":
        output_file = args.output or "reports/historical_analysis.md"
        report = manager.export_report(output_file)
        print(f"✅ 报告已生成：{output_file}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
