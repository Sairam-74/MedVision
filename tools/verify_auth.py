"""Real account lifecycle checks using disposable storage; no emails are sent."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    checks=[]
    def check(value,label):
        if not value: raise RuntimeError(label)
        checks.append(label)
    with tempfile.TemporaryDirectory(prefix='medvision-auth-') as t:
        folder=Path(t)
        os.environ['MEDVISION_DB']=str(folder/'accounts.sqlite3')
        os.environ['MEDVISION_GENERATED_DIR']=str(folder/'generated')
        os.environ['MEDVISION_DEMO_PASSWORD']='disposable-demo-password'
        os.environ['MEDVISION_DEMO_RECOVERY_CODE']='disposable-demo-recovery-code-long'
        os.environ['MEDVISION_DEMO_PREFILL']='1'
        import backend_service as b
        from app_store import Store
        from fastapi.testclient import TestClient
        with TestClient(b.app,client=('127.0.0.1',4321)) as client, TestClient(b.app,client=('192.0.2.1',1234)) as remote:
            data=client.get('/auth/demo-credentials').json()
            check(data['enabled'] and data['password']==os.environ['MEDVISION_DEMO_PASSWORD'],'prefill matches the actual seeded demo password')
            check(remote.get('/auth/demo-credentials').json()=={'enabled':False},'demo prefill unavailable to non-loopback clients')
            check(client.get('/auth/demo-credentials',headers={'Origin':'https://evil.invalid'}).status_code==403,'untrusted origin cannot request demo prefill')
            check(client.get('/auth/demo-credentials',headers={'Sec-Fetch-Site':'cross-site'}).status_code==403,'cross-site demo prefill rejected')
            os.environ['MEDVISION_DEMO_PREFILL']='0'
            check(client.get('/auth/demo-credentials').json()=={'enabled':False},'demo prefill requires explicit enablement')
            os.environ['MEDVISION_DEMO_PREFILL']='1'
            registration={'name':'New Researcher','email':'NEW@example.invalid','password':'original-long-password'}
            response=client.post('/auth/signup',json={**registration,'role':'admin'})
            check(response.status_code==422,'signup cannot assign an admin role')
            check(client.post('/auth/signup',json={**registration,'password':'short'}).status_code==422,'server enforces password length')
            check(client.post('/auth/signup',json={**registration,'email':'bad-address'}).status_code==422,'server validates email')
            response=client.post('/auth/signup',json=registration)
            check(response.status_code==201,'real account created')
            code=response.json()['recoveryCode']
            check(len(code)>=32,'signup returns a strong recovery code once')
            check(client.post('/auth/signup',json=registration).status_code==409,'duplicate email rejected')
            check(client.post('/auth/login',json={'identifier':'new@example.invalid','password':'incorrect-password'}).status_code==401,'wrong account password rejected')
            logged=client.post('/auth/login',json={'identifier':'new@example.invalid','password':registration['password']})
            check(logged.status_code==200 and logged.json()['user']['role']=='technician','signup account signs in without elevated privileges')
            session=client.cookies.get(b.COOKIE)
            check(client.get('/analyses').json()==[],'new account does not inherit demo history')
            fresh=Store(folder/'accounts.sqlite3')
            check(fresh.credentials_match('new@example.invalid',registration['password']),'account persists in SQLite')
            bad=client.post('/auth/forgot-password',json={'email':'new@example.invalid','recoveryCode':'invalid-recovery-code-long'})
            missing=client.post('/auth/forgot-password',json={'email':'missing@example.invalid','recoveryCode':'invalid-recovery-code-long'})
            check(bad.status_code==missing.status_code==400 and bad.json()==missing.json(),'recovery hides nonexistent versus wrong-code accounts')
            check(client.post('/auth/forgot-password',json={'email':'new@example.invalid'}).status_code==422,'email alone cannot grant reset access')
            recover=client.post('/auth/forgot-password',json={'email':'new@example.invalid','recoveryCode':code})
            check(recover.status_code==200 and '#token=' in recover.json()['resetUrl'],'valid recovery yields a reset token in URL fragment')
            token=recover.json()['resetUrl'].split('#token=')[1]
            with fresh.connect() as db:
                row=db.execute('SELECT token_hash,expires FROM password_resets').fetchone()
                check(row[0]!=token and 0<row[1]-time.time()<=600,'reset token hashed with ten-minute expiry')
                db.execute('UPDATE password_resets SET expires=?',(time.time()-1,))
            check(client.post('/auth/reset-password',json={'token':token,'password':'replacement-long-password'}).status_code==400,'expired token rejected')
            # Direct setup avoids imposing test traffic on the recovery request limiter.
            token=fresh.recovery_grant('new@example.invalid',code)
            reset=client.post('/auth/reset-password',json={'token':token,'password':'replacement-long-password'})
            check(reset.status_code==200,'password reset succeeds with ownership proof')
            new_code=reset.json()['recoveryCode']
            check(new_code!=code,'recovery code rotates after reset')
            client.cookies.set(b.COOKIE,session)
            check(client.get('/analyses').status_code==401,'all old sessions revoked after password reset')
            check(client.post('/auth/reset-password',json={'token':token,'password':'another-long-password'}).status_code==400,'reset token is single-use')
            check(fresh.recovery_grant('new@example.invalid',code) is None,'old recovery code revoked')
            check(fresh.recovery_grant('new@example.invalid',new_code) is not None,'new recovery code works')
            check(client.post('/auth/login',json={'identifier':'new@example.invalid','password':registration['password']}).status_code==401,'old password rejected')
            check(client.post('/auth/login',json={'identifier':'new@example.invalid','password':'replacement-long-password'}).status_code==200,'new password signs in')
            with fresh.connect() as db:
                user=db.execute('SELECT password_hash FROM users WHERE email=?',('new@example.invalid',)).fetchone()
                recovery=db.execute('SELECT code_hash FROM recovery_keys WHERE user_id=(SELECT id FROM users WHERE email=?)',('new@example.invalid',)).fetchone()
                check(user[0].startswith('pbkdf2_sha256$600000$') and new_code!=recovery[0],'password and recovery code stored as hashes')
            check(client.post('/auth/signup',json=registration,headers={'Origin':'https://evil.invalid'}).status_code==403,'cross-origin signup denied')
            for _ in range(8):
                last=client.post('/auth/forgot-password',json={'email':'missing@example.invalid','recoveryCode':'invalid-recovery-code-long'})
            check(last.status_code==429,'recovery requests rate limited')
    out=ROOT/'experiments/session_20261006_auth/auth_checks.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({'checks_passed':len(checks),'checks':checks,'temporary_storage':True,'real_existing_accounts_changed':False},indent=2))
    print('Account lifecycle checks passed:',len(checks))


if __name__=='__main__':main()
