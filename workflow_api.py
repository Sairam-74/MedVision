"""Owned workflow APIs; reuse existing sessions, inference and SQLite case records."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from datetime import date
import cv2
import numpy as np
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict, field_validator
from workflow_store import WorkflowStore, now, uid


class Input(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)

class PatientSearchInput(Input):
    q:str=Field(default='',max_length=120)
    limit:int=Field(default=25,ge=1,le=100)
    offset:int=Field(default=0,ge=0)

class StudySearchInput(PatientSearchInput):
    patient_id:str=Field(default='',max_length=80)
    examination_date:str=Field(default='',max_length=10)
    body_part:str=Field(default='',max_length=80)
    laterality:str=Field(default='',max_length=40)
    status:str=Field(default='',max_length=40)

class PatientInput(Input):
    name:str=Field(min_length=1,max_length=120)
    identifier:str=Field(default='',max_length=80)
    age:int|None=Field(default=None,ge=0,le=130)
    gender:str=Field(default='Not specified',max_length=40)

class StudyInput(Input):
    patient_id:str=Field(min_length=1,max_length=80)
    examination_date:date
    body_part:str=Field(min_length=1,max_length=80)
    laterality:str=Field(default='Not applicable',pattern='^(Left|Right|Bilateral|Not applicable)$')
    clinical_history:str=Field(default='',max_length=4000)
    referring_physician:str=Field(default='',max_length=120)

class ReportInput(Input):
    revision:int=Field(ge=1)
    findings:str=Field(min_length=1,max_length=16000)
    impression:str=Field(min_length=1,max_length=8000)
    ai_decision:str=Field(pattern='^(pending|accepted|rejected|corrected)$')
    corrections:dict[str,str]=Field(default_factory=dict,max_length=12)
    @field_validator('corrections')
    @classmethod
    def bounded(cls,value):
        if any(len(k)>80 or len(v)>1000 for k,v in value.items()):raise ValueError('Correction too long')
        return value

CATEGORIES={'False positive','False negative','Wrong localization','Wrong bone','Wrong fracture type','Wrong displacement','Incorrect segmentation','Misleading confidence','Other'}
class FeedbackInput(Input):
    correct:bool
    category:str=Field(default='',max_length=80)
    comments:str=Field(default='',max_length=4000)
    corrected_findings:dict[str,str]=Field(default_factory=dict,max_length=12)
    @field_validator('corrected_findings')
    @classmethod
    def bounded(cls,value):return ReportInput.bounded(value)

class ConfirmInput(Input):
    fracture_present:bool
    training_consent:bool=False
    training_partition_verified:bool=False

class JobInput(Input):
    epochs:int=Field(default=2,ge=1,le=20)
    smoke:bool=False


def install(app,store,backend):
    workflow=WorkflowStore(store)
    root=backend['BASE_DIR']; generated=backend['GENERATED_DIR']
    corrections=generated/'corrections';corrections.mkdir(exist_ok=True)
    tasks={}
    def owner(request):return request.state.user['id']
    def reviewer(request):
        if request.state.user['role'] not in ('clinician','admin'):raise HTTPException(403,'Authorized clinician or administrator required')
        return owner(request)
    def admin(request):
        if request.state.user['role']!='admin':raise HTTPException(403,'Administrator required for model management')
        return owner(request)
    def require_study(request,study_id):
        item=workflow.study(owner(request),study_id)
        if not item:raise HTTPException(404,'Study not found')
        return item
    def current():
        with store.connect() as db:
            row=db.execute("SELECT id FROM model_versions WHERE status='production'").fetchone()
            return row[0] if row else 'unavailable'
    with store.connect() as db:
        if not db.execute('SELECT 1 FROM model_versions').fetchone():
            path=backend['CHECKPOINT_PATH']; bundle=backend['BUNDLE_PATH']
            document=json.loads(Path(bundle).read_text()) if bundle else {}
            digest=document.get('checkpoint_sha256') or (hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else 'unavailable')
            db.execute('INSERT INTO model_versions(id,status,bundle_path,checkpoint_sha,dataset_version,training_config,created_at) VALUES(?,?,?,?,?,?,?)',('fracture_model_v1','production',str(Path(bundle).resolve()) if bundle else None,digest,document.get('manifest_sha256'),json.dumps(document),now()))
        production=db.execute("SELECT bundle_path FROM model_versions WHERE status='production'").fetchone()
        if production and production[0]:
            path=Path(production[0]).resolve()
            if root not in path.parents:raise RuntimeError('Production bundle must be isolated inside this clone')
            backend['BUNDLE_PATH']=str(path)

    @app.exception_handler(sqlite3.Error)
    async def database_error(request,exc):
        return JSONResponse({'detail':'Database operation failed; retry or inspect local service diagnostics'},status_code=503)

    @app.get('/patients/search')
    async def patient_search(request:Request,q:str='',limit:int=25,offset:int=0):
        if len(q)>120 or not 1<=limit<=100 or offset<0:raise HTTPException(422,'Invalid search parameters')
        return workflow.patients(owner(request),q,offset,limit)

    @app.post('/patients/search')
    async def patient_search_private(data:PatientSearchInput,request:Request):
        return await patient_search(request,**data.model_dump())

    @app.post('/patients',status_code=201)
    async def patient_create(data:PatientInput,request:Request):
        try:return workflow.create_patient(owner(request),data.model_dump())
        except ValueError as e:raise HTTPException(409,str(e)) from e

    @app.post('/studies',status_code=201)
    async def study_create(data:StudyInput,request:Request):
        try:return workflow.create_study(owner(request),data.model_dump(mode='json'))
        except LookupError as e:raise HTTPException(404,str(e)) from e

    @app.get('/studies')
    async def study_search(request:Request,q:str='',patient_id:str='',examination_date:str='',body_part:str='',laterality:str='',status:str='',limit:int=25,offset:int=0):
        if any(len(x)>120 for x in (q,patient_id,examination_date,body_part,laterality,status)) or not 1<=limit<=100 or offset<0:raise HTTPException(422,'Invalid search parameters')
        if examination_date:
            try:date.fromisoformat(examination_date)
            except ValueError as e:raise HTTPException(422,'Invalid examination date') from e
        if status and status not in {'draft','final','queued','processing','completed','failed','timed_out'}:raise HTTPException(422,'Invalid status')
        return workflow.search(owner(request),q,patient_id,examination_date,body_part,laterality,status,limit,offset)

    @app.post('/studies/search')
    async def study_search_private(data:StudySearchInput,request:Request):
        return await study_search(request,**data.model_dump())

    @app.get('/patients/{patient_id}/history')
    async def patient_history(patient_id:str,request:Request,limit:int=25,offset:int=0):
        if not workflow.patient(owner(request),patient_id):raise HTTPException(404,'Patient not found')
        if not 1<=limit<=100 or offset<0:raise HTTPException(422,'Invalid pagination')
        return workflow.search(owner(request),patient_id=patient_id,limit=limit,offset=offset)

    @app.get('/studies/{study_id}')
    async def study_get(study_id:str,request:Request):
        item=require_study(request,study_id)
        for image in item['images']:
            case,result,error=backend['_owned'](request,image['analysis_id'])
            image.update(analysis=backend['_public_analysis'](case),result=result,error=error)
        item['report']=workflow.report(owner(request),study_id)
        return item

    @app.get('/studies/{study_id}/report')
    async def report_get(study_id:str,request:Request):
        require_study(request,study_id)
        return workflow.report(owner(request),study_id)

    @app.post('/studies/{study_id}/report/generate')
    async def report_generate(study_id:str,request:Request):
        reviewer(request);require_study(request,study_id)
        study=require_study(request,study_id)
        if not study['images'] or any(store.get_case(i['analysis_id'],owner(request))[0]['status']!='completed' for i in study['images']):raise HTTPException(409,'Complete all image analyses before generating the report')
        try:return workflow.report(owner(request),study_id,True)
        except ValueError as e:raise HTTPException(409,str(e)) from e

    @app.post('/studies/{study_id}/report/{action}')
    async def report_save(study_id:str,action:str,data:ReportInput,request:Request):
        reviewer(request)
        if action not in ('save','finalize','reopen'):raise HTTPException(404,'Unknown report operation')
        try:return workflow.save_report(owner(request),study_id,data.model_dump(),action)
        except LookupError as e:raise HTTPException(404,str(e)) from e
        except ValueError as e:raise HTTPException(409,str(e)) from e

    @app.get('/analyses/{analysis_id}/feedback')
    async def feedback_get(analysis_id:str,request:Request):
        backend['_owned'](request,analysis_id)
        return [{k:v for k,v in r.items() if k!='corrected_mask_path'}|{'has_corrected_mask':bool(r['corrected_mask_path']),'training_eligible':bool(json.loads(r['corrected_findings']).get('training_eligible'))} for r in workflow.feedback_list(owner(request),analysis_id)]

    @app.post('/analyses/{analysis_id}/feedback',status_code=201)
    async def feedback_create(analysis_id:str,data:FeedbackInput,request:Request):
        reviewer(request);case,result,error=backend['_owned'](request,analysis_id)
        if not result:raise HTTPException(409,'Only completed analysis can be reviewed')
        if not data.correct and data.category not in CATEGORIES:raise HTTPException(422,'Select a supported error category')
        if data.correct and data.category:raise HTTPException(422,'Correct result must not have an error category')
        record=workflow.feedback(owner(request),analysis_id,data.model_dump(),result.get('modelVersion',result.get('modelSha256','unknown')))
        return {k:v for k,v in record.items() if k!='corrected_mask_path'}

    def get_feedback(request,feedback_id):
        with store.connect() as db:
            row=db.execute('SELECT * FROM feedback WHERE id=? AND owner_id=?',(feedback_id,owner(request))).fetchone()
        if not row:raise HTTPException(404,'Feedback not found')
        return dict(row)

    @app.post('/feedback/{feedback_id}/mask')
    async def correction_upload(feedback_id:str,request:Request):
        reviewer(request);feedback=get_feedback(request,feedback_id)
        if feedback['confirmed']:raise HTTPException(409,'Confirmed annotation is immutable; submit another review')
        body=await backend['_bounded_body'](request,backend['MAX_REQUEST_BYTES'])
        from starlette.formparsers import MultiPartParser
        async def stream():yield body
        form=await MultiPartParser(request.headers,stream(),max_files=1,max_fields=0).parse()
        try:
            upload=form.get('mask')
            if not upload or not hasattr(upload,'read'):raise HTTPException(422,'PNG mask required')
            raw=await upload.read()
            if len(raw)>backend['MAX_UPLOAD_BYTES'] or not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise HTTPException(422,'Valid PNG mask required')
            backend['_decode_image'](raw)
            mask=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_GRAYSCALE)
            case,_,_=backend['_owned'](request,feedback['analysis_id'])
            image=cv2.imread(case['imagePath'],cv2.IMREAD_GRAYSCALE)
            if mask is None or image is None or mask.shape!=image.shape or not set(np.unique(mask)).issubset({0,255}):raise HTTPException(422,'Binary mask must match original image dimensions, with pixels 0 or 255')
            path=corrections/(feedback_id+'.png'); path.write_bytes(raw)
            with store.connect() as db:db.execute('UPDATE feedback SET corrected_mask_path=? WHERE id=?',(str(path),feedback_id))
        finally:await form.close()
        return {'stored':True,'confirmed':False}

    @app.post('/feedback/{feedback_id}/confirm')
    async def correction_confirm(feedback_id:str,data:ConfirmInput,request:Request):
        reviewer(request);feedback=get_feedback(request,feedback_id)
        if feedback['confirmed']:return {'confirmed':True,'id':feedback_id}
        case,result,_=backend['_owned'](request,feedback['analysis_id'])
        image=cv2.imread(case['imagePath'],cv2.IMREAD_GRAYSCALE)
        path=Path(feedback['corrected_mask_path']) if feedback['corrected_mask_path'] else None
        if not path:
            if not feedback['correct']:raise HTTPException(422,'Incorrect segmentation requires a corrected binary mask (including all-zero masks for negatives)')
            mask=backend['_mask_from_prediction']({'mask_png_base64':result.get('maskPngBase64')})
            if mask is None or mask.shape!=image.shape:raise HTTPException(422,'Native-size reviewed mask required')
            path=corrections/(feedback_id+'.png');cv2.imwrite(str(path),mask*255)
        mask=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
        if mask is None or mask.shape!=image.shape or bool(mask.any())!=data.fracture_present:raise HTTPException(422,'Confirmed label must agree with corrected mask')
        corrected=json.loads(feedback['corrected_findings']);corrected['fracture_present']=data.fracture_present;corrected['training_consent']=data.training_consent;corrected['training_partition_verified']=data.training_partition_verified
        digest=hashlib.sha256(str(image.shape).encode()+image.tobytes()).hexdigest()
        manifest_path=root/'experiments/data_v2/manifest.json'
        manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.is_file() else {'rows':[]}
        train_hashes={r['decoded_sha256'] for r in manifest['rows'] if r['split']=='train'}
        corrected['training_image_sha256']=digest
        corrected['training_eligible']=data.training_consent and data.training_partition_verified and digest in train_hashes
        with store.connect() as db:
            db.execute('UPDATE feedback SET confirmed=1,confirmed_at=?,corrected_mask_path=?,corrected_findings=? WHERE id=?',(now(),str(path),json.dumps(corrected),feedback_id))
        maybe_queue(request,automatic=True)
        return {'confirmed':True,'id':feedback_id,'training_eligible':corrected['training_eligible']}

    def models():
        with store.connect() as db:return [dict(r) for r in db.execute('SELECT * FROM model_versions ORDER BY created_at DESC')]
    @app.get('/models/current')
    async def model_current(request:Request):
        rows=models();row=next((r for r in rows if r['status']=='production'),None)
        if row:row={k:v for k,v in row.items() if k!='bundle_path'}
        with store.connect() as db:
            count=db.execute('SELECT count(*) FROM feedback').fetchone()[0] if request.state.user['role']=='admin' else db.execute('SELECT count(*) FROM feedback WHERE owner_id=?',(owner(request),)).fetchone()[0]
        return {'model':row,'feedback_count':count,'threshold':int(os.environ.get('MEDVISION_FEEDBACK_THRESHOLD','10')),'metrics':json.loads(row['metrics']) if row and row['metrics'] else None,'limitations':['Segmentation-only model; clinical subtype and calibrated case confidence unavailable.']}
    @app.get('/models/history')
    async def model_history(request:Request):return [{k:v for k,v in r.items() if k!='bundle_path'} for r in models()]

    async def run_process(job_id):
        with store.connect() as db:db.execute("UPDATE retraining_jobs SET status='training',started_at=? WHERE id=?",(now(),job_id))
        log=generated/'training_logs';log.mkdir(exist_ok=True)
        with (log/(job_id+'.log')).open('wb') as out:
            proc=await asyncio.create_subprocess_exec(sys.executable,str(root/'tools/retrain_worker.py'),'--job',job_id,'--db',str(store.path),'--root',str(root),cwd=str(root),stdout=out,stderr=out)
            with store.connect() as db:db.execute('UPDATE retraining_jobs SET worker_pid=? WHERE id=?',(proc.pid,job_id))
            code=await proc.wait()
        if code:
            with store.connect() as db:db.execute("UPDATE retraining_jobs SET status='failed',error='Training worker failed; inspect local job log',completed_at=? WHERE id=?",(now(),job_id))
    async def run(job_id):
        try:await run_process(job_id)
        except Exception:
            backend['logger'].exception('Training worker launch/monitor failed for %s',job_id)
            with store.connect() as db:db.execute("UPDATE retraining_jobs SET status='failed',error='Worker launch or monitoring failed; inspect local job log',completed_at=? WHERE id=?",(now(),job_id))
    def maybe_queue(request,data=None,automatic=False):
        actor=owner(request)
        if not automatic:admin(request)
        threshold=int(os.environ.get('MEDVISION_FEEDBACK_THRESHOLD','10'))
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM retraining_jobs WHERE status IN ('queued','training','evaluating')").fetchone():
                if automatic:return None
                raise HTTPException(409,'A retraining job is already active')
            used=set()
            for row in db.execute("SELECT feedback_ids FROM retraining_jobs WHERE status IN ('queued','training','evaluating','candidate_ready','promoted')"):
                used.update(json.loads(row[0]))
            rows=[dict(r) for r in db.execute('SELECT * FROM feedback WHERE owner_id=? AND confirmed=1 ORDER BY confirmed_at',(actor,)) if r['id'] not in used]
            # Train at most one confirmed annotation per image; latest review wins.
            eligible=[r for r in rows if json.loads(r['corrected_findings']).get('training_eligible')]
            rows=list({json.loads(r['corrected_findings'])['training_image_sha256']:r for r in eligible}.values())
            if len(rows)<threshold:
                if automatic:return None
                raise HTTPException(409,f'Need {threshold} distinct confirmed train-only image annotations; have {len(rows)}')
            job_id=uid('train');cfg=data.model_dump() if data else {'epochs':2,'smoke':False}
            db.execute('INSERT INTO retraining_jobs(id,status,actor_id,config,feedback_ids,created_at) VALUES(?,?,?,?,?,?)',(job_id,'queued',actor,json.dumps(cfg),json.dumps([r['id'] for r in rows]),now()))
        task=asyncio.create_task(run(job_id));tasks[job_id]=task;task.add_done_callback(lambda _:tasks.pop(job_id,None))
        return {'id':job_id,'status':'queued'}
    @app.post('/retraining/jobs',status_code=201)
    async def job_create(data:JobInput,request:Request):return maybe_queue(request,data)
    @app.get('/retraining/jobs')
    async def job_list(request:Request):
        reviewer(request)
        with store.connect() as db:
            rows=db.execute('SELECT * FROM retraining_jobs ORDER BY created_at DESC LIMIT 100').fetchall() if request.state.user['role']=='admin' else db.execute('SELECT * FROM retraining_jobs WHERE actor_id=? ORDER BY created_at DESC LIMIT 100',(owner(request),)).fetchall()
            return [dict(r) for r in rows]
    @app.get('/retraining/jobs/{job_id}')
    async def job_get(job_id:str,request:Request):
        reviewer(request)
        with store.connect() as db:row=db.execute('SELECT * FROM retraining_jobs WHERE id=?',(job_id,)).fetchone()
        if not row or (row['actor_id']!=owner(request) and request.state.user['role']!='admin'):raise HTTPException(404,'Job not found')
        return dict(row)
    @app.post('/retraining/jobs/{job_id}/retry')
    async def job_retry(job_id:str,request:Request):
        admin(request);row=await job_get(job_id,request)
        if row['status'] not in ('failed','interrupted','blocked'):raise HTTPException(409,'Only failed/interrupted/blocked jobs can be retried')
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM retraining_jobs WHERE status IN ('queued','training','evaluating')").fetchone():raise HTTPException(409,'A job is already running')
            db.execute("UPDATE retraining_jobs SET status='queued',error=NULL,completed_at=NULL WHERE id=?",(job_id,))
        task=asyncio.create_task(run(job_id));tasks[job_id]=task;task.add_done_callback(lambda _:tasks.pop(job_id,None))
        return {'id':job_id,'status':'queued'}

    @app.post('/models/{model_id}/{action}')
    async def model_change(model_id:str,action:str,request:Request):
        actor=admin(request)
        if action not in ('promote','rollback'):raise HTTPException(404,'Unknown model operation')
        if backend['inference_lock'].locked() or backend['jobs']:raise HTTPException(409,'Wait for active inference to finish')
        async with backend['inference_lock']:
            with store.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT * FROM model_versions WHERE id=?',(model_id,)).fetchone()
                if not row:raise HTTPException(404,'Model not found')
                if action=='promote':
                    metrics=json.loads(row['metrics'] or '{}')
                    if row['status']!='candidate_ready' or not metrics.get('acceptance',{}).get('passed'):raise HTTPException(409,'Candidate has not passed all validation gates')
                    if metrics.get('evaluated_production_version')!=current():raise HTTPException(409,'Production baseline changed; reevaluate candidate')
                    if not row['bundle_path'] or hashlib.sha256(Path(row['bundle_path']).read_bytes()).hexdigest()!=metrics.get('bundle_sha256'):raise HTTPException(409,'Candidate bundle changed after validation')
                elif row['status']!='previous':raise HTTPException(409,'Only retained previous models support rollback')
                bundle=row['bundle_path']
                if bundle:backend['ready_bundle'](bundle)
                elif row['checkpoint_sha']!=hashlib.sha256(backend['CHECKPOINT_PATH'].read_bytes()).hexdigest():raise HTTPException(409,'Legacy checkpoint changed')
                previous=current()
                db.execute("UPDATE model_versions SET status='previous' WHERE status='production'")
                db.execute("UPDATE model_versions SET status='production',promoted_at=?,previous_version=? WHERE id=?",(now(),previous,model_id))
                db.execute('INSERT INTO model_events VALUES(?,?,?,?,?)',(uid('event'),action,model_id,actor,now()))
                db.execute("UPDATE retraining_jobs SET status='promoted' WHERE candidate_id=?",(model_id,))
            backend['BUNDLE_PATH']=bundle
        return {'production_version':model_id,'previous_version':previous,'timestamp':now()}
    return workflow,current
