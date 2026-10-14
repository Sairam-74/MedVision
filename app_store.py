"""Transactional local-demo accounts, revocable sessions and owned case storage."""
from contextlib import contextmanager
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sqlite3
import time


def hash_password(password, salt=None):
    salt=salt or secrets.token_hex(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex()
    return f'pbkdf2_sha256$600000${salt}${digest}'


def verify_password(password, encoded):
    _,iterations,salt,digest=encoded.split('$')
    actual=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),int(iterations)).hex()
    return hmac.compare_digest(actual,digest)


class Store:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE,password_hash TEXT,user_json TEXT);
                CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id TEXT,expires REAL);
                CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY,owner_id TEXT,created REAL,payload TEXT,result TEXT,error TEXT);
                CREATE TABLE IF NOT EXISTS login_failures(ip TEXT,created REAL);
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT);
                CREATE TABLE IF NOT EXISTS recovery_keys(user_id TEXT PRIMARY KEY,code_hash TEXT);
                CREATE TABLE IF NOT EXISTS password_resets(token_hash TEXT PRIMARY KEY,user_id TEXT,expires REAL);
                CREATE TABLE IF NOT EXISTS auth_attempts(scope TEXT,ip TEXT,created REAL);
            ''')
        self.dummy_hash=hash_password(secrets.token_urlsafe(24))

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        db.row_factory=sqlite3.Row
        try:
            with db: yield db
        finally: db.close()

    def seed_user(self,user,password):
        with self.connect() as db:
            exists=db.execute('SELECT 1 FROM users WHERE email=?',(user['email'],)).fetchone()
            if not exists and password:
                db.execute('INSERT INTO users VALUES(?,?,?,?)',(user['id'],user['email'],hash_password(password),json.dumps(user)))

    def login(self,email,password,ip):
        now=time.time()
        with self.connect() as db:
            db.execute('DELETE FROM login_failures WHERE created<?',(now-60,))
            if db.execute('SELECT count(*) FROM login_failures WHERE ip=?',(ip,)).fetchone()[0]>=5:
                return None,True
            row=db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        valid=verify_password(password,row['password_hash'] if row else self.dummy_hash)
        if not row or not valid:
            with self.connect() as db: db.execute('INSERT INTO login_failures VALUES(?,?)',(ip,now))
            return None,False
        return json.loads(row['user_json']),False

    def credentials_match(self,email,password):
        with self.connect() as db:
            row=db.execute('SELECT password_hash FROM users WHERE email=?',(email,)).fetchone()
        return bool(row and verify_password(password,row[0]))

    def allow_auth_attempt(self,scope,ip,limit=5,window=60):
        now=time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM auth_attempts WHERE created<?',(now-900,))
            if db.execute('SELECT count(*) FROM auth_attempts WHERE scope=? AND ip=? AND created>?',(scope,ip,now-window)).fetchone()[0]>=limit:
                return False
            db.execute('INSERT INTO auth_attempts VALUES(?,?,?)',(scope,ip,now))
        return True

    def create_user(self,name,email,password):
        user={'id':'user-'+secrets.token_hex(16),'name':name,'email':email,
              'role':'technician','status':'active','organization':'Local Research Workspace'}
        code=secrets.token_urlsafe(32)
        encoded=hash_password(password)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT count(*) FROM users').fetchone()[0]>=100:
                raise ValueError('Local account limit reached')
            if db.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone():
                raise ValueError('An account already uses this email')
            db.execute('INSERT INTO users VALUES(?,?,?,?)',(user['id'],email,encoded,json.dumps(user)))
            db.execute('INSERT INTO recovery_keys VALUES(?,?)',(user['id'],hashlib.sha256(code.encode()).hexdigest()))
        return user,code

    def seed_recovery(self,user_id,code):
        if not code:return
        with self.connect() as db:
            if db.execute('SELECT 1 FROM users WHERE id=?',(user_id,)).fetchone():
                db.execute('INSERT OR IGNORE INTO recovery_keys VALUES(?,?)',(user_id,hashlib.sha256(code.encode()).hexdigest()))

    def recovery_grant(self,email,code,ttl=600):
        digest=hashlib.sha256(code.encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT users.id,code_hash FROM users JOIN recovery_keys ON users.id=recovery_keys.user_id WHERE email=?',(email,)).fetchone()
            if not hmac.compare_digest(digest,row['code_hash'] if row else '0'*64):
                return None
            token=secrets.token_urlsafe(32)
            db.execute('DELETE FROM password_resets WHERE expires<? OR user_id=?',(time.time(),row['id']))
            db.execute('INSERT INTO password_resets VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],time.time()+ttl))
        return token

    def reset_password(self,token,password):
        digest=hashlib.sha256(token.encode()).hexdigest()
        encoded=hash_password(password)
        code=secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT user_id FROM password_resets WHERE token_hash=? AND expires>?',(digest,time.time())).fetchone()
            if not row:return None
            user_id=row['user_id']
            db.execute('UPDATE users SET password_hash=? WHERE id=?',(encoded,user_id))
            db.execute('DELETE FROM sessions WHERE user_id=?',(user_id,))
            db.execute('DELETE FROM password_resets WHERE user_id=?',(user_id,))
            db.execute('INSERT OR REPLACE INTO recovery_keys VALUES(?,?)',(user_id,hashlib.sha256(code.encode()).hexdigest()))
        return user_id,code

    def session(self,user_id,ttl=8*3600):
        token=secrets.token_urlsafe(32); expires=time.time()+ttl
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
            db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user_id,expires))
        return token,expires

    def user_for_session(self,token):
        if not token or len(token)>256: return None
        digest=hashlib.sha256(token.encode()).hexdigest()
        with self.connect() as db:
            row=db.execute('SELECT user_json FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires>?',(digest,time.time())).fetchone()
        return json.loads(row[0]) if row else None

    def revoke(self,token):
        if token:
            with self.connect() as db: db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))

    def save_case(self,case,owner,result=None,error=None):
        with self.connect() as db:
            db.execute('INSERT INTO cases VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,result=excluded.result,error=excluded.error',
                       (case['id'],owner,time.time(),json.dumps(case,default=str),json.dumps(result) if result else None,error))

    def list_cases(self,owner):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT payload FROM cases WHERE owner_id=? ORDER BY created DESC',(owner,))]

    def get_case(self,case_id,owner):
        with self.connect() as db:
            row=db.execute('SELECT * FROM cases WHERE id=? AND owner_id=?',(case_id,owner)).fetchone()
        if not row: return None
        return json.loads(row['payload']),json.loads(row['result']) if row['result'] else None,row['error']

    def delete_case(self,case_id,owner):
        with self.connect() as db: db.execute('DELETE FROM cases WHERE id=? AND owner_id=?',(case_id,owner))

    def mark_interrupted(self):
        with self.connect() as db:
            for row in db.execute('SELECT * FROM cases').fetchall():
                case=json.loads(row['payload'])
                if case['status'] in ('queued','processing'):
                    case['status']='failed'
                    db.execute('UPDATE cases SET payload=?,error=? WHERE id=?',(json.dumps(case),'Server restarted during processing. Upload again.',row['id']))

    def import_legacy_demo(self,path,demo_id):
        if not Path(path).is_file(): return
        with self.connect() as db:
            if db.execute("SELECT 1 FROM metadata WHERE key='legacy_import'").fetchone(): return
        old=json.loads(Path(path).read_text(encoding='utf-8'))
        # Prior application recorded every case as its single demo user. Keep
        # that account's history; do not expose filesystem paths or history JSON.
        for case in old.get('analyses',[]):
            self.save_case(case,demo_id,old.get('results',{}).get(case['id']),old.get('errors',{}).get(case['id']))
        with self.connect() as db: db.execute("INSERT OR REPLACE INTO metadata VALUES('legacy_import','1')")
