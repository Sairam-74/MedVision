"""Real one-epoch retraining smoke; never eligible for production promotion."""
import base64,io,json,os,sys,time,zipfile,hashlib
from pathlib import Path
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
folder=ROOT/'.feature_data'/'retraining-smoke';folder.mkdir(parents=True,exist_ok=True)
# Use a fresh isolated database each run, preserving prior evidence.
from workflow_store import uid
run=folder/uid('run');run.mkdir();os.environ['MEDVISION_DB']=str(run/'app.sqlite3');os.environ['MEDVISION_GENERATED_DIR']=str(run/'storage');os.environ['MEDVISION_FEEDBACK_THRESHOLD']='2';os.environ['OMP_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2';os.environ.pop('MEDVISION_BUNDLE',None)
import backend_service as b
from fastapi.testclient import TestClient
from medvision_pipeline import FracDataset,PreprocessConfig,sha
from tools.retrain_worker import acceptance
checks=[]
def check(value,label):
    if not value:raise AssertionError(label)
    checks.append(label)
user={'id':'smoke-admin','name':'Synthetic Training Reviewer','email':'smoke.admin@example.invalid','role':'admin','status':'active','organization':'Synthetic smoke'}
b.store.seed_user(user,'synthetic-training-password')
# The orchestration upload fixture returns a deterministic mask; the candidate
# trainer and evaluation below run the real Attention U-Net and real dataset.
def fixture(path,checkpoint):
    im=cv2.imread(path,0);ok,mask=cv2.imencode('.png',np.zeros_like(im));return {'mask_png_base64':base64.b64encode(mask).decode(),'mask_shape':list(im.shape),'mask_present':False,'model_sha256':sha(ROOT/'best_model.pt')}
real_predict=b._predict_selected
b._predict_selected=fixture
ds=FracDataset(ROOT/'FracAtlas.zip',ROOT/'experiments/data_v2/manifest.json','train',PreprocessConfig())
selected=[next(i for i,r in enumerate(ds.rows) if int(r['fractured'])==label) for label in (1,0)]
original_sha=sha(ROOT/'best_model.pt')
with TestClient(b.app) as client:
    client.post('/auth/login',json={'identifier':user['email'],'password':'synthetic-training-password'})
    p=client.post('/patients',json={'name':'Synthetic Training Cohort'}).json();study=client.post('/studies',json={'patient_id':p['id'],'examination_date':'2026-10-14','body_part':'Research cohort'}).json()
    feedback_ids=[]
    for i in selected:
        image,mask=ds.native(i);row=ds.rows[i];ok,image_png=cv2.imencode('.png',image);ok,mask_png=cv2.imencode('.png',mask*255)
        response=client.post('/studies/'+study['id']+'/images',data={'view_type':'AP'},files={'image':('deidentified-train.png',image_png.tobytes(),'image/png')});check(response.status_code==200,'train-cohort image upload')
        aid=response.json()['analysisId']
        for _ in range(100):
            status=client.get('/analyses/'+aid+'/status').json()['status']
            if status not in ('queued','processing'):break
            time.sleep(.1)
        check(status=='completed','orchestration fixture completed')
        feedback=client.post('/analyses/'+aid+'/feedback',json={'correct':False,'category':'Incorrect segmentation','comments':'Synthetic smoke annotation from authorized train-only research cohort'}).json();feedback_ids.append(feedback['id'])
        check(client.post('/feedback/'+feedback['id']+'/mask',files={'mask':('mask.png',mask_png.tobytes(),'image/png')}).status_code==200,'real train annotation mask accepted')
        # Temporarily keep automatic threshold above the count; manually create a smoke-only job.
        os.environ['MEDVISION_FEEDBACK_THRESHOLD']='99'
        check(client.post('/feedback/'+feedback['id']+'/confirm',json={'fracture_present':bool(int(row['fractured'])),'training_consent':True,'training_partition_verified':True}).status_code==200,'real train annotation confirmed')
    os.environ['MEDVISION_FEEDBACK_THRESHOLD']='2'
    created=client.post('/retraining/jobs',json={'epochs':1,'smoke':True});check(created.status_code==201,'threshold creates real background smoke job');job_id=created.json()['id']
    check(client.post('/retraining/jobs',json={'epochs':1,'smoke':True}).status_code==409,'duplicate active retraining prevented')
    t=time.perf_counter();check(client.get('/health').status_code==200 and time.perf_counter()-t<3,'ordinary health request responsive during background training')
    b._predict_selected=real_predict
    ok,concurrent_image=cv2.imencode('.png',np.tile(np.arange(80,dtype=np.uint8),(64,1)))
    concurrent_upload=client.post('/analyses',files={'image':('synthetic-concurrent.png',concurrent_image.tobytes(),'image/png')})
    check(concurrent_upload.status_code==200,'ordinary upload accepted while real candidate trains')
    concurrent_id=concurrent_upload.json()['analysisId']
    for _ in range(300):
        concurrent_status=client.get('/analyses/'+concurrent_id+'/status').json()['status']
        if concurrent_status not in ('queued','processing'):break
        time.sleep(.1)
    check(concurrent_status=='completed','real production inference succeeds alongside real candidate training')
    check(client.get('/retraining/jobs/'+job_id).json()['status'] in ('training','evaluating'),'candidate still active during completed production inference')
    for _ in range(600):
        job=client.get('/retraining/jobs/'+job_id).json()
        if job['status'] not in ('queued','training','evaluating'):break
        time.sleep(.5)
    check(job['status']=='rejected','real candidate evaluated and rejected by smoke/promotion gates: '+str(job.get('error')))
    model=next(r for r in client.get('/models/history').json() if r['id']==job['candidate_id']);metrics=json.loads(model['metrics'])
    check(metrics['validation_size']==4 and metrics['smoke'],'real smoke evaluation explicitly labeled four-image smoke')
    check(not metrics['acceptance']['passed'] and not metrics['reserved_test_evaluated'],'smoke never promoted and reserved test never used')
    check(client.post('/models/'+job['candidate_id']+'/promote').status_code==409,'rejected candidate promotion denied')
    check(sha(ROOT/'best_model.pt')==original_sha,'production checkpoint unchanged by training')
    check(client.get('/models/current').json()['model']['id']=='fracture_model_v1','production version unchanged')
    check(bool(job['started_at']) and bool(job['completed_at']),'server training timestamps persisted')
    # Gate logic covers successful fixtures and individual failures, without
    # calling these fixtures measured model performance or promoting a model.
    good={'n_positive':83,'n_normal':380,'case_true_positive':80,'case_true_negative':350,'case_false_negative':3,'case_false_positive':30,'mean_positive_dice':.6,'mean_positive_iou':.5,'localized_positive':80}
    old={**good,'case_false_negative':4,'case_false_positive':35,'mean_positive_dice':.5,'mean_positive_iou':.4,'localized_positive':79}
    check(acceptance(good,old,True,True,False)['passed'],'all-gate success fixture accepted by gate function only')
    check(not acceptance(good,old,True,False,False)['passed'],'unverified patient independence blocks promotion')
    check(not acceptance({**good,'mean_positive_iou':.3},old,True,True,False)['passed'],'accuracy alone cannot pass promotion')
report={'checks_passed':len(checks),'checks':checks,'job_id':job_id,'candidate_status':job['status'],'real_smoke_metrics':metrics,'production_promoted':False,'full_validation_executed':False,'training_data':'two verified train-cohort corrections plus existing train samples; four-image validation smoke only'}
(ROOT/'test-results'/'retraining-smoke.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
