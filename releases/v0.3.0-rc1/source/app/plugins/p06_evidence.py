from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult
from app.core.models import BOQItem, Task, Evidence, EvidenceSubmission


@register(CapabilityManifest(id="p06.evidence_plan", version="1.0.1", risk="medium"))
def evidence_plan(db, project_id, actor, role, payload):
    boq_id = (payload.get("boq_id") or "").strip()
    requirements = payload.get("requirements") or []
    if not boq_id:
        return CapabilityResult("needs_information", {"required": ["boq_id"]})
    boq = db.scalar(select(BOQItem).where(BOQItem.project_id == project_id, BOQItem.id == boq_id))
    if not boq:
        return CapabilityResult("needs_information", {"required": ["valid_boq_id"]})
    if not requirements:
        return CapabilityResult("needs_information", {"required": ["requirements"]})

    created = []
    boq_marker = f"[BOQ:{boq_id}]"
    for idx, req in enumerate(requirements, start=1):
        evidence_type = (req.get("evidence_type") or "").strip()
        department = (req.get("department") or "").strip()
        if not evidence_type or not department:
            return CapabilityResult(
                "needs_information",
                {"required": ["department", "evidence_type"], "requirement_index": idx - 1},
            )
        task_id = req.get("task_id") or f"TASK-{project_id}-{boq_id}-{idx}"
        existing = db.get(Task, task_id)
        evidence_marker = f"[EVID:{evidence_type}]"
        raw_title = req.get("title") or f"{boq.name} / {evidence_type}"
        title = raw_title
        if not title.startswith(boq_marker):
            title = f"{boq_marker} {title}"
        if evidence_marker not in title:
            title = f"{boq_marker} {evidence_marker} " + title.removeprefix(boq_marker).strip()
        if existing is None:
            task = Task(
                id=task_id,
                project_id=project_id,
                title=title,
                department=department,
                role=req.get("role"),
                assignee=req.get("assignee"),
                status="open",
                due_at=req.get("due_at"),
            )
            db.add(task)
        else:
            existing.title = title
            existing.department = department
            existing.role = req.get("role")
            existing.assignee = req.get("assignee")
            existing.due_at = req.get("due_at")
        created.append(
            {
                "task_id": task_id,
                "boq_id": boq_id,
                "department": department,
                "role": req.get("role"),
                "assignee": req.get("assignee"),
                "evidence_type": evidence_type,
                "required_channel": req.get("required_channel"),
                "due_at": req.get("due_at").isoformat() if hasattr(req.get("due_at"), "isoformat") else req.get("due_at"),
            }
        )
    db.commit()
    return CapabilityResult("success", {"boq_id": boq_id, "boq_name": boq.name, "requirements": created})


def _required_evidence_type(title: str | None) -> str | None:
    text = title or ""
    marker = "[EVID:"
    start = text.find(marker)
    if start < 0:
        return None
    end = text.find("]", start)
    if end < 0:
        return None
    return text[start + len(marker):end].strip() or None


@register(CapabilityManifest(id="p06.evidence_closure", version="1.0.1", risk="low"))
def evidence_closure(db, project_id, actor, role, payload):
    boq_id = (payload.get("boq_id") or "").strip()
    if not boq_id:
        return CapabilityResult("needs_information", {"required": ["boq_id"]})

    marker = f"[BOQ:{boq_id}]"
    tasks = db.scalars(select(Task).where(Task.project_id == project_id)).all()
    relevant = [t for t in tasks if (t.title or "").startswith(marker)]
    if not relevant:
        return CapabilityResult("needs_information", {"required": ["evidence_plan"], "boq_id": boq_id})

    rows = []
    closed = 0
    for task in relevant:
        required_type = _required_evidence_type(task.title)
        submissions = db.scalars(select(EvidenceSubmission).where(EvidenceSubmission.project_id == project_id, EvidenceSubmission.task_id == task.id)).all()
        verified = []
        rejected_type_mismatch = []
        for sub in submissions:
            ev = db.get(Evidence, sub.evidence_id)
            if not ev or sub.verification_state != "verified" or ev.status != "verified":
                continue
            if required_type and ev.evidence_type != required_type:
                rejected_type_mismatch.append({"evidence_id": ev.id, "actual_type": ev.evidence_type, "required_type": required_type})
                continue
            verified.append({
                "evidence_id": ev.id,
                "evidence_type": ev.evidence_type,
                "submission_id": sub.id,
                "source_channel": sub.source_channel,
                "capture_time": sub.capture_time.isoformat() if sub.capture_time else None,
            })
        is_closed = bool(verified)
        if is_closed:
            closed += 1
        rows.append({
            "task_id": task.id,
            "required_evidence_type": required_type,
            "department": task.department,
            "role": task.role,
            "assignee": task.assignee,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "closed": is_closed,
            "verified_evidence": verified,
            "rejected_type_mismatch": rejected_type_mismatch,
        })

    total = len(rows)
    ratio = 0.0 if total == 0 else round(closed / total, 4)
    outcome = "success" if closed == total else ("partial" if closed else "needs_information")
    return CapabilityResult(outcome, {
        "boq_id": boq_id,
        "total_requirements": total,
        "closed_requirements": closed,
        "closure_ratio": ratio,
        "requirements": rows,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    })
