from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult
from app.skills.advisory_search import AdvisoryDocument, AdvisorySearchIndex


@register(CapabilityManifest(
    id="p08.advisory_search",
    version="1.0.0",
    risk="low",
    reads=["rule_search_projection"],
    outputs=["candidate"],
))
def advisory_rule_search(db, project_id, actor, role, payload):
    query = str(payload.get("query", "")).strip()
    if not query:
        return CapabilityResult("needs_information", {"required": ["query"]})
    documents = []
    for idx, row in enumerate(payload.get("documents") or []):
        if not isinstance(row, dict):
            continue
        text = str(row.get("text") or row.get("content") or "").strip()
        if not text:
            continue
        documents.append(AdvisoryDocument(
            id=str(row.get("id") or f"RULE-CAND-{idx+1}"),
            text=text,
            metadata={k: v for k, v in row.items() if k not in {"id", "text", "content"}},
        ))
    if not documents:
        return CapabilityResult("needs_information", {"required": ["documents"]})
    rows = AdvisorySearchIndex(documents).search(query, top_k=int(payload.get("top_k", 10)))
    return CapabilityResult(
        "success" if rows else "needs_information",
        {
            "query": query,
            "results": rows,
            "advisory_only": True,
            "verified": False,
            "rule_applicability_not_determined": True,
        },
        candidates=rows,
    )
