"""Bootstrap isolated local accounts; never change existing account passwords."""
import os
from pathlib import Path
import secrets
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app_store import Store
from workflow_store import WorkflowStore
root=Path(__file__).resolve().parents[1];folder=root/'.feature_data';folder.mkdir(exist_ok=True)
db_path=Path(os.environ.get('MEDVISION_DB',folder/'app.sqlite3')).resolve()
if root not in db_path.parents:raise ValueError('Database must be inside the independent clone')
store=Store(db_path);WorkflowStore(store)
for role in ('clinician','admin'):
    file=folder/(role+'_password.txt')
    with store.connect() as db:exists=db.execute('SELECT 1 FROM users WHERE email=?',('feature.'+role+'@example.invalid',)).fetchone()
    if exists:continue
    password=secrets.token_urlsafe(32);file.write_text(password,encoding='utf-8')
    user={'id':'feature-'+role,'name':'Synthetic Feature '+role.title(),'email':'feature.'+role+'@example.invalid','role':role,'status':'active','organization':'Isolated Local Research'}
    store.seed_user(user,password)
print('Isolated accounts and additive migrations ready; passwords remain in local ignored files.')
