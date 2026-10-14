"""Executed integration evidence, with real inference separated from deterministic checks."""
import argparse,base64,concurrent.futures,hashlib,io,json,os,sys,tempfile,time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--real',action='store_true');a=ap.parse_args();checks=[]
    def check(value,label):
        if not value:raise AssertionError(label)
        checks.append(label)
    with tempfile.TemporaryDirectory(prefix='medvision-workflow-') as tmp:
        folder=Path(tmp);os.environ['MEDVISION_DB']=str(folder/'db.sqlite3');os.environ['MEDVISION_GENERATED_DIR']=str(folder/'storage');os.environ['MEDVISION_DEMO_PASSWORD']='synthetic-workflow-password';os.environ['MEDVISION_FEEDBACK_THRESHOLD']='99';os.environ.pop('MEDVISION_BUNDLE',None)
        import backend_service as b
        from fastapi.testclient import TestClient
        from app_store import Store
        if not a.real:
            def predictor(path,checkpoint):
                im=cv2.imread(path,0);mask=np.zeros(im.shape,np.uint8);mask[8:16,8:16]=255
                ok,raw=cv2.imencode('.png',mask)
                return {'mask_png_base64':base64.b64encode(raw).decode(),'mask_shape':list(im.shape),'mask_present':True,'model_sha256':'deterministic-test-only','severity_features':{'component_count':1,'area':64}}
            b._predict_selected=predictor
        with TestClient(b.app) as client:
            check(client.get('/studies').status_code==401,'study search requires session')
            check(client.get('/models/current').status_code==401,'model information requires session')
            check(client.post('/auth/login',json={'identifier':'demo.clinician@example.invalid','password':'synthetic-workflow-password'}).status_code==200,'clinician login')
            patient=client.post('/patients',json={'name':'Synthetic Patient Alpha','age':42,'gender':'Female'}).json()
            check(patient['identifier'].startswith('MV-'),'backend assigns persistent patient identifier')
            check(client.post('/patients',json={'name':'Synthetic different individual','identifier':patient['identifier']}).status_code==409,'duplicate identifier rejected')
            same=client.post('/patients',json={'name':'Synthetic Patient Alpha','age':20}).json()
            check(same['id']!=patient['id'],'same name never merges patient identities')
            check(client.post('/patients',json={'name':'Invalid','age':131}).status_code==422,'patient input validation')
            check(client.get('/patients/search',params={'q':patient['identifier']}).json()[0]['id']==patient['id'],'returning patient search by identifier')
            check(len(client.get('/patients/search',params={'q':'Synthetic Patient Alpha'}).json())==2,'returning patient search distinguishes duplicate names')
            study_data={'patient_id':patient['id'],'examination_date':'2026-10-14','body_part':'Forearm','laterality':'Left','clinical_history':'Synthetic research fixture','referring_physician':'Synthetic Referrer'}
            study=client.post('/studies',json=study_data).json();sid=study['id']
            check(client.post('/studies',json={**study_data,'patient_id':'missing'}).status_code==404,'study requires owned patient')
            check(client.post('/studies',json={**study_data,'examination_date':'bad'}).status_code==422,'examination date validation')
            buf=io.BytesIO();Image.fromarray(np.arange(64*80,dtype=np.uint8).reshape(64,80)).save(buf,format='PNG');raw=buf.getvalue();ids=[]
            for view in ('AP','Lateral','Oblique'):
                response=client.post('/studies/'+sid+'/images',data={'view_type':view},files={'image':('synthetic.png',raw,'image/png')})
                check(response.status_code==200,'upload '+view);aid=response.json()['analysisId'];ids.append(aid)
                for _ in range(180):
                    status=client.get('/analyses/'+aid+'/status').json()
                    if status['status'] not in ('queued','processing'):break
                    time.sleep(.2)
                check(status['status']=='completed',('real' if a.real else 'deterministic')+' inference '+view)
                result=client.get('/analyses/'+aid).json()
                check(result['confidence'] is None and 'not supported' in result['bone'],'unsupported clinical fields explicit '+view)
                mask=cv2.imdecode(np.frombuffer(base64.b64decode(result['maskPngBase64']),np.uint8),0)
                check(mask.shape==(64,80),'native mask alignment '+view)
                check(client.get(result['originalImageUrl']).content==raw,'stored original unchanged '+view)
                check(client.get(result['overlayUrl']).status_code==200,'stored overlay retrieval '+view)
                check(bool(result['modelVersion']) and bool(result['analysisCompletedAt']),'persisted model version and completion time '+view)
            loaded=client.get('/studies/'+sid).json()
            check(len(loaded['images'])==3 and loaded['patient']['id']==patient['id'],'three views belong to one persisted patient/study')
            check({i['view_type'] for i in loaded['images']}=={'AP','Lateral','Oblique'},'view selector metadata comes from database')
            for q in ('Synthetic Patient Alpha',patient['identifier']):check(client.get('/studies',params={'q':q}).json()['total']==1,'backend study search '+q)
            check(client.get('/studies',params={'examination_date':'2026-10-14','body_part':'Forearm','laterality':'Left','status':'completed'}).json()['total']==1,'backend study filters')
            check(client.post('/studies/search',json={'q':patient['identifier']}).json()['total']==1,'private study search via body')
            check(client.post('/patients/search',json={'q':patient['identifier']}).json()[0]['id']==patient['id'],'private patient search via body')
            check(client.get('/studies',params={'limit':0}).status_code==422,'search pagination validated')
            check(client.get('/patients/'+patient['id']+'/history').json()['total']==1,'returning patient previous study retrieval')
            rep=client.post('/studies/'+sid+'/report/generate').json()
            check(rep['status']=='draft' and rep['revision']==1,'AI draft never finalized automatically')
            check(rep['patient_information']['identifier']==patient['identifier'] and len(rep['examination']['views'])==3,'structured report uses persisted patient and examination')
            payload={'revision':rep['revision'],'findings':'Radiologist edited synthetic findings','impression':'Synthetic reviewed impression','ai_decision':'corrected','corrections':{'bone':'Radiologist-supplied synthetic correction'}}
            saved=client.post('/studies/'+sid+'/report/save',json=payload).json()
            check(saved['revision']==2 and len(saved['versions'])==2,'report edits persist with immutable AI draft history')
            check(client.post('/studies/'+sid+'/report/save',json=payload).status_code==409,'concurrent report revision conflict rejected')
            payload['revision']=saved['revision'];final=client.post('/studies/'+sid+'/report/finalize',json=payload).json()
            check(final['status']=='final' and bool(final['finalized_at']),'report finalized by authorized reviewer')
            payload['revision']=final['revision'];check(client.post('/studies/'+sid+'/report/save',json=payload).status_code==409,'final report locked until reopened')
            reopened=client.post('/studies/'+sid+'/report/reopen',json=payload).json();check(reopened['status']=='draft' and len(reopened['versions'])==4,'final report can reopen with audit trail')
            correct=client.post('/analyses/'+ids[0]+'/feedback',json={'correct':True,'comments':'Synthetic correct review'}).json()
            incorrect=client.post('/analyses/'+ids[1]+'/feedback',json={'correct':False,'category':'Incorrect segmentation','comments':'Synthetic correction needed'}).json()
            check(correct['confirmed']==0 and incorrect['confirmed']==0,'correct and incorrect feedback persisted as preliminary')
            check(client.post('/analyses/'+ids[0]+'/feedback',json={'correct':False,'category':'fake'}).status_code==422,'feedback category validation')
            check(client.post('/feedback/'+incorrect['id']+'/confirm',json={'fracture_present':False,'training_consent':True,'training_partition_verified':True}).status_code==422,'incorrect result cannot train without corrected mask')
            mask=np.zeros((64,80),np.uint8);ok,encoded=cv2.imencode('.png',mask)
            check(client.post('/feedback/'+incorrect['id']+'/mask',files={'mask':('mask.png',encoded.tobytes(),'image/png')}).status_code==200,'native binary corrected mask stored')
            check(client.post('/feedback/'+incorrect['id']+'/confirm',json={'fracture_present':False,'training_consent':True,'training_partition_verified':True}).status_code==200,'reviewed correction confirmation persisted')
            check(client.get('/analyses/'+ids[1]+'/feedback').json()[0]['confirmed']==1,'confirmed annotation distinct from preliminary feedback')
            check(client.post('/feedback/'+incorrect['id']+'/mask',files={'mask':('mask.png',encoded.tobytes(),'image/png')}).status_code==409,'confirmed annotation immutable')
            check(client.post('/retraining/jobs',json={}).status_code==403,'manual training restricted to administrator')
            check(client.post('/models/fracture_model_v1/promote').status_code==403,'model promotion restricted to administrator')
            check(client.post('/studies/'+sid+'/images',data={'view_type':'Unknown'},files={'image':('x.png',raw,'image/png')}).status_code==422,'invalid view rejected')
            check(client.post('/studies/'+sid+'/images',data={'view_type':'AP'},files={'image':('x.png',b'bad','image/png')}).status_code==415,'invalid image signature rejected')
            check(client.delete('/analyses/'+ids[0]).status_code==409,'audited study analysis cannot be silently deleted')
            with b.store.connect() as db:
                check(not db.execute('PRAGMA foreign_key_check').fetchall(),'foreign-key integrity checked')
                user=b.demo_user.copy();user.update(id='admin-test',email='admin.synthetic@example.invalid',role='admin');b.store.seed_user(user,'synthetic-admin-password')
            with TestClient(b.app) as other:
                other.post('/auth/login',json={'identifier':'admin.synthetic@example.invalid','password':'synthetic-admin-password'})
                check(other.get('/studies/'+sid).status_code==404,'cross-account patient/study access denied')
                check(other.get('/analyses/'+ids[0]).status_code==404,'cross-account image analysis access denied')
                check(other.post('/models/fracture_model_v1/promote').status_code==409,'unvalidated model cannot be promoted even by administrator')
                check(other.post('/retraining/jobs',json={}).status_code==409,'confirmed-image threshold checked before creating job')
            # Database uniqueness holds under concurrent creation, not just frontend checks.
            def concurrent_create(_):
                try:b.workflow.create_patient(b.demo_user['id'],{'name':'Concurrent Synthetic','identifier':'SYN-CONCURRENT','age':None,'gender':'Other'});return True
                except ValueError:return False
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:check(sum(pool.map(concurrent_create,range(4)))==1,'concurrent patient identifier uniqueness')
            import sqlite3
            original_create=b.workflow.create_patient
            def broken_database(*args,**kwargs):raise sqlite3.OperationalError('synthetic database outage')
            b.workflow.create_patient=broken_database
            check(client.post('/patients',json={'name':'Synthetic outage'}).status_code==503,'database failure produces meaningful service error')
            b.workflow.create_patient=original_create
            # Exercise rollback against a retained real legacy artifact in this
            # disposable database only; this is a registry lifecycle fixture.
            with b.store.connect() as db:
                db.execute("INSERT INTO model_versions(id,status,checkpoint_sha,training_config,created_at) VALUES('retained_legacy_fixture','previous',?,'{}',?)",(hashlib.sha256(b.CHECKPOINT_PATH.read_bytes()).hexdigest(),'2026-10-14T00:00:00+00:00'))
            with TestClient(b.app) as manager:
                manager.post('/auth/login',json={'identifier':'admin.synthetic@example.invalid','password':'synthetic-admin-password'})
                rolled=manager.post('/models/retained_legacy_fixture/rollback')
                check(rolled.status_code==200 and rolled.json()['previous_version']=='fracture_model_v1','rollback handler activates retained checksum-verified legacy artifact in disposable registry')
                check(manager.get('/models/current').json()['model']['id']=='retained_legacy_fixture','model version change persisted after rollback fixture')
            with b.store.connect() as db:check(db.execute("SELECT count(*) FROM model_events WHERE action='rollback'").fetchone()[0]==1,'rollback audit event persisted')
            fresh=Store(folder/'db.sqlite3');check(fresh.get_case(ids[0],b.demo_user['id']) is not None,'case persists across Store reopening')
            check(b.workflow.study(b.demo_user['id'],sid)['patient']['identifier']==patient['identifier'],'patient and study persistence verified')
    out=ROOT/'test-results';out.mkdir(exist_ok=True);report={'mode':'real checkpoint inference' if a.real else 'deterministic integration predictor','checks_passed':len(checks),'checks':checks,'synthetic_patient_data':True,'metrics_claimed':False};(out/('workflow-real.json' if a.real else 'workflow-integration.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
