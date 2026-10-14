"""Additive SQLite migration for owned studies, reports and reviewed corrections."""
import json
import secrets
import sqlite3
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


def uid(prefix):
    return prefix + '-' + secrets.token_hex(16)


class WorkflowStore:
    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS workflow_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS patients(id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), identifier TEXT NOT NULL, name TEXT NOT NULL, age INTEGER, gender TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(owner_id,identifier));
            CREATE TABLE IF NOT EXISTS studies(id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), patient_id TEXT NOT NULL REFERENCES patients(id), examination_date TEXT NOT NULL, body_part TEXT NOT NULL, laterality TEXT NOT NULL, clinical_history TEXT NOT NULL, referring_physician TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS study_images(id TEXT PRIMARY KEY, study_id TEXT NOT NULL REFERENCES studies(id), analysis_id TEXT UNIQUE NOT NULL REFERENCES cases(id), view_type TEXT NOT NULL CHECK(view_type IN ('AP','Lateral','Oblique')), uploaded_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY, study_id TEXT UNIQUE NOT NULL REFERENCES studies(id), revision INTEGER NOT NULL, status TEXT NOT NULL, findings TEXT NOT NULL, impression TEXT NOT NULL, ai_decision TEXT NOT NULL, corrections TEXT NOT NULL, author_id TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, finalized_at TEXT);
            CREATE TABLE IF NOT EXISTS report_versions(id TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES reports(id), revision INTEGER NOT NULL, snapshot TEXT NOT NULL, author_id TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(report_id,revision));
            CREATE TABLE IF NOT EXISTS feedback(id TEXT PRIMARY KEY, analysis_id TEXT NOT NULL REFERENCES cases(id), owner_id TEXT NOT NULL REFERENCES users(id), reviewer_id TEXT NOT NULL REFERENCES users(id), correct INTEGER NOT NULL, category TEXT NOT NULL, comments TEXT NOT NULL, corrected_findings TEXT NOT NULL, corrected_mask_path TEXT, confirmed INTEGER NOT NULL DEFAULT 0, model_version TEXT NOT NULL, created_at TEXT NOT NULL, confirmed_at TEXT);
            CREATE TABLE IF NOT EXISTS model_versions(id TEXT PRIMARY KEY, status TEXT NOT NULL, bundle_path TEXT, checkpoint_sha TEXT NOT NULL, dataset_version TEXT, training_config TEXT NOT NULL, metrics TEXT, created_at TEXT NOT NULL, trained_at TEXT, evaluated_at TEXT, promoted_at TEXT, previous_version TEXT);
            CREATE TABLE IF NOT EXISTS model_events(id TEXT PRIMARY KEY, action TEXT NOT NULL, model_id TEXT NOT NULL, actor_id TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS retraining_jobs(id TEXT PRIMARY KEY, status TEXT NOT NULL, actor_id TEXT NOT NULL, config TEXT NOT NULL, feedback_ids TEXT NOT NULL, candidate_id TEXT, error TEXT, created_at TEXT NOT NULL, started_at TEXT, completed_at TEXT);
            CREATE INDEX IF NOT EXISTS patients_search ON patients(owner_id,name,identifier);
            CREATE INDEX IF NOT EXISTS studies_search ON studies(owner_id,examination_date,body_part,laterality);
            CREATE INDEX IF NOT EXISTS images_study ON study_images(study_id);
            CREATE INDEX IF NOT EXISTS feedback_analysis ON feedback(analysis_id);
            ''')
            db.execute('INSERT OR IGNORE INTO workflow_migrations VALUES(1,?)',(now(),))
            columns={r[1] for r in db.execute('PRAGMA table_info(retraining_jobs)')}
            if 'worker_pid' not in columns:db.execute('ALTER TABLE retraining_jobs ADD COLUMN worker_pid INTEGER')
            import psutil
            for row in db.execute("SELECT id,worker_pid FROM retraining_jobs WHERE status IN ('queued','training','evaluating')").fetchall():
                live=False
                try:
                    cmd=psutil.Process(row['worker_pid']).cmdline() if row['worker_pid'] else []
                    live=any('retrain_worker.py' in arg for arg in cmd) and row['id'] in cmd
                except (psutil.Error,TypeError):pass
                if not live:db.execute("UPDATE retraining_jobs SET status='interrupted',error='Worker interrupted; authorized retry required',completed_at=? WHERE id=?",(now(),row['id']))

    def create_patient(self, owner, data):
        stamp=now(); identifier=data.get('identifier') or 'MV-'+secrets.token_hex(8).upper()
        item=dict(id=uid('pat'),owner_id=owner,identifier=identifier,name=data['name'],age=data.get('age'),gender=data['gender'],created_at=stamp,updated_at=stamp)
        try:
            with self.store.connect() as db:
                db.execute('INSERT INTO patients VALUES(:id,:owner_id,:identifier,:name,:age,:gender,:created_at,:updated_at)',item)
        except sqlite3.IntegrityError as e:
            raise ValueError('Patient identifier already exists in this account') from e
        return item

    def patients(self, owner, q='', offset=0, limit=25):
        # Escape LIKE wildcards so identifiers are literal search terms.
        term='%'+q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        with self.store.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM patients WHERE owner_id=? AND (name LIKE ? ESCAPE '\\' OR identifier LIKE ? ESCAPE '\\') ORDER BY name,id LIMIT ? OFFSET ?",(owner,term,term,limit,offset))]

    def patient(self, owner, patient_id):
        with self.store.connect() as db:
            row=db.execute('SELECT * FROM patients WHERE id=? AND owner_id=?',(patient_id,owner)).fetchone()
            return dict(row) if row else None

    def create_study(self, owner, data):
        if not self.patient(owner,data['patient_id']): raise LookupError('Patient not found')
        stamp=now(); item=dict(id=uid('stu'),owner_id=owner,**data,created_at=stamp,updated_at=stamp)
        with self.store.connect() as db:
            db.execute('INSERT INTO studies VALUES(:id,:owner_id,:patient_id,:examination_date,:body_part,:laterality,:clinical_history,:referring_physician,:created_at,:updated_at)',item)
        return item

    def study(self, owner, study_id):
        with self.store.connect() as db:
            row=db.execute('SELECT * FROM studies WHERE id=? AND owner_id=?',(study_id,owner)).fetchone()
            if not row:return None
            item=dict(row); item['patient']=dict(db.execute('SELECT * FROM patients WHERE id=?',(item['patient_id'],)).fetchone())
            item['images']=[dict(r) for r in db.execute('SELECT * FROM study_images WHERE study_id=? ORDER BY uploaded_at,id',(study_id,))]
        return item

    def search(self, owner, q='', patient_id='', examination_date='', body_part='', laterality='', status='', limit=25, offset=0):
        clauses=['s.owner_id=?']; args=[owner]
        if q:
            term='%'+q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
            clauses.append("(p.name LIKE ? ESCAPE '\\' OR p.identifier LIKE ? ESCAPE '\\')");args.extend([term,term])
        for column,value in [('s.patient_id',patient_id),('s.examination_date',examination_date),('s.body_part',body_part),('s.laterality',laterality)]:
            if value:clauses.append(column+'=?');args.append(value)
        if status in ('draft','final'):
            clauses.append('r.status=?');args.append(status)
        elif status:
            clauses.append("EXISTS(SELECT 1 FROM study_images i JOIN cases c ON c.id=i.analysis_id WHERE i.study_id=s.id AND json_extract(c.payload,'$.status')=?)");args.append(status)
        query=' FROM studies s JOIN patients p ON p.id=s.patient_id LEFT JOIN reports r ON r.study_id=s.id WHERE '+' AND '.join(clauses)
        with self.store.connect() as db:
            count=db.execute('SELECT count(*)'+query,args).fetchone()[0]
            rows=db.execute('SELECT s.*,p.name AS patient_name,p.identifier AS patient_identifier,r.status AS report_status'+query+' ORDER BY s.examination_date DESC,s.created_at DESC LIMIT ? OFFSET ?',(*args,limit,offset)).fetchall()
            items=[]
            for row in rows:
                item=dict(row)
                item['images']=[dict(r) for r in db.execute("SELECT i.view_type,i.analysis_id,json_extract(c.payload,'$.status') AS status FROM study_images i JOIN cases c ON c.id=i.analysis_id WHERE i.study_id=?",(item['id'],))]
                items.append(item)
        return dict(items=items,total=count,limit=limit,offset=offset)

    def attach(self, owner, study_id, analysis_id, view):
        if not self.study(owner,study_id):raise LookupError('Study not found')
        with self.store.connect() as db:
            db.execute('INSERT INTO study_images VALUES(?,?,?,?,?)',(uid('img'),study_id,analysis_id,view,now()))
            db.execute('UPDATE studies SET updated_at=? WHERE id=?',(now(),study_id))

    def report(self, owner, study_id, create=False):
        study=self.study(owner,study_id)
        if not study:raise LookupError('Study not found')
        with self.store.connect() as db:
            row=db.execute('SELECT * FROM reports WHERE study_id=?',(study_id,)).fetchone()
            if row and create:
                existing=dict(row)
                if existing['status']=='final':raise ValueError('Reopen a final report before regenerating')
                findings=[]
                for image in study['images']:
                    case,result,error=self.store.get_case(image['analysis_id'],owner)
                    if result:
                        findings.append(f"{image['view_type']}: {result.get('fracturePresence','Uncertain')}; {result.get('severityFeatures',{}).get('componentCount',0)} segmented regions. Model {result.get('modelVersion','unavailable')}. Bone/type/displacement/angulation not supported; confidence unavailable.")
                return self.save_report(owner,study_id,{'revision':existing['revision'],'findings':'\n'.join(findings),'impression':'AI-assisted research draft. Radiologist review required; no diagnosis established.','ai_decision':'pending','corrections':{}},'save')
            if not row and create:
                findings=[]; versions=[]
                for image in study['images']:
                    record=self.store.get_case(image['analysis_id'],owner)
                    case,result,error=record
                    if result:
                        findings.append(f"{image['view_type']}: {result.get('fracturePresence','Uncertain')}; {result.get('severityFeatures',{}).get('componentCount',0)} segmented regions. Bone, type, displacement and angulation not supported. Confidence unavailable.")
                        versions.append(result.get('modelVersion',result.get('modelSha256','unknown')))
                    else:findings.append(f"{image['view_type']}: {case['status']}. Analysis unavailable.")
                stamp=now()
                item=dict(id=uid('rep'),study_id=study_id,revision=1,status='draft',findings='\n'.join(findings) or 'No completed analysis available.',impression='AI-assisted research draft; uncertain clinical significance. Radiologist review required. No diagnosis established.',ai_decision='pending',corrections=json.dumps({'model_versions':versions}),author_id=owner,created_at=stamp,updated_at=stamp,finalized_at=None)
                db.execute('INSERT OR IGNORE INTO reports VALUES(:id,:study_id,:revision,:status,:findings,:impression,:ai_decision,:corrections,:author_id,:created_at,:updated_at,:finalized_at)',item)
                row=db.execute('SELECT * FROM reports WHERE study_id=?',(study_id,)).fetchone()
                db.execute('INSERT OR IGNORE INTO report_versions VALUES(?,?,?,?,?,?)',(uid('rv'),row['id'],1,json.dumps(dict(row)),owner,stamp))
            if not row:return None
            item=dict(row);item['patient_information']={k:study['patient'][k] for k in ('name','identifier','age','gender')}
            item['examination']={k:study[k] for k in ('examination_date','body_part','laterality','clinical_history','referring_physician')}
            item['examination']['views']=[i['view_type'] for i in study['images']]
            item['versions']=[dict(r) for r in db.execute('SELECT * FROM report_versions WHERE report_id=? ORDER BY revision',(item['id'],))]
            return item

    def save_report(self, owner, study_id, data, action):
        existing=self.report(owner,study_id)
        if not existing:raise LookupError('Generate a draft first')
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=dict(db.execute('SELECT * FROM reports WHERE study_id=?',(study_id,)).fetchone())
            if row['revision']!=data['revision']:raise ValueError('Report changed; reload before saving')
            if row['status']=='final' and action!='reopen':raise ValueError('Reopen the finalized report before editing')
            if action=='finalize' and data['ai_decision']=='pending':raise ValueError('Review, accept, reject or correct AI suggestions before finalization')
            stamp=now();row.update(findings=data['findings'],impression=data['impression'],ai_decision=data['ai_decision'],corrections=json.dumps({**json.loads(row['corrections']), 'radiologist':data['corrections']}),revision=row['revision']+1,status='final' if action=='finalize' else 'draft',author_id=owner,updated_at=stamp,finalized_at=stamp if action=='finalize' else None)
            db.execute('UPDATE reports SET revision=:revision,status=:status,findings=:findings,impression=:impression,ai_decision=:ai_decision,corrections=:corrections,author_id=:author_id,updated_at=:updated_at,finalized_at=:finalized_at WHERE id=:id',row)
            db.execute('INSERT INTO report_versions VALUES(?,?,?,?,?,?)',(uid('rv'),row['id'],row['revision'],json.dumps(row),owner,stamp))
        return self.report(owner,study_id)

    def feedback(self, owner, analysis_id, data, version, mask_path=None):
        item=dict(id=uid('fb'),analysis_id=analysis_id,owner_id=owner,reviewer_id=owner,correct=int(data['correct']),category=data['category'],comments=data['comments'],corrected_findings=json.dumps(data['corrected_findings']),corrected_mask_path=mask_path,confirmed=0,model_version=version,created_at=now(),confirmed_at=None)
        with self.store.connect() as db:
            db.execute('INSERT INTO feedback VALUES(:id,:analysis_id,:owner_id,:reviewer_id,:correct,:category,:comments,:corrected_findings,:corrected_mask_path,:confirmed,:model_version,:created_at,:confirmed_at)',item)
        return item

    def feedback_list(self, owner, analysis_id):
        with self.store.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM feedback WHERE owner_id=? AND analysis_id=? ORDER BY created_at',(owner,analysis_id))]
