#!/usr/bin/env python3
"""
💰 手动转换 CHM 文件为 Markdown

使用已安装的 libchm-bin 工具

作者：太一 AGI
创建：2026-04-11
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime


def convert_chm_to_md(chm_file: str, output_dir: Path) -> bool:
    """转换 CHM 文件为 Markdown"""
    file_name = Path(chm_file).stem
    print(f"📕 转换 CHM: {file_name}")
    
    # 创建临时目录解压 CHM
    extract_dir = output_dir / f"chm_extract_{file_name}"
    extract_dir.mkdir(exist_ok=True)
    
    try:
        # 使用 chm2pdf 或 extract_chm
        # 尝试使用 Python chm 库
        try:
            import chm
            
            chm_file_obj = chm.ChmFile(chm_file)
            
            md_lines = []
            md_lines.append(f"# 📕 {file_name}\n")
            md_lines.append(f"> **来源**: {chm_file}\n")
            md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            md_lines.append("")
            md_lines.append(f"> **对象列表**:\n\n")
            
            # 列出所有对象
            content_count = 0
            for item in chm_file_obj.list_objects():
                if item[2] and item[0].endswith(('.html', '.htm', '.txt')):
                    content_count += 1
                    md_lines.append(f"- {item[0]}\n")
                    
                    # 提取内容
                    try:
                        content = chm_file_obj.retrieve_object(item)
                        if content:
                            # 清理 HTML 标签
                            import re
                            text = re.sub(r'<[^>]+>', '', content.decode('utf-8', errors='ignore'))
                            text = re.sub(r'\s+', ' ', text).strip()
                            
                            if len(text) > 100:
                                md_lines.append(f"\n```text\n{text[:2000]}\n```\n\n")
                    except:
                        pass
            
            md_lines.append(f"\n**共 {content_count} 个内容文件**\n")
            
            # 保存
            output_file = output_dir / f"{file_name}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines))
            
            print(f"   ✅ 已保存：{output_file.name} ({content_count} 个对象)\n")
            return True
            
        except ImportError:
            print(f"   ⚠️  Python chm 库不可用\n")
            
            # 尝试使用命令行工具
            # 列出 CHM 内容
            result = subprocess.run(
                ["chmls", chm_file],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                md_lines = []
                md_lines.append(f"# 📕 {file_name}\n")
                md_lines.append(f"> **来源**: {chm_file}\n")
                md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                md_lines.append("")
                md_lines.append("## 文件列表\n\n```text\n")
                md_lines.append(result.stdout)
                md_lines.append("```\n")
                
                output_file = output_dir / f"{file_name}_index.md"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(md_lines))
                
                print(f"   ✅ 索引已保存：{output_file.name}\n")
                return True
            else:
                print(f"   ❌ chmls 命令失败\n")
                return False
    
    except Exception as e:
        print(f"   ❌ 转换失败：{e}\n")
        return False
    finally:
        # 清理临时目录
        try:
            import shutil
            shutil.rmtree(extract_dir, ignore_errors=True)
        except:
            pass


def main():
    """主函数"""
    print("="*60)
    print("💰 手动转换 CHM 文件为 Markdown")
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
