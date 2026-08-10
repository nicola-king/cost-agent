from pydantic import BaseModel, Field
from typing import Any

class ProjectCreate(BaseModel):
    name: str
    region: str | None = None

class BOQCreate(BaseModel):
    code: str | None = None
    name: str
    description: str | None = None
    unit: str
    award_quantity: float | None = None
    award_unit_price: float | None = None

class MeasurementCreate(BaseModel):
    object_id: str
    measurement_type: str
    quantity: float
    unit: str
    method: str
    scope: dict[str, Any] | None = None

class CapabilityRequest(BaseModel):
    capability_id: str
    project_id: str
    actor: str = "user"
    role: str = "cost_lead"
    payload: dict[str, Any] = Field(default_factory=dict)

class TaskCreate(BaseModel):
    title: str
    department: str | None = None
    role: str | None = None
    assignee: str | None = None
    due_at: str | None = None

class TaskAck(BaseModel):
    actor: str

class StageUpdate(BaseModel):
    completed_items: float | None = None
    required_items: float | None = None
    evidence_closure: float | None = None
    details: dict[str, Any] | None = None
