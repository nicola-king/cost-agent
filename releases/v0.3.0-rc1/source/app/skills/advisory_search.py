from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

SYNONYMS = {
    "砼": "混凝土",
    "现浇砼": "现浇混凝土",
    "螺纹钢": "钢筋",
    "圆钢": "钢筋",
    "木模板": "模板",
    "钢模板": "模板",
    "安全文明": "安全文明施工",
    "土方": "土石方",
    "石方": "土石方",
    "给水管": "管道",
    "排水管": "管道",
    "电线": "电缆",
    "电缆桥架": "桥架",
    "暖通": "通风空调",
    "空调": "通风空调",
    "消防": "消防工程",
    "给水": "给排水",
    "排水": "给排水",
    "粉刷": "抹灰",
    "吊顶": "天棚吊顶",
    "支护": "基坑支护",
    "路面": "道路工程",
    "路基": "道路工程",
    "灌注桩": "桩基工程",
    "预制桩": "桩基工程",
}

STOP_WORDS = {
    "的", "了", "是", "在", "和", "与", "及", "或", "等", "可以", "应当", "必须",
    "应", "不得", "按", "执行", "规定", "相关", "相应", "该", "其", "根据", "按照",
    "参照", "实施", "进行", "采用", "包括", "其中", "部分", "全部", "其他", "同时",
}


def normalize_text(text: str) -> str:
    value = str(text or "").strip().lower()
    for src, dst in sorted(SYNONYMS.items(), key=lambda kv: len(kv[0]), reverse=True):
        value = value.replace(src.lower(), dst.lower())
    return re.sub(r"\s+", " ", value)


def tokenize(text: str) -> list[str]:
    """Dependency-free tokenizer for Chinese engineering text.

    Keeps alphanumeric/code tokens and Chinese 2-4 gram fragments. It is deliberately
    deterministic so ranking can be audited and reproduced without an external model.
    """
    normalized = normalize_text(text)
    tokens: list[str] = []
    for token in re.findall(r"[a-z0-9.#+-]+|[\u4e00-\u9fff]+", normalized):
        if token in STOP_WORDS:
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            if len(token) <= 4:
                tokens.append(token)
            for n in (2, 3, 4):
                if len(token) >= n:
                    tokens.extend(token[i:i+n] for i in range(len(token) - n + 1))
        else:
            tokens.append(token)
    return tokens


@dataclass(frozen=True)
class AdvisoryDocument:
    id: str
    text: str
    metadata: dict


class AdvisorySearchIndex:
    def __init__(self, documents: Iterable[AdvisoryDocument]):
        self.documents = list(documents)
        self._tokens = {doc.id: tokenize(doc.text) for doc in self.documents}
        self._idf: dict[str, float] = {}
        self._vectors: dict[str, dict[str, float]] = {}
        self._build()

    def _build(self) -> None:
        n_docs = len(self.documents)
        if not n_docs:
            return
        df: Counter[str] = Counter()
        for words in self._tokens.values():
            df.update(set(words))
        self._idf = {word: math.log((n_docs + 1) / (freq + 1)) + 1 for word, freq in df.items()}
        for doc in self.documents:
            self._vectors[doc.id] = self._vector(self._tokens[doc.id])

    def _vector(self, words: list[str]) -> dict[str, float]:
        tf = Counter(words)
        max_tf = max(tf.values(), default=1)
        return {word: (count / max_tf) * self._idf.get(word, 0.0) for word, count in tf.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        common = set(a) & set(b)
        if not common:
            return 0.0
        dot = sum(a[k] * b[k] for k in common)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        q = normalize_text(query)
        if not q:
            return []
        qv = self._vector(tokenize(q))
        ranked = []
        for doc in self.documents:
            score = self._cosine(qv, self._vectors.get(doc.id, {}))
            normalized_doc = normalize_text(doc.text)
            if q in normalized_doc:
                score += 0.35
            if score <= 0:
                continue
            ranked.append({
                "id": doc.id,
                "score": round(min(score, 1.0), 6),
                "text": doc.text,
                "metadata": doc.metadata,
                "state": "CANDIDATE",
                "decision_authority": "NONE",
            })
        ranked.sort(key=lambda row: (-row["score"], row["id"]))
        return ranked[: max(1, min(int(top_k), 100))]


def classify_similarity(query: str, candidate_text: str, score: float) -> dict:
    q = normalize_text(query)
    c = normalize_text(candidate_text)
    if q and q == c:
        relation = "SAME_CANDIDATE"
    elif q and (q in c or c in q or score >= 0.58):
        relation = "SIMILAR_CANDIDATE"
    else:
        relation = "WEAK_CANDIDATE"
    return {
        "relation": relation,
        "state": "RECOMMENDATION",
        "requires_human_review": True,
        "verified": False,
    }
