#!/usr/bin/env python3
"""
💰 使用 Python chm 库转换 CHM 文件为 Markdown

不依赖 chm2pdf，使用 Python chm 库

作者：太一 AGI
创建：2026-04-11
"""

import subprocess
from pathlib import Path
from datetime import datetime


def convert_chm_to_md(chm_file: str, output_dir: Path) -> bool:
    """转换 CHM 文件为 Markdown"""
    file_name = Path(chm_file).stem
    print(f"📕 转换 CHM: {file_name}")
    
    # 方法 1: 使用 extract_chm
    try:
        extract_dir = output_dir / f"chm_extract_{file_name}"
        extract_dir.mkdir(exist_ok=True)
        
        result = subprocess.run(
            ["extract_chm", "-o", str(extract_dir), chm_file],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print(f"   ✅ CHM 解压成功")
            
            # 合并所有 HTML 文件
            md_lines = []
            md_lines.append(f"# 📕 {file_name}\n")
            md_lines.append(f"> **来源**: {chm_file}\n")
            md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            md_lines.append("")
            
            # 查找并转换 HTML 文件
            html_files = list(extract_dir.rglob("*.html")) + list(extract_dir.rglob("*.htm"))
            
            for html_file in sorted(html_files)[:50]:  # 限制 50 个文件
                try:
                    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 简单清理 HTML 标签
                    import re
                    text = re.sub(r'<[^>]+>', '', content)
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    if len(text) > 100:
                        md_lines.append(f"## {html_file.name}\n\n")
                        md_lines.append(f"{text[:5000]}\n\n")  # 限制 5000 字符
                except:
                    pass
            
            # 保存
            output_file = output_dir / f"{file_name}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines))
            
            print(f"   ✅ 已保存：{output_file.name} ({len(html_files)} 个 HTML 文件)\n")
            return True
        
    except FileNotFoundError:
        print(f"   ⚠️  需要安装：sudo apt install libchm-bin\n")
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  转换超时\n")
    except Exception as e:
        print(f"   ⚠️  转换失败：{e}\n")
    
    # 方法 2: 使用 Python chm 库
    try:
        import chm
        
        chm_file_obj = chm.ChmFile(chm_file)
        items = chm_file_obj.get_object('/#SYSTEM')
        
        md_lines = []
        md_lines.append(f"# 📕 {file_name}\n")
        md_lines.append(f"> **来源**: {chm_file}\n")
        md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_lines.append("")
        md_lines.append(f"> **注意**: CHM 文件内容提取\n\n")
        
        # 列出所有对象
        for item in chm_file_obj.list_objects():
            if item[2] and item[0].endswith(('.html', '.htm', '.txt')):
                md_lines.append(f"- {item[0]}\n")
        
        output_file = output_dir / f"{file_name}_index.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        
        print(f"   ✅ 索引已保存：{output_file.name}\n")
        return True
        
    except ImportError:
        print(f"   ⚠️  需要安装：pip install python-chm --break-system-packages\n")
        return False
    except Exception as e:
        print(f"   ⚠️  Python chm 库失败：{e}\n")
        return False


def main():
    """主函数"""
    print("="*60)
    print("💰 使用 Python/命令行工具转换 CHM 文件为 Markdown")
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
    
    # 查找 CHM 文件
    chm_files = list(base_dir.rglob("*.chm")) + list(base_dir.rglob("*.chw"))
    print(f"📊 找到 {len(chm_files)} 个 CHM 文件\n")
    
    # 转换
    success = 0
    fail = 0
    
    for f in chm_files[:10]:
        if convert_chm_to_md(str(f), output_dir):
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
