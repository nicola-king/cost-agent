#!/usr/bin/env python3
"""
💰 转换 Access 数据库和 CHM 文件为 Markdown

支持:
- Access (.mdb/.accdb) → Markdown (需 pyodbc)
- CHM (.chm/.chw) → Markdown (需 chm2pdf + pdfplumber)

作者：太一 AGI
创建：2026-04-11
"""

import subprocess
from pathlib import Path
from datetime import datetime


def convert_mdb_to_md(mdb_file: str, output_dir: Path) -> bool:
    """转换 Access 数据库为 Markdown"""
    file_name = Path(mdb_file).stem
    print(f"💾 转换 Access: {file_name}")
    
    try:
        import pyodbc
        import pandas as pd
        
        # 连接数据库
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            f'DBQ={mdb_file};'
        )
        
        try:
            conn = pyodbc.connect(conn_str)
        except Exception as e:
            print(f"   ⚠️  需要安装 Access 驱动：sudo apt install mdbtools\n")
            return False
        
        # 获取所有表
        cursor = conn.cursor()
        tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
        
        print(f"   找到 {len(tables)} 个表")
        
        md_lines = []
        md_lines.append(f"# 💾 {file_name}\n")
        md_lines.append(f"> **来源**: {mdb_file}\n")
        md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_lines.append(f"> **表数量**: {len(tables)} 个\n")
        md_lines.append("")
        
        for table in tables:
            md_lines.append(f"## 📄 表：{table}\n")
            md_lines.append("")
            
            try:
                df = pd.read_sql(f"SELECT * FROM [{table}]", conn)
                md_lines.append(f"**行数**: {len(df)} 行，**列数**: {len(df.columns)} 列\n")
                md_lines.append("")
                
                if len(df) > 0:
                    # 前 20 行预览
                    md_lines.append("### 数据预览 (前 20 行)\n\n")
                    cols = df.columns[:15].tolist()
                    md_lines.append("| " + " | ".join(str(c) for c in cols) + " |\n")
                    md_lines.append("|" + "|".join(["---"] * len(cols)) + "|\n")
                    
                    for idx, row in df.head(20).iterrows():
                        values = [str(row[col])[:50] if pd.notna(row[col]) else '' for col in cols]
                        md_lines.append("| " + " | ".join(values) + " |\n")
                    
                    md_lines.append("\n")
                
            except Exception as e:
                md_lines.append(f"⚠️ 读取失败：{e}\n")
            
            md_lines.append("\n")
        
        conn.close()
        
        # 保存
        output_file = output_dir / f"{file_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        
        print(f"   ✅ 已保存：{output_file.name}\n")
        return True
    
    except ImportError as e:
        print(f"   ⚠️  需要安装：pip install pyodbc pandas --break-system-packages\n")
        return False
    except Exception as e:
        print(f"   ❌ 转换失败：{e}\n")
        return False


def convert_chm_to_md(chm_file: str, output_dir: Path) -> bool:
    """转换 CHM 文件为 Markdown"""
    file_name = Path(chm_file).stem
    print(f"📕 转换 CHM: {file_name}")
    
    try:
        # 方法 1: 使用 chm2pdf 转换
        pdf_file = output_dir / f"{file_name}.pdf"
        
        cmd = ["chm2pdf", chm_file, "-o", str(pdf_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and pdf_file.exists():
            print(f"   ✅ CHM → PDF 成功")
            
            # 然后用 pdfplumber 转换 PDF
            import pdfplumber
            
            md_lines = []
            md_lines.append(f"# 📕 {file_name}\n")
            md_lines.append(f"> **来源**: {chm_file}\n")
            md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            md_lines.append("")
            
            with pdfplumber.open(str(pdf_file)) as pdf:
                md_lines.append(f"> **页数**: {len(pdf.pages)} 页\n\n")
                
                for i, page in enumerate(pdf.pages):
                    md_lines.append(f"## 第 {i+1} 页\n\n")
                    text = page.extract_text()
                    if text:
                        md_lines.append(f"{text}\n")
                    md_lines.append("\n")
            
            # 保存
            output_file = output_dir / f"{file_name}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines))
            
            print(f"   ✅ 已保存：{output_file.name}\n")
            return True
        else:
            print(f"   ⚠️  chm2pdf 失败，尝试直接提取\n")
            return False
    
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  转换超时\n")
        return False
    except FileNotFoundError:
        print(f"   ⚠️  需要安装：sudo apt install chm2pdf\n")
        return False
    except Exception as e:
        print(f"   ❌ 转换失败：{e}\n")
        return False


def main():
    """主函数"""
    print("="*60)
    print("💰 转换 Access 数据库和 CHM 文件为 Markdown")
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
    
    # 查找 Access 和 CHM 文件
    mdb_files = list(base_dir.rglob("*.mdb"))
    accdb_files = list(base_dir.rglob("*.accdb"))
    chm_files = list(base_dir.rglob("*.chm")) + list(base_dir.rglob("*.chw"))
    
    print(f"📊 找到文件:")
    print(f"   Access (.mdb): {len(mdb_files)} 个")
    print(f"   Access (.accdb): {len(accdb_files)} 个")
    print(f"   CHM: {len(chm_files)} 个\n")
    
    # 转换统计
    stats = {
        'MDB': {'success': 0, 'fail': 0},
        'CHM': {'success': 0, 'fail': 0},
    }
    
    # 转换 MDB
    print("="*60)
    print("💾 转换 Access 数据库 (.mdb)")
    print("="*60)
    for f in mdb_files[:10]:
        if convert_mdb_to_md(str(f), output_dir):
            stats['MDB']['success'] += 1
        else:
            stats['MDB']['fail'] += 1
    
    # 转换 CHM
    print("="*60)
    print("📕 转换 CHM 文件")
    print("="*60)
    for f in chm_files[:10]:
        if convert_chm_to_md(str(f), output_dir):
            stats['CHM']['success'] += 1
        else:
            stats['CHM']['fail'] += 1
    
    # 总结
    print("\n" + "="*60)
    print("✅ 转换完成!")
    print("="*60)
    for type_name, type_stats in stats.items():
        print(f"   {type_name}: 成功 {type_stats['success']} 个，失败 {type_stats['fail']} 个")
    
    print(f"\n📁 输出目录：{output_dir}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
