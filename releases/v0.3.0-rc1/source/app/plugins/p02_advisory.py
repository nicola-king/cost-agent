from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult
from app.skills.advisory_search import AdvisoryDocument, AdvisorySearchIndex, classify_similarity


def _docs(payload: dict) -> list[AdvisoryDocument]:
    rows = payload.get("documents") or []
    docs = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        text = str(row.get("text") or row.get("name") or "").strip()
        if not text:
            continue
        docs.append(AdvisoryDocument(
            id=str(row.get("id") or f"DOC-{idx + 1}"),
            text=text,
            metadata={k: v for k, v in row.items() if k not in {"id", "text"}},
        ))
    return docs


@register(CapabilityManifest(
    id="p02.advisory_match",
    version="1.0.0",
    risk="low",
    reads=["candidate_documents"],
    outputs=["candidate", "recommendation"],
))
def advisory_match(db, project_id, actor, role, payload):
    query = str(payload.get("query", "")).strip()
    docs = _docs(payload)
    if not query:
        return CapabilityResult("needs_information", {"required": ["query"]})
    if not docs:
        return CapabilityResult("needs_information", {"required": ["documents"]})
    rows = AdvisorySearchIndex(docs).search(query, top_k=int(payload.get("top_k", 10)))
    for row in rows:
        row["classification"] = classify_similarity(query, row["text"], row["score"])
    return CapabilityResult(
        "success" if rows else "needs_information",
        {
            "query": query,
            "results": rows,
            "advisory_only": True,
            "verified": False,
            "human_review_required": True,
        },
        candidates=rows,
    )
