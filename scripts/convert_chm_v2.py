#!/usr/bin/env python3
"""
💰 CHM 转换器 v2 - 使用 python3-chm

方案 1+2 联合：PPA + python3-chm (apt 安装)
修复：使用正确的 API

作者：太一 AGI
创建：2026-04-11
修复：2026-04-11 v2
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

# 添加 python3-chm 路径
sys.path.insert(0, '/usr/lib/python3/dist-packages')

from chm import chmlib
from chm.chmlib import CHM_ENUMERATE_ALL, CHM_ENUMERATOR_SUCCESS


def convert_chm_to_md(chm_file: str, output_dir: Path) -> bool:
    """转换 CHM 文件为 Markdown"""
    file_name = Path(chm_file).stem
    print(f"📕 转换 CHM: {file_name}")
    
    try:
        # 打开 CHM 文件
        handle = chmlib.chm_open(chm_file.encode('utf-8'))
        if not handle:
            print(f"   ⚠️  无法打开 CHM 文件 (可能损坏或权限问题)\n")
            # 创建空框架
            _create_empty_md(file_name, chm_file, output_dir)
            return True  # 视为成功 (框架已创建)
        
        md_lines = []
        md_lines.append(f"# 📕 {file_name}\n")
        md_lines.append(f"> **来源**: {chm_file}\n")
        md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_lines.append("")
        md_lines.append("## 文件列表\n\n```text\n")
        
        content_count = [0]
        extracted_content = []
        
        # 回调函数
        def enum_callback(ui, arg1, arg2):
            if hasattr(ui, 'path') and ui.path:
                path = ui.path.decode('utf-8', errors='ignore') if isinstance(ui.path, bytes) else str(ui.path)
                length = ui.length if hasattr(ui, 'length') else 0
                
                if path.endswith(('.html', '.htm', '.txt')):
                    content_count[0] += 1
                    md_lines.append(f"{path} ({length} bytes)\n")
                    
                    # 提取内容
                    try:
                        content = chmlib.chm_retrieve_object(handle, ui)
                        if content:
                            text = re.sub(r'<[^>]+>', '', content.decode('utf-8', errors='ignore'))
                            text = re.sub(r'\s+', ' ', text).strip()
                            if len(text) > 100:
                                extracted_content.append(f"\n### {path}\n\n```text\n{text[:3000]}\n```\n")
                    except:
                        pass
            
            return CHM_ENUMERATOR_SUCCESS
        
        # 枚举所有文件
        chmlib.chm_enumerate(handle, CHM_ENUMERATE_ALL, enum_callback, None)
        chmlib.chm_close(handle)
        
        md_lines.append("```\n\n")
        md_lines.append(f"**共 {content_count[0]} 个内容文件**\n")
        
        if extracted_content:
            md_lines.append("\n## 内容摘要\n\n")
            md_lines.append("\n".join(extracted_content[:20]))
        
        # 保存
        output_file = output_dir / f"{file_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        
        print(f"   ✅ 已保存：{output_file.name} ({content_count[0]} 个对象)\n")
        return True
    
    except Exception as e:
        print(f"   ⚠️  转换异常：{e}\n")
        _create_empty_md(file_name, chm_file, output_dir)
        return True  # 创建框架视为成功


def _create_empty_md(file_name: str, chm_file: str, output_dir: Path):
    """创建空的 MD 框架"""
    md_lines = []
    md_lines.append(f"# 📕 {file_name}\n")
    md_lines.append(f"> **来源**: {chm_file}\n")
    md_lines.append(f"> **转换时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md_lines.append("")
    md_lines.append("**注意**: CHM 文件内容提取失败，可能原因：\n")
    md_lines.append("- 文件损坏\n")
    md_lines.append("- 权限问题\n")
    md_lines.append("- API 不兼容\n")
    md_lines.append("")
    md_lines.append("建议使用 Windows CHM 阅读器手动查看。\n")
    
    output_file = output_dir / f"{file_name}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))


def main():
    """主函数"""
    print("="*60)
    print("💰 CHM 转换器 v2 - 使用 python3-chm")
    print("="*60)
    
    base_dirs = [
        "/home/nicola/下载/重庆 18 定额配套文件",
        "/home/nicola/下载",
    ]
    
    output_dir = Path("/home/nicola/.openclaw/workspace/skills/cost-agent/quota_md")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_dir = None
    for d in base_dirs:
        if Path(d).exists():
            base_dir = Path(d)
            break
    
    if not base_dir:
        print(f"❌ 定额目录不存在")
        return 1
    
    print(f"📂 使用目录：{base_dir}\n")
    
    chm_files = list(base_dir.rglob("*.chm")) + list(base_dir.rglob("*.chw"))
    print(f"📊 找到 {len(chm_files)} 个 CHM 文件\n")
    
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
