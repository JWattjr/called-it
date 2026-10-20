"""Read-only partial link audit for the stopped fairness release, never a release verdict."""
import json,re,time,sys
from datetime import datetime,timezone
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent.parent
p=json.loads((ROOT/'deploy/proof.json').read_text())
diagnostic='--diagnostic' in sys.argv
prefix='diagnostic-schedule-v1-' if diagnostic else p.get('deploymentPrefix','r3-')
contracts={'Unfunded consensus candidate':p['consensusDiagnostics']} if diagnostic else p['contracts']
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
checks=[]
for name,contract in contracts.items():
    url='https://explorer-studio.genlayer.com/address/'+contract['address']
    response=requests.get(url.replace('/address/','/api/address/'),headers=headers,timeout=60)
    data=response.json() if response.status_code==200 else {}
    checks.append({'label':name,'url':url,'apiHttpStatus':response.status_code,'type':data.get('type'),'passed':response.status_code==200 and data.get('type')=='CONTRACT'})
    time.sleep(2.2)
for label,h in p['transactions'].items():
    if not label.startswith(prefix):continue
    url='https://explorer-studio.genlayer.com/tx/'+h
    response=requests.get(url.replace('/tx/','/api/transactions/'),headers=headers,timeout=60)
    data=response.json() if response.status_code==200 else {}
    actual=data.get('transaction',data)
    stored=json.loads((ROOT/'deploy/receipts'/(label+'.json')).read_text())
    passed=response.status_code==200 and str(actual.get('hash','')).lower()==h.lower() and actual.get('status')==stored.get('status')=='FINALIZED'
    checks.append({'label':label,'url':url,'apiHttpStatus':response.status_code,'status':actual.get('status'),'savedResult':stored.get('result_name'),'passed':passed})
    time.sleep(2.2)
syntax=all(re.fullmatch(r'0x[0-9a-fA-F]{64}',h) for h in p['transactions'].values())
report={'checkedAt':datetime.now(timezone.utc).isoformat(),'releaseAttempt':p['releaseAttempt'],'readOnly':True,'scope':str(len(contracts))+' contract API records and all '+prefix+'transaction API records. A valid link does not imply successful contract execution.','passed':syntax and all(v['passed'] for v in checks),'allTransactionIdentifiersCanonical':syntax,'checks':checks,'notReaudited':['Earlier release transaction records','Other published HTTP links','Full contract source and state audit'],'executionFailures':[v for v in checks if v.get('savedResult')=='MAJORITY_DISAGREE']}
(ROOT/('deploy/diagnostic-link-audit.json' if diagnostic else 'deploy/fairness-link-audit.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(len(checks),'link checks;',sum(not v['passed'] for v in checks),'failures; this is a partial link audit, not successful live proof.')
raise SystemExit(0 if report['passed'] else 1)
