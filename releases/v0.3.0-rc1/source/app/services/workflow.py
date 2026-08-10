from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.models import WorkflowState
from app.services.idgen import new_id

STAGES = [
    ("project_init", "项目初始化"),
    ("tender_compare", "招投标合同对比"),
    ("clearing", "清标"),
    ("baseline0", "0号台账"),
    ("evidence_plan", "证据策划"),
    ("cost_plan", "成本策划"),
    ("quantity_price_baseline", "量价基线"),
    ("startup_briefing", "开工造价宣讲"),
    ("dynamic_cost", "施工过程动态造价"),
    ("change_claim", "变更/签证/索赔"),
    ("monthly_close", "月度造价闭环"),
    ("monthly_briefing", "月度造价宣讲"),
    ("payment", "过程计量/支付"),
    ("settlement", "竣工结算"),
    ("preaudit", "模拟审计/审定"),
    ("archive", "数字资产归档"),
]

def ensure_workflow(db: Session, project_id: str):
    existing = {x.stage_key for x in db.scalars(select(WorkflowState).where(WorkflowState.project_id == project_id)).all()}
    for key, _ in STAGES:
        if key not in existing:
            db.add(WorkflowState(id=new_id("WF"), project_id=project_id, stage_key=key))
    db.flush()

def set_stage(db: Session, project_id: str, stage_key: str, *, completed_items: float | None = None, required_items: float | None = None, evidence_closure: float | None = None, details: dict | None = None):
    ensure_workflow(db, project_id)
    row = db.scalar(select(WorkflowState).where(WorkflowState.project_id == project_id, WorkflowState.stage_key == stage_key))
    if completed_items is not None: row.completed_items = completed_items
    if required_items is not None: row.required_items = required_items
    if evidence_closure is not None: row.evidence_closure = evidence_closure
    if details is not None: row.details = details
    pct = 0 if not row.required_items else min(1.0, row.completed_items / row.required_items)
    if row.required_items and pct >= 1 and (row.evidence_closure is None or row.evidence_closure >= 1): row.status = "complete"
    elif row.completed_items or row.evidence_closure: row.status = "partial"
    else: row.status = "not_started"
    row.updated_at = datetime.now(timezone.utc)
    return row

def workflow_view(db: Session, project_id: str):
    ensure_workflow(db, project_id)
    db.flush()
    rows = {x.stage_key: x for x in db.scalars(select(WorkflowState).where(WorkflowState.project_id == project_id)).all()}
    out=[]
    for key,name in STAGES:
        r=rows[key]
        task_pct = 0 if not r.required_items else min(100.0, r.completed_items / r.required_items * 100)
        ev_pct = None if r.evidence_closure is None else r.evidence_closure * 100
        out.append({"key":key,"name":name,"status":r.status,"task_progress":round(task_pct,1),"evidence_closure":None if ev_pct is None else round(ev_pct,1),"details":r.details})
    return out
