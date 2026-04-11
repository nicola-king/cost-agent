#!/usr/bin/env python3
"""
💰 修复版：使用 python3-chm 转换 CHM 文件为 Markdown

方案 1+2 联合：PPA + python3-chm (apt 安装)
修复：使用 chmlib 低级 API 枚举文件

作者：太一 AGI
创建：2026-04-11
修复：2026-04-11
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

# 添加 python3-chm 路径
sys.path.insert(0, '/usr/lib/python3/dist-packages')

from chm import chmlib
from chm.chmlib import CHM_ENUMERATE_ALL, CHM_ENUMERATOR_SUCCESS, CHM_ENUMERATOR_FAILURE


def convert_chm_to_md(chm_file: str, output_dir: Path) -> bool:
    """转换 CHM 文件为 Markdown"""
    file_name = Path(chm_file).stem
    print(f"📕 转换 CHM: {file_name}")
    
    try:
        # 打开 CHM 文件
        handle = chmlib.chm_open(chm_file.encode('utf-8'))
        if not handle:
            print(f"   ❌ 无法打开 CHM 文件\n")
            return False
        
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
            # ui 是 chmUnitInfo 结构
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
                            # 清理 HTML 标签
                            text = re.sub(r'<[^>]+>', '', content.decode('utf-8', errors='ignore'))
                            text = re.sub(r'\s+', ' ', text).strip()
                            
                            if len(text) > 100:
                                extracted_content.append(f"\n### {path}\n\n```text\n{text[:3000]}\n```\n")
                    except Exception as e:
                        pass
            
            return CHM_ENUMERATOR_SUCCESS
        
        # 枚举所有文件
        chmlib.chm_enumerate(handle, CHM_ENUMERATE_ALL, enum_callback, None)
        
        chmlib.chm_close(handle)
        
        md_lines.append("```\n\n")
        md_lines.append(f"**共 {content_count[0]} 个内容文件**\n")
        
        # 添加提取的内容
        if extracted_content:
            md_lines.append("\n## 内容摘要\n\n")
            md_lines.append("\n".join(extracted_content[:20]))  # 限制 20 个
        
        # 保存
        output_file = output_dir / f"{file_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        
        print(f"   ✅ 已保存：{output_file.name} ({content_count[0]} 个对象)\n")
        return True
    
    except Exception as e:
        print(f"   ❌ 转换失败：{e}\n")
        return False


def main():
    """主函数"""
    print("="*60)
    print("💰 修复版：使用 python3-chm 转换 CHM 文件为 Markdown")
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
