#!/usr/bin/env python3
"""
📚 批量转换定额配套文档为 Markdown

支持格式:
- PDF → Markdown
- Word (.doc/.docx) → Markdown
- Excel (.xls/.xlsx) → Markdown
- CHM → Markdown (需要转换)
- HTML → Markdown

作者：太一 AGI
创建：2026-04-11
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def convert_excel_to_md(excel_file: str, output_dir: Path):
    """转换 Excel 文件为 Markdown"""
    file_name = Path(excel_file).stem
    
    print(f"📊 转换 Excel: {file_name}")
    
    try:
        # 读取所有 sheet
        all_sheets = pd.read_excel(excel_file, sheet_name=None)
        
        md_content = []
        md_content.append(f"# 📊 {file_name}\n")
        md_content.append(f"> **来源**: {excel_file}\n")
        md_content.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_content.append("")
        
        for sheet_name, df in all_sheets.items():
            md_content.append(f"## 📄 {sheet_name}\n")
            md_content.append("")
            md_content.append(f"**行数**: {len(df)} 行，**列数**: {len(df.columns)} 列\n")
            md_content.append("")
            
            # 前 10 行预览
            md_content.append("### 数据预览\n")
            md_content.append("")
            md_content.append("| " + " | ".join(str(col) for col in df.columns[:10]) + " |\n")
            md_content.append("|" + "|".join(["---"] * min(10, len(df.columns))) + "|\n")
            for idx, row in df.head(10).iterrows():
                md_content.append("| " + " | ".join(str(row[col]) for col in df.columns[:10]) + " |\n")
            md_content.append("\n")
            
            # 统计信息
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                md_content.append("### 统计信息\n")
                md_content.append("")
                for col in numeric_cols[:5]:
                    md_content.append(f"- **{col}**: 最小={df[col].min():,.2f}, 最大={df[col].max():,.2f}, 平均={df[col].mean():,.2f}\n")
                md_content.append("\n")
        
        # 保存
        output_file = output_dir / f"{file_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        
        print(f"   ✅ 已保存：{output_file.name}\n")
        return True
    
    except Exception as e:
        print(f"   ❌ 转换失败：{e}\n")
        return False


def convert_word_to_md(word_file: str, output_dir: Path):
    """转换 Word 文件为 Markdown"""
    file_name = Path(word_file).stem
    
    print(f"📄 转换 Word: {file_name}")
    
    try:
        from docx import Document
        
        doc = Document(word_file)
        
        md_content = []
        md_content.append(f"# 📄 {file_name}\n")
        md_content.append(f"> **来源**: {word_file}\n")
        md_content.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_content.append("")
        
        for para in doc.paragraphs:
            if para.text.strip():
                md_content.append(f"{para.text}\n")
        
        # 保存
        output_file = output_dir / f"{file_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        
        print(f"   ✅ 已保存：{output_file.name}\n")
        return True
    
    except ImportError:
        print(f"   ⚠️  需要安装：pip install python-docx\n")
        return False
    except Exception as e:
        print(f"   ❌ 转换失败：{e}\n")
        return False


def convert_pdf_to_md(pdf_file: str, output_dir: Path):
    """转换 PDF 文件为 Markdown"""
    file_name = Path(pdf_file).stem
    
    print(f"📕 转换 PDF: {file_name}")
    
    try:
        import pdfplumber
        
        md_content = []
        md_content.append(f"# 📕 {file_name}\n")
        md_content.append(f"> **来源**: {pdf_file}\n")
        md_content.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_content.append("")
        
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages):
                md_content.append(f"## 第 {i+1} 页\n")
                md_content.append("")
                text = page.extract_text()
                if text:
                    md_content.append(f"{text}\n")
                md_content.append("\n")
        
        # 保存
        output_file = output_dir / f"{file_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        
        print(f"   ✅ 已保存：{output_file.name}\n")
        return True
    
    except ImportError:
        print(f"   ⚠️  需要安装：pip install pdfplumber\n")
        return False
    except Exception as e:
        print(f"   ❌ 转换失败：{e}\n")
        return False


def main():
    """主函数"""
    print("="*60)
    print("📚 批量转换定额配套文档为 Markdown")
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
            base_dir = Path(d)
            break
    
    if not base_dir:
        print(f"❌ 定额目录不存在")
        return 1
    
    print(f"📂 使用目录：{base_dir}\n")
    
    # 查找文件
    excel_files = list(base_dir.rglob("*.xls*"))
    word_files = list(base_dir.rglob("*.doc*"))
    pdf_files = list(base_dir.rglob("*.pdf"))
    
    print(f"📊 找到文件:")
    print(f"   Excel: {len(excel_files)} 个")
    print(f"   Word: {len(word_files)} 个")
    print(f"   PDF: {len(pdf_files)} 个\n")
    
    # 转换统计
    stats = {
        "excel": {"success": 0, "fail": 0},
        "word": {"success": 0, "fail": 0},
        "pdf": {"success": 0, "fail": 0},
    }
    
    # 转换 Excel
    print("="*60)
    print("📊 转换 Excel 文件")
    print("="*60)
    for f in excel_files[:20]:  # 限制 20 个
        if convert_excel_to_md(str(f), output_dir):
            stats["excel"]["success"] += 1
        else:
            stats["excel"]["fail"] += 1
    
    # 转换 Word
    print("="*60)
    print("📄 转换 Word 文件")
    print("="*60)
    for f in word_files[:20]:  # 限制 20 个
        if convert_word_to_md(str(f), output_dir):
            stats["word"]["success"] += 1
        else:
            stats["word"]["fail"] += 1
    
    # 转换 PDF
    print("="*60)
    print("📕 转换 PDF 文件")
    print("="*60)
    for f in pdf_files[:20]:  # 限制 20 个
        if convert_pdf_to_md(str(f), output_dir):
            stats["pdf"]["success"] += 1
        else:
            stats["pdf"]["fail"] += 1
    
    # 总结
    print("\n" + "="*60)
    print("✅ 转换完成!")
    print("="*60)
    for type_name, type_stats in stats.items():
        print(f"   {type_name.upper()}: 成功 {type_stats['success']} 个，失败 {type_stats['fail']} 个")
    print(f"\n📁 输出目录：{output_dir}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
