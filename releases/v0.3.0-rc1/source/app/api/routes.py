from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.models import Project, Source, Evidence, EvidenceSubmission, BOQItem, Measurement, AuditEvent, ReviewIssue, Task, ChangeEvent, Rule
from app.core.schemas import ProjectCreate, BOQCreate, MeasurementCreate, CapabilityRequest, TaskCreate, TaskAck, StageUpdate
from app.services.idgen import new_id
from app.services.hashutil import sha256_file
from app.services.capability import gateway
from app.services.policy import can_view_commercial
from app.services.workflow import ensure_workflow, set_stage, workflow_view
from app.adapters_xlsx import read_xlsx_rows, map_boq_rows

router = APIRouter(prefix="/api")
ROOT = Path(__file__).resolve().parents[2]
STORAGE = ROOT / "data" / "sources"
STORAGE.mkdir(parents=True, exist_ok=True)

@router.get("/health")
def health():
    return {"status":"ok","architecture":"v1.0-frozen","mode":"local-first"}

@router.post("/projects")
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    p=Project(id=new_id("PRJ"),name=body.name,region=body.region)
    db.add(p); ensure_workflow(db,p.id); db.commit(); db.refresh(p)
    return {"id":p.id,"name":p.name,"region":p.region}

@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return [{"id":x.id,"name":x.name,"region":x.region,"status":x.status} for x in db.scalars(select(Project)).all()]

@router.post("/projects/{project_id}/sources")
def upload_source(project_id:str,source_type:str=Form(...),title:str=Form(...),version:str|None=Form(None),file:UploadFile=File(...),db:Session=Depends(get_db)):
    if not db.get(Project,project_id): raise HTTPException(404,"project not found")
    tmp=STORAGE/f".tmp-{new_id('SRC')}-{file.filename or 'source.bin'}"
    with tmp.open("wb") as out: shutil.copyfileobj(file.file,out)
    digest=sha256_file(tmp)
    existing=db.scalar(select(Source).where(Source.project_id==project_id,Source.sha256==digest))
    if existing:
        tmp.unlink(missing_ok=True); return {"id":existing.id,"deduplicated":True,"sha256":existing.sha256}
    sid=new_id("SRC"); dest_dir=STORAGE/project_id/sid; dest_dir.mkdir(parents=True,exist_ok=True); dest=dest_dir/(file.filename or "source.bin"); tmp.replace(dest)
    src=Source(id=sid,project_id=project_id,title=title,source_type=source_type,file_path=str(dest),sha256=digest,version=version,immutable=True)
    db.add(src); db.add(AuditEvent(id=new_id("AUD"),project_id=project_id,actor="uploader",action="source_ingested",object_id=sid,details={"sha256":digest,"immutable":True})); db.commit()
    return {"id":sid,"sha256":digest,"immutable":True}

@router.get("/projects/{project_id}/sources")
def list_sources(project_id:str,db:Session=Depends(get_db)):
    rows=db.scalars(select(Source).where(Source.project_id==project_id)).all()
    return [{"id":x.id,"title":x.title,"type":x.source_type,"version":x.version,"sha256":x.sha256,"immutable":x.immutable} for x in rows]

@router.post("/projects/{project_id}/boq")
def create_boq(project_id:str,body:BOQCreate,db:Session=Depends(get_db)):
    if not db.get(Project,project_id): raise HTTPException(404,"project not found")
    x=BOQItem(id=new_id("BOQ"),project_id=project_id,**body.model_dump()); db.add(x); db.commit(); db.refresh(x)
    return {"id":x.id,**body.model_dump()}

@router.get("/projects/{project_id}/boq")
def list_boq(project_id:str,db:Session=Depends(get_db)):
    rows=db.scalars(select(BOQItem).where(BOQItem.project_id==project_id)).all()
    return [{"id":x.id,"code":x.code,"name":x.name,"unit":x.unit,"award_quantity":x.award_quantity,"award_unit_price":x.award_unit_price} for x in rows]

@router.post("/projects/{project_id}/measurements")
def create_measurement(project_id:str,body:MeasurementCreate,db:Session=Depends(get_db)):
    x=Measurement(id=new_id("M"),project_id=project_id,**body.model_dump()); db.add(x); db.commit(); db.refresh(x)
    return {"id":x.id,**body.model_dump()}

@router.post("/capabilities/execute")
def execute_capability(body:CapabilityRequest,db:Session=Depends(get_db)):
    try: manifest,result=gateway.execute(db,body.capability_id,body.project_id,body.actor,body.role,body.payload)
    except KeyError: raise HTTPException(404,"capability not found")
    return {"manifest":{"id":manifest.id,"version":manifest.version,"risk":manifest.risk},"outcome":result.outcome,"data":result.data,"observations":result.observations,"candidates":result.candidates,"issues":result.issues}

@router.get("/capabilities")
def capabilities():
    return [{"id":x.id,"version":x.version,"risk":x.risk,"commercial":x.commercial} for x in gateway.manifests()]

@router.get("/projects/{project_id}/commercial-access")
def commercial_access(project_id:str,role:str=Query("cost_engineer")):
    d=can_view_commercial(role); return {"project_id":project_id,"role":role,"allowed":d.allowed,"reason":d.reason}

@router.post("/projects/{project_id}/boq/import-xlsx")
def import_boq_xlsx(project_id:str,header_row:int=Form(1),sheet_name:str|None=Form(None),file:UploadFile=File(...),db:Session=Depends(get_db)):
    if not db.get(Project,project_id): raise HTTPException(404,"project not found")
    filename=file.filename or "award_boq.xlsx"
    if not filename.lower().endswith(".xlsx"): raise HTTPException(400,"only .xlsx is supported in MVP")
    tmp=STORAGE/f".tmp-{new_id('SRC')}-{filename}"
    with tmp.open("wb") as out: shutil.copyfileobj(file.file,out)
    digest=sha256_file(tmp)
    existing=db.scalar(select(Source).where(Source.project_id==project_id,Source.sha256==digest))
    if existing: src=existing; tmp.unlink(missing_ok=True)
    else:
        sid=new_id("SRC"); dest_dir=STORAGE/project_id/sid; dest_dir.mkdir(parents=True,exist_ok=True); dest=dest_dir/filename; tmp.replace(dest)
        src=Source(id=sid,project_id=project_id,title=filename,source_type="award_boq",file_path=str(dest),sha256=digest,immutable=True); db.add(src); db.flush()
    try: mapped=map_boq_rows(list(read_xlsx_rows(src.file_path,sheet_name=sheet_name)),header_row=header_row)
    except Exception as e: db.rollback(); raise HTTPException(400,f"xlsx parse failed: {e}")
    created=0; skipped=0
    for item in mapped:
        q=select(BOQItem).where(BOQItem.project_id==project_id,BOQItem.code==item["code"]) if item["code"] else select(BOQItem).where(BOQItem.project_id==project_id,BOQItem.name==item["name"],BOQItem.unit==item["unit"])
        if db.scalar(q): skipped+=1; continue
        db.add(BOQItem(id=new_id("BOQ"),project_id=project_id,**item)); created+=1
    set_stage(db,project_id,"project_init",completed_items=1,required_items=1)
    set_stage(db,project_id,"clearing",completed_items=created if created else 0,required_items=max(created,1),details={"award_boq_source_id":src.id,"imported":created,"skipped":skipped})
    db.add(AuditEvent(id=new_id("AUD"),project_id=project_id,actor="uploader",action="award_boq_imported",object_id=src.id,details={"created":created,"skipped":skipped,"sha256":digest})); db.commit()
    return {"source_id":src.id,"sha256":digest,"created":created,"skipped":skipped,"rows_detected":len(mapped)}

@router.post("/projects/{project_id}/tasks")
def create_task(project_id:str,body:TaskCreate,db:Session=Depends(get_db)):
    if not db.get(Project,project_id): raise HTTPException(404,"project not found")
    due=datetime.fromisoformat(body.due_at) if body.due_at else None
    t=Task(id=new_id("TSK"),project_id=project_id,title=body.title,department=body.department,role=body.role,assignee=body.assignee,due_at=due); db.add(t); db.commit()
    return {"id":t.id,"status":t.status}

@router.get("/projects/{project_id}/tasks")
def list_tasks(project_id:str,department:str|None=Query(None),assignee:str|None=Query(None),status:str|None=Query(None),db:Session=Depends(get_db)):
    q=select(Task).where(Task.project_id==project_id)
    if department: q=q.where(Task.department==department)
    if assignee: q=q.where(Task.assignee==assignee)
    if status: q=q.where(Task.status==status)
    return [{"id":x.id,"title":x.title,"department":x.department,"role":x.role,"assignee":x.assignee,"status":x.status,"due_at":x.due_at,"acknowledged_at":x.acknowledged_at} for x in db.scalars(q).all()]

@router.post("/projects/{project_id}/tasks/{task_id}/ack")
def acknowledge_task(project_id:str,task_id:str,body:TaskAck,db:Session=Depends(get_db)):
    t=db.get(Task,task_id)
    if not t or t.project_id!=project_id: raise HTTPException(404,"task not found")
    t.acknowledged_at=datetime.now(timezone.utc); t.status="acknowledged"; db.add(AuditEvent(id=new_id("AUD"),project_id=project_id,actor=body.actor,action="task_acknowledged",object_id=task_id,details={})); db.commit()
    return {"id":task_id,"status":t.status,"acknowledged_at":t.acknowledged_at}

@router.post("/projects/{project_id}/evidence/upload")
def upload_evidence(project_id:str,evidence_type:str=Form(...),title:str=Form(...),department:str|None=Form(None),role:str|None=Form(None),assignee:str|None=Form(None),work_location:str|None=Form(None),object_id:str|None=Form(None),task_id:str|None=Form(None),capture_time:str|None=Form(None),source_channel:str=Form("web"),note:str|None=Form(None),file:UploadFile=File(...),db:Session=Depends(get_db)):
    if not db.get(Project,project_id): raise HTTPException(404,"project not found")
    tmp=STORAGE/f".tmp-{new_id('SRC')}-{file.filename or 'evidence.bin'}"
    with tmp.open("wb") as out: shutil.copyfileobj(file.file,out)
    digest=sha256_file(tmp); existing=db.scalar(select(Source).where(Source.project_id==project_id,Source.sha256==digest))
    if existing: src=existing; tmp.unlink(missing_ok=True)
    else:
        sid=new_id("SRC"); dest_dir=STORAGE/project_id/sid; dest_dir.mkdir(parents=True,exist_ok=True); dest=dest_dir/(file.filename or "evidence.bin"); tmp.replace(dest)
        src=Source(id=sid,project_id=project_id,title=title,source_type=evidence_type,file_path=str(dest),sha256=digest,immutable=True); db.add(src); db.flush()
    ev=Evidence(id=new_id("EV"),project_id=project_id,source_id=src.id,evidence_type=evidence_type,content=note,locator={"work_location":work_location,"object_id":object_id},status="candidate",created_by=assignee or "uploader"); db.add(ev); db.flush()
    ct=datetime.fromisoformat(capture_time) if capture_time else None
    db.add(EvidenceSubmission(id=new_id("ES"),project_id=project_id,evidence_id=ev.id,task_id=task_id,department=department,role=role,assignee=assignee,work_location=work_location,object_id=object_id,capture_time=ct,source_channel=source_channel,metadata_json={"filename":file.filename,"sha256":digest}))
    if task_id:
        t=db.get(Task,task_id)
        if t and t.project_id==project_id: t.status="submitted"
    db.add(AuditEvent(id=new_id("AUD"),project_id=project_id,actor=assignee or "uploader",action="evidence_uploaded",object_id=ev.id,details={"source_id":src.id,"sha256":digest,"task_id":task_id})); db.commit()
    return {"id":ev.id,"source_id":src.id,"sha256":digest,"immutable_source":True,"status":ev.status}

@router.get("/projects/{project_id}/evidence")
def list_evidence(project_id:str,assignee:str|None=Query(None),db:Session=Depends(get_db)):
    rows=db.scalars(select(EvidenceSubmission).where(EvidenceSubmission.project_id==project_id)).all(); out=[]
    for s in rows:
        if assignee and s.assignee!=assignee: continue
        ev=db.get(Evidence,s.evidence_id); src=db.get(Source,ev.source_id) if ev and ev.source_id else None
        out.append({"id":ev.id,"type":ev.evidence_type,"status":ev.status,"assignee":s.assignee,"sha256":src.sha256 if src else None})
    return out

@router.get("/projects/{project_id}/workflow")
def get_workflow(project_id:str,db:Session=Depends(get_db)):
    if not db.get(Project,project_id): raise HTTPException(404,"project not found")
    return workflow_view(db,project_id)

@router.post("/projects/{project_id}/workflow/{stage_key}")
def update_workflow(project_id:str,stage_key:str,body:StageUpdate,db:Session=Depends(get_db)):
    row=set_stage(db,project_id,stage_key,**body.model_dump()); db.commit(); return {"stage_key":stage_key,"status":row.status}

@router.get("/projects/{project_id}/audit-events")
def audit_events(project_id:str,limit:int=Query(50,ge=1,le=200),db:Session=Depends(get_db)):
    rows=db.scalars(select(AuditEvent).where(AuditEvent.project_id==project_id).order_by(AuditEvent.created_at.desc()).limit(limit)).all()
    return [{"id":x.id,"actor":x.actor,"action":x.action,"object_id":x.object_id,"details":x.details,"created_at":x.created_at} for x in rows]

@router.get("/projects/{project_id}/workspace")
def workspace(project_id:str,role:str=Query("cost_engineer"),db:Session=Depends(get_db)):
    p=db.get(Project,project_id)
    if not p: raise HTTPException(404,"project not found")
    sources=db.scalars(select(Source).where(Source.project_id==project_id)).all(); boqs=db.scalars(select(BOQItem).where(BOQItem.project_id==project_id)).all(); measurements=db.scalars(select(Measurement).where(Measurement.project_id==project_id)).all(); evidence=db.scalars(select(Evidence).where(Evidence.project_id==project_id)).all(); tasks=db.scalars(select(Task).where(Task.project_id==project_id)).all(); issues=db.scalars(select(ReviewIssue).where(ReviewIssue.project_id==project_id)).all()
    baseline_ids={m.object_id for m in measurements if m.measurement_type=="baseline_drawing"}; stages=workflow_view(db,project_id); access=can_view_commercial(role)
    return {"project":{"id":p.id,"name":p.name,"region":p.region,"status":p.status},"stages":stages,"baseline":{"ready":len(baseline_ids),"total_boq":len(boqs),"missing":max(0,len(boqs)-len(baseline_ids))},"counts":{"sources":len(sources),"boq":len(boqs),"measurements":len(measurements),"open_issues":sum(1 for x in issues if x.status!="resolved"),"open_tasks":sum(1 for x in tasks if x.status!="closed")},"evidence":{"total":len(evidence),"candidate":sum(1 for x in evidence if x.status in {"candidate","unknown"}),"verified":sum(1 for x in evidence if x.status in {"verified","closed"})},"commercial_allowed":access.allowed,"commercial_reason":access.reason}

@router.get("/projects/{project_id}/boq-workspace")
def boq_workspace(project_id:str,db:Session=Depends(get_db)):
    if not db.get(Project,project_id): raise HTTPException(404,"project not found")
    boqs=db.scalars(select(BOQItem).where(BOQItem.project_id==project_id)).all(); measurements=db.scalars(select(Measurement).where(Measurement.project_id==project_id,Measurement.measurement_type=="baseline_drawing")).all(); latest={}
    for m in measurements:
        prior=latest.get(m.object_id)
        if prior is None or m.created_at>=prior.created_at: latest[m.object_id]=m
    rows=[]; diff_count=0; amount_total=0.0
    for b in boqs:
        m=latest.get(b.id); diff=None if not m or b.award_quantity is None else m.quantity-b.award_quantity
        if diff is not None and abs(diff)>1e-9: diff_count+=1
        if b.award_quantity is not None and b.award_unit_price is not None: amount_total+=b.award_quantity*b.award_unit_price
        rows.append({"id":b.id,"code":b.code,"name":b.name,"unit":b.unit,"award_quantity":b.award_quantity,"award_unit_price":b.award_unit_price,"baseline_quantity":None if not m else m.quantity,"baseline_measurement_id":None if not m else m.id,"quantity_difference":diff})
    return {"summary":{"total":len(boqs),"baseline_ready":len(latest),"baseline_missing":max(0,len(boqs)-len(latest)),"quantity_difference_count":diff_count,"award_amount_total":amount_total},"rows":rows}

@router.get("/projects/{project_id}/changes")
def list_changes(project_id:str,db:Session=Depends(get_db)):
    xs=db.scalars(select(ChangeEvent).where(ChangeEvent.project_id==project_id).order_by(ChangeEvent.created_at.desc())).all()
    return [{"id":x.id,"event_type":x.event_type,"title":x.title,"status":x.status,"major":x.major} for x in xs]

@router.get("/projects/{project_id}/rules")
def list_rules(project_id:str,db:Session=Depends(get_db)):
    p=db.get(Project,project_id)
    if not p: raise HTTPException(404,"project not found")
    xs=db.scalars(select(Rule)).all(); return [{"id":x.id,"title":x.title,"rule_type":x.rule_type,"source_id":x.source_id,"region":x.region,"scope":x.scope,"classification":x.classification} for x in xs if not (x.region and p.region and x.region!=p.region)]
