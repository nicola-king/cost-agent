from datetime import datetime, timezone
from sqlalchemy import select
from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult
from app.core.models import Rule

@register(CapabilityManifest(id="p08.rule_applicability", version="1.0.0", risk="high"))
def rule_applicability(db, project_id, actor, role, payload):
    region = payload.get("region")
    scope = payload.get("scope")
    at = datetime.fromisoformat(payload["at"]) if payload.get("at") else datetime.now(timezone.utc)
    rules = db.scalars(select(Rule)).all()
    applicable = []
    for r in rules:
        if r.region and region and r.region != region: continue
        if r.scope and scope and r.scope != scope: continue
        if r.effective_from and at < r.effective_from: continue
        if r.effective_to and at > r.effective_to: continue
        applicable.append({"id": r.id, "title": r.title, "rule_type": r.rule_type, "classification": r.classification})
    outcome = "success" if applicable else "needs_information"
    return CapabilityResult(outcome, {"applicable_rules": applicable, "at": at.isoformat(), "no_applicable_rule_found": not applicable})
