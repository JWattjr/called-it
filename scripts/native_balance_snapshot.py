"""Read native balances before claims and verify exact credit deltas afterward."""
import json,sys,time
from datetime import datetime,timezone
from chain import ROOT,load,save,client

p=load();phase=sys.argv[1]
entry=next(e for e in p['takes'] if e['label']=='sources-unreachable')
b=entry['bet'];assert b.get('counterparty')
addresses={'author':b['author'],'counterparty':b['counterparty'],'escrow':p['contracts']['TakeEscrow']['address']}
proof=p.setdefault('nativeBalanceProof',{'addresses':addresses})
assert proof['addresses']==addresses
if phase=='before' and proof.get('before'):
    print('Existing pre-claim balance snapshot retained.');raise SystemExit(0)
assert phase in ('before','after')
assert b['status']==('MATCHED' if phase=='before' else 'SETTLED')
values={}
for label,address in addresses.items():
    result=client().provider.make_request('eth_getBalance',[address,'latest'])['result']
    values[label]=str(int(result,0) if isinstance(result,str) else int(result))
    time.sleep(2.2)
proof[phase]={'checkedAt':datetime.now(timezone.utc).isoformat(),'balancesWei':values}
if phase=='after':
    assert proof.get('before')
    before=proof['before']['balancesWei'];checks=[]
    for label in ('author','counterparty'):
        amount=int(b['payouts'].get(addresses[label].lower(),0))
        claim=b.get('claims',{}).get(addresses[label].lower(),{})
        checks.append({'wallet':label,'expectedCreditWei':str(amount),'actualCreditWei':str(int(values[label])-int(before[label])),'passed':int(values[label])-int(before[label])==amount and (amount==0 or claim.get('status')=='PAID')})
    total=sum(map(int,b['payouts'].values()))
    checks.append({'wallet':'escrow','expectedDebitWei':str(total),'actualDebitWei':str(int(before['escrow'])-int(values['escrow'])),'passed':int(before['escrow'])-int(values['escrow'])==total})
    proof.update(passed=all(v['passed'] for v in checks),checks=checks)
save(p)
(ROOT/'deploy/native-balance-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
print(phase,'native balances recorded:',values)
if phase=='after' and not proof['passed']:raise RuntimeError('Native balance deltas do not match verified payouts; STOP')
