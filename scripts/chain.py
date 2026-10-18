"""Release transport: pinned SDK, explicit zero fee, durable hashes, finalized reads."""
import importlib.metadata
import json
import time
from pathlib import Path
from eth_account import Account
from genlayer_py import create_client, studionet
from genlayer_py.types import TransactionHashVariant
from genlayer_py.provider import provider

ROOT=Path(__file__).resolve().parent.parent
assert importlib.metadata.version('genlayer-py')=='0.18.0'
_post=provider.requests.post
def browser_post(url,**kwargs):
    kwargs['headers']={**kwargs.get('headers',{}),'User-Agent':'Mozilla/5.0 CalledIt/1.0'}
    kwargs.setdefault('timeout',60)
    return _post(url,**kwargs)
provider.requests.post=browser_post

def signer(index=0):
    path=ROOT/'.secrets/demo-accounts.json'
    path.parent.mkdir(exist_ok=True)
    if not path.exists():path.write_text(json.dumps([Account.create().key.hex() for _ in range(2)]))
    return Account.from_key(json.loads(path.read_text())[index])

def client(index=0):
    return create_client(chain=studionet,account=signer(index))

def save(p):
    path=ROOT/'deploy/proof.json'
    tmp=path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(p,indent=2),encoding='utf8')
    tmp.replace(path)

def load():
    path=ROOT/'deploy/proof.json'
    return json.loads(path.read_text()) if path.exists() else {'network':'StudioNet','chainId':61999,'contracts':{},'transactions':{},'takes':[],'releaseStatus':'IN_PROGRESS'}

def success(r):
    leader=(r.get('consensus_data',{}).get('leader_receipt') or [{}])[0] if r.get('consensus_data') else {}
    return r.get('status_name',r.get('status')) in ('FINALIZED',7,'7') and (r.get('txExecutionResultName',leader.get('execution_result')) in ('SUCCESS','FINISHED_WITH_RETURN') or r.get('value_credited') is True) and r.get('result_name') not in ('MAJORITY_DISAGREE','UNDETERMINED','DISAGREE')

def final(c,h,label,seconds=1800):
    target=ROOT/'deploy/receipts'/(label+'.json')
    if target.exists():
        r=json.loads(target.read_text())
        if success(r):return r
    for n in range(seconds//10):
        r=c.provider.make_request('eth_getTransactionByHash',[h])['result']
        if r and r.get('status_name',r.get('status')) in ('FINALIZED',7,'7'):
            target.write_text(json.dumps(r,indent=2),encoding='utf8')
            print(label,'FINALIZED_SUCCESS' if success(r) else 'FINALIZED_ERROR',h,flush=True)
            if not success(r):raise RuntimeError('Finalized execution error: '+label)
            return r
        if n%6==0:print(label,'waiting',r.get('status') if r else 'SUBMITTED',flush=True)
        time.sleep(10)
    raise RuntimeError('Still pending; resume saved hash '+h)

def fees(c):
    try:
        f=c.estimate_transaction_fees({'leaderTimeunitsAllocation':300,'validatorTimeunitsAllocation':600,'totalMessageFees':0,'rotations':[2]})
    except Exception as e:
        if 'missing fee_manager_contract and sim_getFeeConfig' not in str(e):raise
        return {'feeValue':0}
    if int(f['feeValue']):raise RuntimeError('Nonzero network fee requires owner approval')
    return {'feeValue':0,'distribution':f['distribution']}

def tx(p,label,contract=None,method=None,args=None,code=None,index=0,value=0):
    c=client(index)
    if value:
        approval=ROOT/'.secrets/deposit-approval.json'
        if not approval.exists() or json.loads(approval.read_text()).get('approvedTotalWei')!=20:
            raise RuntimeError('Owner must approve the 20-wei cumulative demo deposit budget')
        journal=p.setdefault('deposits',{})
        if label not in journal:
            if sum(journal.values())+value>20:raise RuntimeError('Deposit budget exhausted')
            journal[label]=value
            save(p)
    if label not in p['transactions']:
        h=c.deploy_contract(code,args=args or [],fees=fees(c)) if code is not None else c.write_contract(contract,method,args=args or [],value=value,fees=fees(c))
        h=h.hex() if hasattr(h,'hex') else str(h)
        p['transactions'][label]=h if h.startswith('0x') else '0x'+h
        save(p)
    r=final(c,p['transactions'][label],label)
    for i,h in enumerate(r.get('triggered_transactions') or []):
        child=label+'-child-'+str(i)
        p['transactions'][child]=h
        save(p)
        final(c,h,child)
    return r

def read(address,method,args=None,index=0):
    for attempt in range(4):
        try:
            r=client(index).read_contract(address,method,args=args or [],transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
            break
        except Exception:
            if attempt==3:raise
            time.sleep(10*(attempt+1))
    time.sleep(2.2)
    return json.loads(r) if isinstance(r,str) and r.startswith(('{','[')) else r
