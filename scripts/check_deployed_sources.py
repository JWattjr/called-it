"""Read-only early gate: actual deployed bytes must match this checkout."""
import base64,hashlib,json,time
from datetime import datetime,timezone
from chain import ROOT,load,browser_post
from genlayer_py import create_client,studionet

p=load();target=ROOT/'deploy/source-verification.json'
target.write_text(json.dumps({'passed':False,'reason':'Audit running; do not reuse an earlier result.'}))
c=create_client(chain=studionet)
checks=[]
assert len(p['contracts'])==4
for name,contract in p['contracts'].items():
    deployed=c.provider.make_request('gen_getContractCode',[contract['address']])['result']
    live=hashlib.sha256(base64.b64decode(deployed)).hexdigest()
    local=hashlib.sha256((ROOT/'contracts'/contract['source']).read_bytes()).hexdigest()
    checks.append({'contract':name,'address':contract['address'],'manifest':contract['sha256'],'deployed':live,'local':local,'passed':live==local==contract['sha256']})
    time.sleep(2.2)
report={'checkedAt':datetime.now(timezone.utc).isoformat(),'passed':all(v['passed'] for v in checks),'readOnly':True,'checks':checks,'releaseAttempt':p['releaseAttempt']}
target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('Deployed source hashes:',sum(v['passed'] for v in checks),'of',len(checks),'match local bytes and manifest.')
raise SystemExit(0 if report['passed'] else 1)
