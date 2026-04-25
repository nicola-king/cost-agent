#!/usr/bin/env python3
"""
增量更新引擎 - 支持新文件自动加入知识图谱
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 路径配置
WORKSPACE = Path("/home/nicola/.openclaw/workspace")
QUOTA_SKILLS_DIR = WORKSPACE / "skills" / "08-emerged"
QUOTA_MD_DIR = WORKSPACE / "skills" / "07-system" / "cost-agent" / "quota_md"
DATA_DIR = Path(__file__).parent.parent / "data"

# 状态文件
STATE_FILE = DATA_DIR / "update_state.json"


class IncrementalUpdater:
    """增量更新引擎"""

    def __init__(self):
        self.state: Dict = self._load_state()
        self.changes: List[Dict] = []

    def _load_state(self) -> Dict:
        """加载更新状态"""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'lastUpdate': None,
            'files': {},
            'version': 1
        }

    def _save_state(self):
        """保存更新状态"""
        os.makedirs(DATA_DIR, exist_ok=True)
        self.state['lastUpdate'] = datetime.now().isoformat()
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def _compute_hash(self, filepath: Path) -> str:
        """计算文件哈希"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _get_file_mtime(self, filepath: Path) -> float:
        """获取文件修改时间"""
        return filepath.stat().st_mtime

    def check_for_changes(self) -> List[Dict]:
        """检查文件变更"""
        changes = []

        # 检查定额文件
        for skill_dir in QUOTA_SKILLS_DIR.glob('quota-*'):
            json_file = skill_dir / "quota_data.json"
            if json_file.exists():
                change = self._check_file_change(json_file, 'quota')
                if change:
                    changes.append(change)

        # 检查政府文件
        for md_file in QUOTA_MD_DIR.glob('*.md'):
            change = self._check_file_change(md_file, 'gov_doc')
            if change:
                changes.append(change)

        # 检查 Q&A 文件
        qa_file = DATA_DIR / "qa_pairs.json"
        if qa_file.exists():
            change = self._check_file_change(qa_file, 'qa')
            if change:
                changes.append(change)

        self.changes = changes
        return changes

    def _check_file_change(self, filepath: Path, file_type: str) -> Optional[Dict]:
        """检查单个文件变更"""
        file_hash = self._compute_hash(filepath)
        file_mtime = self._get_file_mtime(filepath)

        file_key = str(filepath)
        last_state = self.state['files'].get(file_key)

        if last_state is None:
            # 新文件
            return {
                'path': str(filepath),
                'type': file_type,
                'action': 'added',
                'hash': file_hash,
                'mtime': file_mtime,
                'size': filepath.stat().st_size
            }

        if last_state['hash'] != file_hash:
            # 文件已修改
            return {
                'path': str(filepath),
                'type': file_type,
                'action': 'modified',
                'hash': file_hash,
                'mtime': file_mtime,
                'size': filepath.stat().st_size,
                'previous_hash': last_state['hash']
            }

        return None

    def update_state(self, changes: List[Dict]):
        """更新状态记录"""
        for change in changes:
            file_key = change['path']
            self.state['files'][file_key] = {
                'hash': change['hash'],
                'mtime': change['mtime'],
                'size': change['size'],
                'lastChecked': datetime.now().isoformat()
            }

        self._save_state()

    def rebuild_if_needed(self) -> bool:
        """如果有变更，重建索引"""
        changes = self.check_for_changes()

        if not changes:
            print("✅ 无文件变更，无需更新")
            return False

        print(f"📝 发现 {len(changes)} 个文件变更:")
        for change in changes:
            print(f"  {change['action']}: {Path(change['path']).name}")

        # 触发重建
        self._trigger_rebuild(changes)

        # 更新状态
        self.update_state(changes)

        return True

    def _trigger_rebuild(self, changes: List[Dict]):
        """触发重建流程"""
        print("\n🔨 开始增量重建...")

        # 1. 重建 Q&A 索引
        if any(c['type'] == 'gov_doc' for c in changes):
            self._rebuild_qa_index()

        # 2. 重建文档索引
        if any(c['type'] == 'gov_doc' for c in changes):
            self._rebuild_doc_index()

        # 3. 重建知识图谱
        if any(c['type'] in ['quota', 'gov_doc', 'qa'] for c in changes):
            self._rebuild_knowledge_graph()

        print("\n✅ 增量重建完成")

    def _rebuild_qa_index(self):
        """重建 Q&A 索引"""
        try:
            from scripts.extract_qa import QAExtractor
            extractor = QAExtractor()
            pairs = extractor.extract_all()
            extractor.qa_pairs = pairs
            extractor.save()
            print(f"  ✅ Q&A 索引: {len(pairs)} 条")
        except Exception as e:
            print(f"  ⚠️ Q&A 索引重建失败: {e}")

    def _rebuild_doc_index(self):
        """重建文档索引"""
        try:
            from matcher import QuotaMatcher
            matcher = QuotaMatcher()
            matcher._build_doc_index()
            print(f"  ✅ 文档索引: {len(matcher.gov_docs)} 份")
        except Exception as e:
            print(f"  ⚠️ 文档索引重建失败: {e}")

    def _rebuild_knowledge_graph(self):
        """重建知识图谱"""
        try:
            from knowledge_graph import KnowledgeGraph
            graph = KnowledgeGraph()
            graph.build_from_data()
            graph.save()
            print(f"  ✅ 知识图谱: {len(graph.nodes)} 节点, {len(graph.edges)} 边")
        except Exception as e:
            print(f"  ⚠️ 知识图谱重建失败: {e}")

    def get_status(self) -> Dict:
        """获取更新状态"""
        return {
            'lastUpdate': self.state.get('lastUpdate'),
            'trackedFiles': len(self.state.get('files', {})),
            'pendingChanges': len(self.changes),
            'version': self.state.get('version', 1)
        }


def main():
    print("🔄 增量更新引擎")
    print("=" * 50)

    updater = IncrementalUpdater()

    # 检查变更
    changes = updater.check_for_changes()
    if changes:
        print(f"\n📝 发现 {len(changes)} 个变更:")
        for change in changes:
            print(f"  [{change['action']}] {Path(change['path']).name}")
    else:
        print("\n✅ 无变更")

    # 重建
    rebuilt = updater.rebuild_if_needed()

    # 状态
    status = updater.get_status()
    print(f"\n📊 更新状态:")
    print(f"  最后更新: {status['lastUpdate'] or '从未'}")
    print(f"  跟踪文件: {status['trackedFiles']}")
    print(f"  待处理变更: {status['pendingChanges']}")


if __name__ == '__main__':
    main()
