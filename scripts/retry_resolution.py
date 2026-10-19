"""Bounded diagnosed zero-value retries; retain every disagreement receipt."""
import json
import sys
from chain import ROOT, load, save, read, tx

p=load();key='take-2';attempt=int(sys.argv[1]) if len(sys.argv)>1 else 2
if attempt not in (2,3):raise RuntimeError('Only the two explicitly bounded retry attempts are supported')
old='resolve-'+key if attempt==2 else 'resolve-retry-'+key+'-2'
r=json.loads((ROOT/'deploy/receipts'/(old+'.json')).read_text(encoding='utf8'))
if r.get('status')!='FINALIZED' or r.get('result_name')!='MAJORITY_DISAGREE':
    raise RuntimeError('Only this diagnosed finalized disagreement is authorized for retry')
p.setdefault('expectedFailures',{})[old]='CONSENSUS_DISAGREEMENT'
label='resolve-retry-'+key+'-'+str(attempt)
p.setdefault('resolutionAttempts',{})[key]=label
save(p)
state=read(p['contracts']['TakeResolver']['address'],'get_resolution',[key])
if state.get('status')!='OPEN' and label not in p['transactions']:
    raise RuntimeError('Readback must remain OPEN before a retry')
tx(p,label,p['contracts']['TakeResolver']['address'],'resolve',[key])
print('The same frozen rule and evidence were retried once, with zero value.',flush=True)
