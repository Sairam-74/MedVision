"""Local project-owner command. Filesystem/database access is the authority."""
import argparse
import hashlib
import secrets
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app_store import Store

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Reissue a lost recovery code locally; no HTTP endpoint.')
    parser.add_argument('--email',required=True)
    args=parser.parse_args()
    store=Store(ROOT/'.local_demo/app.sqlite3')
    code=secrets.token_urlsafe(32)
    with store.connect() as db:
        row=db.execute('SELECT id FROM users WHERE email=?',(args.email.strip().lower(),)).fetchone()
        if not row:raise SystemExit('Account not found. No account was changed.')
        db.execute('INSERT OR REPLACE INTO recovery_keys VALUES(?,?)',(row[0],hashlib.sha256(code.encode()).hexdigest()))
        db.execute('DELETE FROM password_resets WHERE user_id=?',(row[0],))
    if row[0]=='user-1':
        (ROOT/'.local_demo/demo_recovery_code.txt').write_text(code,encoding='utf-8')
    print('New recovery code (save privately; previous code and reset links are invalid):')
    print(code)
