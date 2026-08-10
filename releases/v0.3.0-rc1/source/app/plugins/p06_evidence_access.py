from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


_SUBMIT_ROLES = {
    "project_manager",
    "cost_lead",
    "cost_engineer",
    "technical",
    "production",
    "measurement",
    "laboratory",
    "records",
    "materials",
    "equipment",
}
_VERIFY_ROLES = {"project_manager", "cost_lead"}


@register(CapabilityManifest(id="p06.evidence_submit_gate", version="1.0.0", risk="low"))
def evidence_submit_gate(db, project_id, actor, role, payload):
    evidence_type = (payload.get("evidence_type") or "").strip()
    task_id = (payload.get("task_id") or "").strip()
    if role not in _SUBMIT_ROLES:
        return CapabilityResult("failed", {"reason": "role_not_allowed_to_submit_evidence", "role": role})
    if not evidence_type or not task_id:
        return CapabilityResult("needs_information", {"required": ["evidence_type", "task_id"]})
    return CapabilityResult("success", {
        "allowed": True,
        "action": "submit_evidence",
        "role": role,
        "task_id": task_id,
        "evidence_type": evidence_type,
        "verification_state": "candidate",
        "automatic_verification": False,
    })


@register(CapabilityManifest(id="p06.evidence_verify_gate", version="1.0.0", risk="high"))
def evidence_verify_gate(db, project_id, actor, role, payload):
    evidence_id = (payload.get("evidence_id") or "").strip()
    decision = (payload.get("decision") or "").strip().lower()
    if role not in _VERIFY_ROLES:
        return CapabilityResult("failed", {"reason": "role_not_allowed_to_verify_evidence", "role": role})
    if not evidence_id or decision not in {"verified", "rejected"}:
        return CapabilityResult("needs_information", {"required": ["evidence_id", "decision: verified|rejected"]})
    return CapabilityResult("success", {
        "allowed": True,
        "action": "verify_evidence",
        "role": role,
        "evidence_id": evidence_id,
        "decision": decision,
        "human_review_required": True,
        "automatic_verification": False,
    })
