from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any
from sqlalchemy.orm import Session
from app.core.models import AuditEvent
from app.services.idgen import new_id

@dataclass
class CapabilityManifest:
    id: str
    version: str
    risk: str
    reads: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=lambda: ["observation", "candidate", "issue"])
    commercial: bool = False

@dataclass
class CapabilityResult:
    outcome: str
    data: dict[str, Any]
    observations: list[dict] = field(default_factory=list)
    candidates: list[dict] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)

class CapabilityGateway:
    def __init__(self):
        self._handlers: dict[str, tuple[CapabilityManifest, Callable]] = {}

    def register(self, manifest: CapabilityManifest, handler: Callable):
        self._handlers[manifest.id] = (manifest, handler)

    def manifests(self):
        return [m for m, _ in self._handlers.values()]

    def execute(self, db: Session, capability_id: str, project_id: str, actor: str, role: str, payload: dict):
        if capability_id not in self._handlers:
            raise KeyError(capability_id)
        manifest, handler = self._handlers[capability_id]
        if manifest.commercial and role not in {"project_manager", "cost_lead"}:
            result = CapabilityResult("failed", {"reason": "commercial_confidential"})
        else:
            result = handler(db=db, project_id=project_id, actor=actor, role=role, payload=payload)
        db.add(AuditEvent(
            id=new_id("AUD"), project_id=project_id, actor=actor,
            action=f"capability:{capability_id}", object_id=payload.get("object_id"),
            details={"version": manifest.version, "outcome": result.outcome}
        ))
        db.commit()
        return manifest, result

gateway = CapabilityGateway()
