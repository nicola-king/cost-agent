#!/usr/bin/env python3
"""
材料信息价管理 (Material Price Management)

功能:
1. 重庆造价站材料信息价管理
2. 实时材料价格查询
3. 材料价格趋势分析
4. 按月份匹配材料价格
5. 支持手动更新/自动导入

数据来源:
- 重庆市建设工程造价管理总站
- 重庆建设工程造价信息网

作者：太一 AGI
创建：2026-04-10
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


# ═══════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class MaterialPrice:
    """材料价格数据"""
    name: str
    category: str
    specification: str
    unit: str
    current_price: float
    previous_price: float
    price_date: str
    source: str
    region: str
    month: str = ""
    
    def __post_init__(self):
        if not self.month:
            self.month = self.price_date
    
    def price_change_rate(self) -> float:
        """价格变动率"""
        if self.previous_price == 0:
            return 0
        return (self.current_price - self.previous_price) / self.previous_price * 100
    
    def to_dict(self) -> dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════
# 管理器核心
# ═══════════════════════════════════════════════════════════

class MaterialPriceManager:
    """材料价格管理器"""
    
    def __init__(self, region: str = "重庆"):
        self.region = region
        self.material_db = self._load_material_db()
        self.price_history = self._load_price_history()
        self.target_month = None
    
    def set_target_month(self, year: int, month: int):
        """设置目标月份"""
        self.target_month = f"{year:04d}-{month:02d}"
    
    def get_available_months(self) -> List[str]:
        """获取可用月份列表"""
        months = set()
        for history in self.price_history.values():
            for record in history:
                if "date" in record:
                    months.add(record["date"][:7])
        months.add(datetime.now().strftime("%Y-%m"))
        return sorted(list(months), reverse=True)
    
    def _load_material_db(self) -> Dict:
        """加载材料数据库"""
        db_file = Path(__file__).parent / "config" / "material_prices.json"
        if db_file.exists():
            with open(db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # 默认材料数据库 (重庆地区 2026 年 4 月信息价)
        return {
            "钢材": {
                "HRB400E 钢筋 Φ10": {"unit": "t", "price": 4250, "previous": 4200},
                "HRB400E 钢筋 Φ20": {"unit": "t", "price": 4180, "previous": 4150},
                "HRB500E 钢筋 Φ10": {"unit": "t", "price": 4550, "previous": 4500},
                "Q235 钢板 10mm": {"unit": "t", "price": 4680, "previous": 4650},
            },
            "水泥": {
                "P.O 42.5 水泥": {"unit": "t", "price": 520, "previous": 510},
                "P.O 52.5 水泥": {"unit": "t", "price": 580, "previous": 570},
                "P.C 32.5 水泥": {"unit": "t", "price": 450, "previous": 440},
            },
            "砂石": {
                "特细砂": {"unit": "m³", "price": 185, "previous": 180},
                "机制砂": {"unit": "m³", "price": 165, "previous": 160},
                "碎石 5-10mm": {"unit": "m³", "price": 155, "previous": 150},
                "碎石 10-20mm": {"unit": "m³", "price": 150, "previous": 145},
            },
            "沥青": {
                "70# 道路石油沥青": {"unit": "t", "price": 4850, "previous": 4800},
                "90# 道路石油沥青": {"unit": "t", "price": 4750, "previous": 4700},
                "SBS 改性沥青": {"unit": "t", "price": 6200, "previous": 6100},
            },
            "管材": {
                "HDPE 双壁波纹管 DN500": {"unit": "m", "price": 285, "previous": 280},
                "HDPE 双壁波纹管 DN800": {"unit": "m", "price": 520, "previous": 510},
                "HDPE 双壁波纹管 DN1000": {"unit": "m", "price": 780, "previous": 760},
                "钢筋混凝土管 DN800": {"unit": "m", "price": 450, "previous": 440},
            },
            "商品混凝土": {
                "C20 商品砼": {"unit": "m³", "price": 480, "previous": 470},
                "C25 商品砼": {"unit": "m³", "price": 500, "previous": 490},
                "C30 商品砼": {"unit": "m³", "price": 520, "previous": 510},
                "C35 商品砼": {"unit": "m³", "price": 545, "previous": 535},
                "C40 商品砼": {"unit": "m³", "price": 570, "previous": 560},
            },
        }
    
    def _load_price_history(self) -> Dict:
        """加载价格历史"""
        history_file = Path(__file__).parent / "config" / "price_history.json"
        if history_file.exists():
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def get_price(self, material_name: str, month: Optional[str] = None) -> Optional[MaterialPrice]:
        """获取材料价格 (按月份匹配)"""
        target_month = month or self.target_month or datetime.now().strftime("%Y-%m")
        
        for category, materials in self.material_db.items():
            if material_name in materials:
                data = materials[material_name]
                return MaterialPrice(
                    name=material_name,
                    category=category,
                    specification="",
                    unit=data["unit"],
                    current_price=data["price"],
                    previous_price=data.get("previous", data["price"]),
                    price_date=target_month,
                    source="重庆市建设工程造价信息网",
                    region=self.region,
                    month=target_month
                )
        return None
    
    def update_price(self, material_name: str, new_price: float, category: str = "") -> None:
        """更新材料价格"""
        found = False
        for cat, materials in self.material_db.items():
            if material_name in materials:
                old_price = materials[material_name]["price"]
                materials[material_name]["previous"] = old_price
                materials[material_name]["price"] = new_price
                
                if material_name not in self.price_history:
                    self.price_history[material_name] = []
                self.price_history[material_name].append({
                    "date": datetime.now().isoformat(),
                    "old_price": old_price,
                    "new_price": new_price,
                    "change_rate": (new_price - old_price) / old_price * 100 if old_price > 0 else 0
                })
                found = True
                break
        
        if not found and category:
            if category not in self.material_db:
                self.material_db[category] = {}
            self.material_db[category][material_name] = {
                "unit": "单位",
                "price": new_price,
                "previous": new_price
            }
        
        self._save_material_db()
        self._save_price_history()
    
    def _save_material_db(self) -> None:
        """保存材料数据库"""
        db_file = Path(__file__).parent / "config" / "material_prices.json"
        db_file.parent.mkdir(exist_ok=True)
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(self.material_db, f, indent=2, ensure_ascii=False)
    
    def _save_price_history(self) -> None:
        """保存价格历史"""
        history_file = Path(__file__).parent / "config" / "price_history.json"
        history_file.parent.mkdir(exist_ok=True)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(self.price_history, f, indent=2, ensure_ascii=False)
    
    def list_materials(self, category: str = "") -> List[str]:
        """列出材料"""
        if category:
            return list(self.material_db.get(category, {}).keys())
        all_materials = []
        for cat, materials in self.material_db.items():
            all_materials.extend([f"{cat}: {m}" for m in materials.keys()])
        return all_materials
    
    def get_price_trend(self, material_name: str, months: int = 6) -> List[Dict]:
        """获取价格趋势"""
        if material_name not in self.price_history:
            price = self.get_price(material_name)
            if price:
                return [{"date": price.month, "price": price.current_price, "change_rate": 0}]
            return []
        
        history = self.price_history[material_name]
        return history[-months:]
    
    def export_to_json(self) -> str:
        """导出为 JSON"""
        return json.dumps(self.material_db, indent=2, ensure_ascii=False)
    
    def import_from_zaojiazhan(self, file_path: str) -> None:
        """从重庆造价站 Excel/CSV 导入"""
        import csv
        
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("材料名称", "").strip()
                spec = row.get("规格", "").strip()
                unit = row.get("单位", "单位").strip()
                price = float(row.get("信息价", 0))
                previous = float(row.get("上期价", price))
                
                if name and price > 0:
                    category = self._auto_categorize(name)
                    full_name = f"{name} {spec}" if spec else name
                    
                    if category not in self.material_db:
                        self.material_db[category] = {}
                    
                    self.material_db[category][full_name] = {
                        "unit": unit,
                        "price": price,
                        "previous": previous
                    }
        
        self._save_material_db()
        print(f"✅ 从 {file_path} 导入完成")
    
    def _auto_categorize(self, material_name: str) -> str:
        """自动分类材料"""
        keywords = {
            "钢筋": "钢材",
            "钢板": "钢材",
            "水泥": "水泥",
            "砂": "砂石",
            "碎石": "砂石",
            "沥青": "沥青",
            "HDPE": "管材",
            "波纹管": "管材",
            "混凝土": "商品混凝土",
            "商品砼": "商品混凝土",
        }
        
        for keyword, category in keywords.items():
            if keyword in material_name:
                return category
        
        return "其他"


# ═══════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="📊 材料信息价管理")
    parser.add_argument("--action", "-a", required=True,
                       choices=["list", "get", "update", "trend", "export", "import", "months"],
                       help="操作类型")
    parser.add_argument("--material", "-m", help="材料名称")
    parser.add_argument("--category", "-c", help="材料类别")
    parser.add_argument("--price", "-p", type=float, help="新价格")
    parser.add_argument("--month", "-M", help="目标月份 (YYYY-MM)")
    parser.add_argument("--months", "-n", type=int, default=6, help="查看月份数")
    parser.add_argument("--file", "-f", help="导入文件路径")
    parser.add_argument("--region", "-r", default="重庆", help="地区")
    
    args = parser.parse_args()
    
    manager = MaterialPriceManager(region=args.region)
    
    if args.action == "list":
        materials = manager.list_materials(args.category)
        print(f"📋 材料列表 ({len(materials)} 个):")
        for m in materials[:20]:
            print(f"  - {m}")
        if len(materials) > 20:
            print(f"  ... 还有 {len(materials) - 20} 个")
    
    elif args.action == "get":
        if not args.material:
            print("❌ 需要指定材料名称 --material")
            return 1
        
        price = manager.get_price(args.material, args.month)
        if price:
            print(f"📊 {price.name}")
            print(f"   当前价格：¥{price.current_price:,.2f} /{price.unit}")
            print(f"   上期价格：¥{price.previous_price:,.2f} /{price.unit}")
            print(f"   变动率：{price.price_change_rate():+.2f}%")
            print(f"   数据来源：{price.source}")
            print(f"   价格日期：{price.month}")
        else:
            print(f"❌ 未找到材料：{args.material}")
    
    elif args.action == "update":
        if not args.material or not args.price:
            print("❌ 需要指定材料名称 --material 和新价格 --price")
            return 1
        
        manager.update_price(args.material, args.price, args.category or "")
        print(f"✅ 价格已更新：{args.material} = ¥{args.price:,.2f}")
    
    elif args.action == "trend":
        if not args.material:
            print("❌ 需要指定材料名称 --material")
            return 1
        
        trend = manager.get_price_trend(args.material, args.months)
        if trend:
            print(f"📈 {args.material} 价格趋势 (近{args.months}个月):")
            for record in trend:
                print(f"   {record['date'][:10]}: ¥{record.get('price', record.get('new_price', 0)):,.2f} ({record.get('change_rate', 0):+.2f}%)")
        else:
            print(f"❌ 无历史数据：{args.material}")
    
    elif args.action == "months":
        months = manager.get_available_months()
        print(f"📅 可用月份 ({len(months)}个):")
        for m in months[:12]:
            print(f"  - {m}")
        if len(months) > 12:
            print(f"  ... 还有 {len(months) - 12} 个月")
    
    elif args.action == "export":
        json_data = manager.export_to_json()
        print(json_data)
    
    elif args.action == "import":
        if not args.file:
            print("❌ 需要指定导入文件 --file")
            return 1
        
        manager.import_from_zaojiazhan(args.file)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
