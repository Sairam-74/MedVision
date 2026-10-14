"""Deterministic policy/failure tests; no training-results claim."""
import asyncio,json,os,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from workflow_store import now,WorkflowStore
checks=[]
def check(v,label):
    if not v:raise AssertionError(label)
    checks.append(label)
with tempfile.TemporaryDirectory(prefix='medvision-job-policy-') as t:
    folder=Path(t);os.environ['MEDVISION_DB']=str(folder/'db.sqlite3');os.environ['MEDVISION_GENERATED_DIR']=str(folder/'storage');os.environ['MEDVISION_FEEDBACK_THRESHOLD']='1';os.environ.pop('MEDVISION_BUNDLE',None)
    import backend_service as b
    from fastapi.testclient import TestClient
    import cv2,numpy as np
    from medvision_pipeline import FracDataset,PreprocessConfig
    user={'id':'policy-admin','name':'Synthetic Policy Reviewer','email':'policy.admin@example.invalid','role':'admin','status':'active','organization':'Policy tests'};b.store.seed_user(user,'synthetic-policy-password')
    # Simulated subprocess launch failure tests automatic scheduling/error state;
    # real training is exercised separately by verify_retraining.py.
    original_exec=asyncio.create_subprocess_exec
    async def failed_launch(*args,**kwargs):raise OSError('Synthetic worker launch failure')
    asyncio.create_subprocess_exec=failed_launch
    try:
        with TestClient(b.app) as client:
            client.post('/auth/login',json={'identifier':user['email'],'password':'synthetic-policy-password'})
            ds=FracDataset(ROOT/'FracAtlas.zip',ROOT/'experiments/data_v2/manifest.json','train',PreprocessConfig());i=next(i for i,r in enumerate(ds.rows) if int(r['fractured'])==0);image,mask=ds.native(i)
            aid='policy-analysis';path=b.UPLOAD_DIR/(aid+'-xray.png');cv2.imwrite(str(path),image)
            case={'id':aid,'createdAt':now(),'status':'completed','imagePath':str(path),'overlayPath':str(b.OVERLAY_DIR/(aid+'-segmented.png'))};b.store.save_case(case,user['id'],{'analysisId':aid,'modelVersion':'fracture_model_v1','maskPngBase64':None})
            fb=client.post('/analyses/'+aid+'/feedback',json={'correct':False,'category':'False positive'}).json();ok,raw=cv2.imencode('.png',mask*255)
            client.post('/feedback/'+fb['id']+'/mask',files={'mask':('mask.png',raw.tobytes(),'image/png')})
            response=client.post('/feedback/'+fb['id']+'/confirm',json={'fracture_present':False,'training_consent':True,'training_partition_verified':True});check(response.status_code==200 and response.json()['training_eligible'],'only known training-cohort correction eligible')
            for _ in range(50):
                jobs=client.get('/retraining/jobs').json()
                if jobs and jobs[0]['status']=='failed':break
                time.sleep(.02)
            check(len(jobs)==1,'confirmed feedback crossing threshold automatically creates one job')
            check(jobs[0]['status']=='failed','worker launch failure persists honest failed status')
            job_id=jobs[0]['id'];check(client.post('/retraining/jobs/'+job_id+'/retry').status_code==200,'authorized failed job retry queued safely')
            time.sleep(.1);check(client.get('/retraining/jobs/'+job_id).json()['status']=='failed','retry failure preserves explicit failed status')
            check(client.get('/health').status_code==200,'worker launch failures leave service available')
            with b.store.connect() as db:db.execute("INSERT INTO retraining_jobs(id,status,actor_id,config,feedback_ids,created_at,worker_pid) VALUES('synthetic-interrupted','training',?,'{}','[]',?,NULL)",(user['id'],now()))
            WorkflowStore(b.store)
            with b.store.connect() as db:row=db.execute("SELECT * FROM retraining_jobs WHERE id='synthetic-interrupted'").fetchone()
            check(row['status']=='interrupted' and bool(row['completed_at']),'restart marks missing worker interrupted without losing its job record')
    finally:asyncio.create_subprocess_exec=original_exec
out=ROOT/'test-results';out.mkdir(exist_ok=True);report={'mode':'deterministic scheduling and failure fixtures','checks_passed':len(checks),'checks':checks,'training_executed':False};(out/'job-policy.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
