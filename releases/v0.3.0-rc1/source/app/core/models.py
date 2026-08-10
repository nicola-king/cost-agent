from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Source(Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str | None] = mapped_column(String, ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    sha256: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str | None] = mapped_column(String)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime)
    immutable: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("sha256", "project_id", name="uq_source_hash_project"),)

class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    source_id: Mapped[str | None] = mapped_column(String, ForeignKey("sources.id"))
    evidence_type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    locator: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="unknown")
    confidence: Mapped[float | None] = mapped_column(Float)
    created_by: Mapped[str] = mapped_column(String, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Relation(Base):
    __tablename__ = "relations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    source_object_id: Mapped[str] = mapped_column(String, nullable=False)
    relation_type: Mapped[str] = mapped_column(String, nullable=False)
    target_object_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="candidate")
    created_by: Mapped[str] = mapped_column(String, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class BOQItem(Base):
    __tablename__ = "boq_items"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    code: Mapped[str | None] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    award_quantity: Mapped[float | None] = mapped_column(Float)
    award_unit_price: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="verified")

class Measurement(Base):
    __tablename__ = "measurements"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    object_id: Mapped[str] = mapped_column(String, nullable=False)
    measurement_type: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    scope: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="calculated")
    measured_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Calculation(Base):
    __tablename__ = "calculations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    calculation_type: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    rule_refs: Mapped[list] = mapped_column(JSON, default=list)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    output_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="calculated")
    executed_by: Mapped[str] = mapped_column(String, default="system")
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ChangeEvent(Base):
    __tablename__ = "change_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="candidate")
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime)
    major: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class CostItem(Base):
    __tablename__ = "cost_items"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    object_id: Mapped[str | None] = mapped_column(String)
    cost_type: Mapped[str] = mapped_column(String, nullable=False)
    cost_state: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String, default="commercial_confidential")
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ReviewIssue(Base):
    __tablename__ = "review_issues"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    object_id: Mapped[str] = mapped_column(String, nullable=False)
    issue_type: Mapped[str] = mapped_column(String, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, default="medium")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="open")
    impact_amount: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    rule_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, ForeignKey("sources.id"))
    region: Mapped[str | None] = mapped_column(String)
    scope: Mapped[str | None] = mapped_column(String)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime)
    expression: Mapped[dict | None] = mapped_column(JSON)
    classification: Mapped[str] = mapped_column(String, default="external")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    department: Mapped[str | None] = mapped_column(String)
    role: Mapped[str | None] = mapped_column(String)
    assignee: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="open")
    due_at: Mapped[datetime | None] = mapped_column(DateTime)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str | None] = mapped_column(String)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    object_id: Mapped[str | None] = mapped_column(String)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class WorkflowState(Base):
    __tablename__ = "workflow_states"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    stage_key: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="not_started")
    completed_items: Mapped[float] = mapped_column(Float, default=0)
    required_items: Mapped[float] = mapped_column(Float, default=0)
    evidence_closure: Mapped[float | None] = mapped_column(Float)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("project_id", "stage_key", name="uq_workflow_stage_project"),)

class EvidenceSubmission(Base):
    __tablename__ = "evidence_submissions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    evidence_id: Mapped[str] = mapped_column(String, ForeignKey("evidence.id"))
    task_id: Mapped[str | None] = mapped_column(String, ForeignKey("tasks.id"))
    department: Mapped[str | None] = mapped_column(String)
    role: Mapped[str | None] = mapped_column(String)
    assignee: Mapped[str | None] = mapped_column(String)
    work_location: Mapped[str | None] = mapped_column(String)
    object_id: Mapped[str | None] = mapped_column(String)
    capture_time: Mapped[datetime | None] = mapped_column(DateTime)
    upload_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    source_channel: Mapped[str] = mapped_column(String, default="web")
    verification_state: Mapped[str] = mapped_column(String, default="candidate")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
