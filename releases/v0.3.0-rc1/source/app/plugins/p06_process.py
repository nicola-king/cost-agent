from sqlalchemy import select
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult
from app.core.models import ChangeEvent, ReviewIssue, Task

@register(CapabilityManifest(id="p06.monthly_snapshot", version="1.0.0", risk="medium", commercial=True))
def monthly_snapshot(db, project_id, actor, role, payload):
    changes = db.scalars(select(ChangeEvent).where(ChangeEvent.project_id == project_id)).all()
    issues = db.scalars(select(ReviewIssue).where(ReviewIssue.project_id == project_id, ReviewIssue.status != "resolved")).all()
    tasks = db.scalars(select(Task).where(Task.project_id == project_id, Task.status != "closed")).all()
    return CapabilityResult("success", {"change_events": len(changes), "open_issues": len(issues), "open_tasks": len(tasks), "high_risk_issues": sum(1 for x in issues if x.risk_level in {"high", "critical"})})
