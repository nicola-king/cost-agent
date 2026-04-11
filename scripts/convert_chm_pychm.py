#!/usr/bin/env python3
"""
💰 使用 pychm 库转换 CHM 文件为 Markdown

GitHub 替代方案：pychm (已成功安装)

作者：太一 AGI
创建：2026-04-11
"""

import os
from pathlib import Path
from datetime import datetime


def convert_chm_to_md(chm_file: str, output_dir: Path) -> bool:
    """转换 CHM 文件为 Markdown"""
    file_name = Path(chm_file).stem
    print(f"📕 转换 CHM: {file_name}")
    
    try:
        # 使用 chmlib 低级 API
        from chm import chmlib
        from chm.chmlib import CHM_ENUMERATE_ALL
        
        # 打开 CHM 文件
        handle = chmlib.chm_open(chm_file)
        if not handle:
            print(f"   ❌ 无法打开 CHM 文件\n")
            return False
        
        md_lines = []
        md_lines.append(f"# 📕 {file_name}\n")
        md_lines.append(f"> **来源**: {chm_file}\n")
        md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_lines.append("")
        md_lines.append("## 文件列表\n\n```text\n")
        
        # 枚举所有对象
        content_count = [0]  # 使用列表以便在回调中修改
        
        def callback(ui, arg1, arg2):
            if ui.filetype == 0:  # 普通文件
                content_count[0] += 1
                md_lines.append(f"{ui.path} ({ui.length} bytes)\n")
                
                # 提取内容
                try:
                    content = chmlib.chm_retrieve_object(handle, ui)
                    if content:
                        import re
                        text = re.sub(r'<[^>]+>', '', content.decode('utf-8', errors='ignore'))
                        text = re.sub(r'\s+', ' ', text).strip()
                        
                        if len(text) > 100:
                            md_lines.append(f"\n```text\n{text[:3000]}\n```\n\n")
                except Exception as e:
                    pass
            return 0
        
        # 枚举所有文件
        chmlib.chm_enumerate(handle, CHM_ENUMERATE_ALL, callback, None)
        
        chmlib.chm_close(handle)
        
        md_lines.append(f"```\n\n**共 {content_count[0]} 个内容文件**\n")
        
        # 保存
        output_file = output_dir / f"{file_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        
        print(f"   ✅ 已保存：{output_file.name} ({content_count} 个对象)\n")
        return True
    
    except ImportError:
        print(f"   ❌ CHM 库不可用 (尝试：pip install pychm 或 sudo apt install python3-chm)\n")
        return False
    except Exception as e:
        print(f"   ❌ 转换失败：{e}\n")
        return False


def main():
    """主函数"""
    print("="*60)
    print("💰 使用 pychm 转换 CHM 文件为 Markdown")
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
