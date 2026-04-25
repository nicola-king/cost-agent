"""
定额智能匹配引擎 - 核心匹配器
三层匹配：定额条目 ↔ 解释Q&A ↔ 政府文件
"""

import os
import re
import json
import glob
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import jieba

# 路径配置



WORKSPACE = Path("/home/nicola/.openclaw/workspace")
QUOTA_SKILLS_DIR = WORKSPACE / "skills" / "08-emerged"
QUOTA_MD_DIR = WORKSPACE / "skills" / "07-system" / "cost-agent" / "quota_md"
DATA_DIR = Path(__file__).parent / "data"

# 定额编号正则



QUOTA_CODE_RE = re.compile(r'([A-Z]{2}\d{4})')

# 同义词词典



SYNONYMS = {
    '砼': '混凝土',
    '混凝土': '混凝土',
    '钢筋': '钢筋',
    '螺纹钢': '钢筋',
    '圆钢': '钢筋',
    '模板': '模板',
    '木模板': '模板',
    '钢模板': '模板',
    '脚手架': '脚手架',
    '钢管脚手架': '脚手架',
    '安全文明': '安全文明施工',
    '安全文明施工': '安全文明施工',
    '土石方': '土石方',
    '土方': '土石方',
    '石方': '土石方',
    '管道': '管道',
    '排水管': '管道',
    '给水管': '管道',
    '电缆': '电缆',
    '电线': '电缆',
    '桥架': '桥架',
    '电缆桥架': '桥架',
    '通风': '通风空调',
    '空调': '通风空调',
    '暖通': '通风空调',
    '消防': '消防工程',
    '消防工程': '消防工程',
    '给排水': '给排水',
    '给水': '给排水',
    '排水': '给排水',
    '抹灰': '抹灰',
    '粉刷': '抹灰',
    '吊顶': '天棚吊顶',
    '天棚': '天棚吊顶',
    '屋面': '屋面工程',
    '防水': '防水工程',
    '防腐': '防腐工程',
    '保温': '保温工程',
    '油漆': '油漆涂料',
    '涂料': '油漆涂料',
    '门窗': '门窗工程',
    '木门': '门窗工程',
    '铝合金窗': '门窗工程',
    '桩基': '桩基工程',
    '灌注桩': '桩基工程',
    '预制桩': '桩基工程',
    '基坑': '基坑工程',
    '支护': '基坑支护',
    '基坑支护': '基坑工程',
    '道路': '道路工程',
    '路面': '道路工程',
    '路基': '道路工程',
    '桥梁': '桥梁工程',
    '隧道': '隧道工程',
    '涵洞': '涵洞工程',
    '砌筑': '砌筑工程',
    '砖砌体': '砌筑工程',
    '混凝土': '混凝土',
    '现浇混凝土': '混凝土',
    '预制混凝土': '混凝土',
}


class QuotaMatcher:
    """定额智能匹配引擎"""

    def __init__(self):
        self.quota_data: Dict[str, List[Dict]] = {}  # skill_name -> records
        self.qa_pairs: List[Dict] = []  # Q&A pairs from 解释
        self.gov_docs: List[Dict] = []  # Government documents
        self.doc_index: Dict[str, Dict] = {}  # file_name -> metadata
        self._loaded = False

    def load_all(self):
        """加载所有数据源"""
        if self._loaded:
            return

        self._load_quota_skills()
        self._load_qa_pairs()
        self._load_gov_docs()
        self._loaded = True

    def _load_quota_skills(self):
        """加载 6 个定额 Skill 的数据"""
        skill_names = [
            'quota-building', 'quota-installation', 'quota-municipal',
            'quota-decoration', 'quota-transit', 'quota-prefab'
        ]
        for name in skill_names:
            skill_dir = QUOTA_SKILLS_DIR / name
            json_file = skill_dir / "quota_data.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # 统一为列表格式
                    if isinstance(data, dict) and 'prefixes' in data:
                        # 从 prefixes 中提取所有记录
                        records = []
                        for prefix, items in data['prefixes'].items():
                            if isinstance(items, list):
                                records.extend(items)
                        self.quota_data[name] = records
                    elif isinstance(data, list):
                        self.quota_data[name] = data
                    else:
                        print(f"⚠️ {name} 数据格式未知: {type(data)}")
                except Exception as e:
                    print(f"⚠️ 加载 {name} 失败: {e}")

    def _load_qa_pairs(self):
        """从定额解释文件中提取 Q&A 对"""
        qa_file = DATA_DIR / "qa_pairs.json"
        if qa_file.exists():
            with open(qa_file, 'r', encoding='utf-8') as f:
                self.qa_pairs = json.load(f)
            return

        # 如果还没有提取，从 MD 文件中提取
        self.qa_pairs = self._extract_qa_from_files()
        # 保存
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(qa_file, 'w', encoding='utf-8') as f:
            json.dump(self.qa_pairs, f, ensure_ascii=False, indent=2)

    def _extract_qa_from_files(self) -> List[Dict]:
        """从定额解释 MD 文件中提取 Q&A 对"""
        qa_pairs = []
        explanation_files = list(QUOTA_MD_DIR.glob('*解释*.md'))

        for filepath in explanation_files:
            filename = filepath.name
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取章节信息
                sections = re.split(r'^(二、|三、|四、|五、|六、|七、|八、)', content, flags=re.MULTILINE)

                current_section = "综合"
                if len(sections) > 1:
                    current_section = sections[1].strip() if len(sections) > 1 else "综合"

                # 提取 Q&A 对
                # 模式: "数字. 问题?\n答：回答"
                qa_pattern = re.compile(
                    r'(\d+)\.\s*(.+?)\s*\n答[：:]\s*(.+?)(?=\n\d+\.|\n## |\n---|\Z)',
                    re.DOTALL | re.MULTILINE
                )

                for match in qa_pattern.finditer(content):
                    q_num = match.group(1)
                    question = match.group(2).strip()
                    answer = match.group(3).strip()

                    # 提取关联的定额编号
                    codes = QUOTA_CODE_RE.findall(answer + question)

                    qa_pairs.append({
                        'id': f"{filename.replace('.md', '')}-{q_num}",
                        'source_file': filename,
                        'section': current_section,
                        'q_num': q_num,
                        'question': question,
                        'answer': answer,
                        'related_codes': codes,
                        'keywords': self._extract_keywords(question + answer)
                    })
            except Exception as e:
                print(f"⚠️ 提取 {filename} Q&A 失败: {e}")

        return qa_pairs

    def _load_gov_docs(self):
        """加载政府文件索引"""
        doc_index_file = DATA_DIR / "doc_index.json"
        if doc_index_file.exists():
            with open(doc_index_file, 'r', encoding='utf-8') as f:
                self.doc_index = json.load(f)
            self.gov_docs = list(self.doc_index.values())
            return

        # 构建文档索引
        self._build_doc_index()

    def _build_doc_index(self):
        """构建政府文件索引"""
        doc_index_file = DATA_DIR / "doc_index.json"
        categories = {
            '定额解释': '*解释*.md',
            '安全文明': '*安全*.md',
            '税金调整': '*税率*.md',
            '工程量规则': '*计算规则*.md',
            '政府文件': '*政府*.md',
            '定额站文件': '*定额站*.md',
            '机械台班': '*机械*.md',
            '配合比': '*配合比*.md',
        }

        for category, pattern in categories.items():
            files = list(QUOTA_MD_DIR.glob(pattern))
            for filepath in files:
                filename = filepath.name
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 提取关键词
                    keywords = self._extract_keywords(content[:2000])

                    # 提取文号
                    doc_numbers = re.findall(r'[\u4e00-\u9fa5〕〔】\[\]]{2,20}[\u4e00-\u9fa5]{2,10}号', content)

                    self.doc_index[filename] = {
                        'filename': filename,
                        'filepath': str(filepath),
                        'category': category,
                        'size': filepath.stat().st_size,
                        'keywords': keywords,
                        'doc_numbers': doc_numbers[:5],  # 最多5个文号
                        'content_preview': content[:500]
                    }
                except Exception as e:
                    print(f"⚠️ 索引 {filename} 失败: {e}")

        # 保存索引
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(doc_index_file, 'w', encoding='utf-8') as f:
            json.dump(self.doc_index, f, ensure_ascii=False, indent=2)

        self.gov_docs = list(self.doc_index.values())

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（使用 jieba）"""
        words = jieba.cut(text)
        # 过滤停用词
        stop_words = {'的', '了', '是', '在', '和', '与', '及', '或', '等', '可以', '应当', '必须', '应', '不得', '按', '执行', '规定', '相关', '相应', '该', '其', '这', '那', '一个', '一些', '一定', '一般', '具体', '根据', '按照', '参照', '执行', '实施', '进行', '采取', '使用', '采用', '包括', '含有', '其中', '部分', '全部', '整个', '其他', '另外', '同时', '以及', '并且', '或者', '但是', '然而', '因此', '所以', '如果', '假如', '假设', '当', '如', '若', '则', '凡', '每', '各', '本', '该', '此', '上述', '以下', '以上', '下列', '前', '后', '左', '右', '上', '下', '内', '外', '中', '间', '边', '旁', '侧', '端', '头', '尾', '始', '终', '起', '止', '高', '低', '长', '短', '大', '小', '多', '少', '轻', '重', '厚', '薄', '宽', '窄', '深', '浅', '远', '近', '新', '旧', '老', '早', '晚', '快', '慢', '冷', '热', '温', '凉', '暖', '寒', '暑', '阴', '晴', '雨', '雪', '风', '霜', '露', '雾', '冰', '水', '火', '土', '石', '金', '木', '草', '花', '树', '叶', '根', '枝', '干', '皮', '肉', '骨', '血', '气', '神', '精', '魂', '灵', '心', '意', '思', '想', '念', '情', '感', '爱', '恨', '喜', '怒', '哀', '乐', '悲', '欢', '离', '合', '生', '死', '存', '亡', '兴', '衰', '成', '败', '得', '失', '利', '弊', '福', '祸', '吉', '凶', '善', '恶', '美', '丑', '好', '坏', '优', '劣', '高', '低', '强', '弱', '硬', '软', '刚', '柔', '坚', '脆', '韧', '脆', '滑', '涩', '粘', '散', '聚', '分', '合', '开', '关', '启', '闭', '通', '断', '连', '断', '接', '离', '近', '远', '亲', '疏', '密', '稀', '浓', '淡', '清', '浊', '明', '暗', '亮', '黑', '白', '红', '黄', '蓝', '绿', '紫', '橙', '青', '灰', '棕', '粉', '银', '金', '铜', '铁', '钢', '铝', '锌', '铅', '锡', '镍', '铬', '锰', '钛', '钨', '钼', '钴', '镁', '钙', '钠', '钾', '锂', '铍', '硼', '碳', '氮', '氧', '氟', '氖', '氢', '氦', '氩', '氪', '氙', '氡'}
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]
        return list(set(keywords))

    def _expand_synonyms(self, keyword: str) -> List[str]:
        """扩展同义词"""
        expanded = {keyword}
        for syn, base in SYNONYMS.items():
            if base == keyword or syn == keyword:
                expanded.add(syn)
                expanded.add(base)
        return list(expanded)

    # ==================== 查询接口 ====================

    def query_by_code(self, code: str) -> Dict:
        """按定额编号查询"""
        self.load_all()
        code = code.upper()

        result = {
            'query': code,
            'quota': None,
            'qa_matches': [],
            'doc_matches': []
        }

        # 1. 查找定额
        for skill_name, records in self.quota_data.items():
            for record in records:
                if record.get('deh', '').upper() == code:
                    result['quota'] = {
                        'skill': skill_name,
                        'data': record
                    }
                    break
            if result['quota']:
                break

        # 2. 查找相关 Q&A
        if result['quota']:
            for qa in self.qa_pairs:
                if code in qa.get('related_codes', []):
                    result['qa_matches'].append(qa)

        # 3. 查找相关文件
        for doc in self.gov_docs:
            if code in doc.get('content_preview', ''):
                result['doc_matches'].append(doc)

        return result

    def search(self, keyword: str, top_k: int = 10) -> Dict:
        """关键词搜索"""
        self.load_all()

        result = {
            'query': keyword,
            'quota_matches': [],
            'qa_matches': [],
            'doc_matches': []
        }

        # 扩展同义词
        expanded_keywords = self._expand_synonyms(keyword)

        # 1. 搜索定额
        for skill_name, records in self.quota_data.items():
            for record in records:
                name = record.get('xmmc', '')
                chapter = record.get('chapter', '')
                score = 0

                for kw in expanded_keywords:
                    if kw in name:
                        score += 3
                    if kw in chapter:
                        score += 2

                if score > 0:
                    result['quota_matches'].append({
                        'skill': skill_name,
                        'data': record,
                        'score': score
                    })

        # 排序并限制数量
        result['quota_matches'].sort(key=lambda x: x['score'], reverse=True)
        result['quota_matches'] = result['quota_matches'][:top_k]

        # 2. 搜索 Q&A
        for qa in self.qa_pairs:
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            score = 0

            for kw in expanded_keywords:
                if kw in question:
                    score += 5
                if kw in answer:
                    score += 2

            if score > 0:
                result['qa_matches'].append({
                    'data': qa,
                    'score': score
                })

        result['qa_matches'].sort(key=lambda x: x['score'], reverse=True)
        result['qa_matches'] = result['qa_matches'][:top_k]

        # 3. 搜索文档
        for doc in self.gov_docs:
            preview = doc.get('content_preview', '')
            keywords = doc.get('keywords', [])
            score = 0

            for kw in expanded_keywords:
                if kw in preview:
                    score += 3
                if kw in keywords:
                    score += 2

            if score > 0:
                result['doc_matches'].append({
                    'data': doc,
                    'score': score
                })

        result['doc_matches'].sort(key=lambda x: x['score'], reverse=True)
        result['doc_matches'] = result['doc_matches'][:top_k]

        return result

    def ask(self, question: str) -> Dict:
        """自然语言问答"""
        self.load_all()

        result = {
            'question': question,
            'qa_answer': None,
            'related_quota': [],
            'related_docs': []
        }

        # 提取关键词
        q_keywords = self._extract_keywords(question)

        # 1. 匹配 Q&A
        best_match = None
        best_score = 0

        for qa in self.qa_pairs:
            qa_keywords = qa.get('keywords', [])
            score = 0

            for kw in q_keywords:
                if kw in qa_keywords:
                    score += 3
                # 检查问题相似度
                if kw in qa.get('question', ''):
                    score += 5

            if score > best_score:
                best_score = score
                best_match = qa

        if best_match and best_score > 0:
            result['qa_answer'] = best_match

            # 2. 查找相关定额
            for code in best_match.get('related_codes', []):
                quota_result = self.query_by_code(code)
                if quota_result.get('quota'):
                    result['related_quota'].append(quota_result['quota'])

            # 3. 查找相关文件
            source_file = best_match.get('source_file', '')
            for doc in self.gov_docs:
                if source_file in doc.get('filename', ''):
                    result['related_docs'].append(doc)

        return result

    def query_doc(self, doc_number: str) -> Dict:
        """按文号查询政府文件"""
        self.load_all()

        result = {
            'query': doc_number,
            'documents': []
        }

        for doc in self.gov_docs:
            doc_numbers = doc.get('doc_numbers', [])
            filename = doc.get('filename', '')

            if doc_number in doc_numbers or doc_number in filename:
                result['documents'].append(doc)

        return result

    def query(self, text: str) -> Dict:
        """综合查询（推荐入口）"""
        self.load_all()

        result = {
            'query': text,
            'type': 'unknown',
            'data': {}
        }

        # 判断查询类型
        # 1. 定额编号
        codes = QUOTA_CODE_RE.findall(text)
        if codes:
            result['type'] = 'quota_code'
            result['data'] = self.query_by_code(codes[0])
            return result

        # 2. 文号
        if re.search(r'[\u4e00-\u9fa5〕〔】\[\]]{2,}号', text):
            result['type'] = 'doc_number'
            result['data'] = self.query_doc(text)
            return result

        # 3. 问题（包含问号或疑问词）
        question_words = ['吗', '呢', '怎么', '如何', '什么', '哪些', '多少', '哪里', '怎样']
        if any(w in text for w in question_words) or '？' in text or '?' in text:
            result['type'] = 'question'
            result['data'] = self.ask(text)
            return result

        # 4. 关键词搜索（默认）
        result['type'] = 'keyword'
        result['data'] = self.search(text)
        return result


# ==================== 便捷函数 ====================




def quick_search(keyword: str) -> List[Dict]:
    """快速搜索"""
    matcher = QuotaMatcher()
    return matcher.search(keyword)

def quick_ask(question: str) -> Optional[Dict]:
    """快速问答"""
    matcher = QuotaMatcher()
    result = matcher.ask(question)
    return result.get('qa_answer')

if __name__ == '__main__':
    # 测试
    matcher = QuotaMatcher()

    print("=== 测试: 定额编号查询 ===")
    result = matcher.query_by_code("DA0001")
    print(f"定额: {result['quota']}")
    print(f"Q&A: {len(result['qa_matches'])} 条")
    print(f"文档: {len(result['doc_matches'])} 条")

    print("\n=== 测试: 关键词搜索 ===")
    result = matcher.search("混凝土")
    print(f"定额: {len(result['quota_matches'])} 条")
    print(f"Q&A: {len(result['qa_matches'])} 条")
    print(f"文档: {len(result['doc_matches'])} 条")

    print("\n=== 测试: 自然语言问答 ===")
    result = matcher.ask("安全文明施工费怎么算？")
    print(f"答案: {result['qa_answer']}")