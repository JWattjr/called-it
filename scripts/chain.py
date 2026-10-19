"""Release transport: pinned SDK, explicit zero fee, durable hashes, finalized reads."""
import importlib.metadata
import json
import re
import time
from contextlib import contextmanager
from functools import lru_cache
try:import msvcrt
except ImportError:msvcrt=None
from pathlib import Path
from eth_account import Account
from genlayer_py import create_client, studionet
from genlayer_py.types import TransactionHashVariant
from genlayer_py.provider import provider

ROOT=Path(__file__).resolve().parent.parent
assert importlib.metadata.version('genlayer-py')=='0.18.0'
_post=provider.requests.post
_broadcast_context=None

def broadcast_marker(label,details=None,remove=False):
    with journal_lock('broadcast'):
        path=ROOT/'.secrets/ambiguous-submissions.json'
        data=json.loads(path.read_text()) if path.exists() else {}
        previous=data.get(label)
        if remove:data.pop(label,None)
        elif details is not None:data[label]=details
        if remove or details is not None:
            temporary=path.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(data,indent=2),encoding='utf8')
            temporary.replace(path)
        return previous
def browser_post(url,**kwargs):
    method=kwargs.get('json',{}).get('method','')
    safe=method.startswith(('eth_get','gen_get','sim_get')) or method in ('eth_estimateGas','eth_chainId','gen_call')
    kwargs['headers']={**kwargs.get('headers',{}),'User-Agent':'Mozilla/5.0 CalledIt/1.0'}
    kwargs.setdefault('timeout',60)
    for attempt in range(3 if safe else 1):
        while True:
            with journal_lock('rpc-budget'):
                path=ROOT/'.secrets/rpc-times.json'
                stamps=json.loads(path.read_text()) if path.exists() else []
                t=time.time();stamps=[v for v in stamps if t-v<3600]
                allowed=len(stamps)<450 and sum(t-v<60 for v in stamps)<24
                if allowed:path.write_text(json.dumps(stamps+[t]))
            if allowed:break
            print('RPC budget: waiting ten seconds before next request',flush=True)
            time.sleep(10)
        try:
            if method=='eth_sendRawTransaction' and _broadcast_context:
                broadcast_marker(_broadcast_context['label'],{**_broadcast_context,'startedAtUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
            response=_post(url,**kwargs)
        except provider.requests.exceptions.RequestException:
            if not safe or attempt==2:raise
            print('Transient read-only RPC transport failure; retrying in ten seconds',flush=True)
            time.sleep(10)
            continue
        if response.status_code not in (502,503,504) or not safe or attempt==2:return response
        print('Transient read-only RPC HTTP',response.status_code,'retrying in ten seconds',flush=True)
        time.sleep(10)
provider.requests.post=browser_post

def signer(index=0):
    path=ROOT/'.secrets/demo-accounts.json'
    path.parent.mkdir(exist_ok=True)
    if not path.exists():path.write_text(json.dumps([Account.create().key.hex() for _ in range(2)]))
    return Account.from_key(json.loads(path.read_text())[index])

@lru_cache(maxsize=2)
def client(index=0):
    return create_client(chain=studionet,account=signer(index))

@contextmanager
def journal_lock(name):
    directory=ROOT/'.secrets'
    directory.mkdir(exist_ok=True)
    with (directory/(name+'.lock')).open('a+b') as handle:
        # Windows byte-range locks may extend past EOF. Do not read the byte
        # before acquiring it: another worker may already hold that range.
        while True:
            try:
                handle.seek(0)
                if msvcrt:msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except OSError:time.sleep(.1)
        try:yield
        finally:
            handle.seek(0)
            if msvcrt:msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(handle.fileno(),fcntl.LOCK_UN)

def save(p):
    path=ROOT/'deploy/proof.json'
    with journal_lock('proof'):
        current=json.loads(path.read_text(encoding='utf8')) if path.exists() else {}
        for key,value in current.items():p.setdefault(key,value)
        p['transactions']={**current.get('transactions',{}),**p.get('transactions',{})}
        if current.get('deposits') or p.get('deposits'):p['deposits']={**current.get('deposits',{}),**p.get('deposits',{})}
        if current.get('expectedFailures') or p.get('expectedFailures'):p['expectedFailures']={**current.get('expectedFailures',{}),**p.get('expectedFailures',{})}
        for key in ('website','github','sourceCommit','funding'):
            if current.get(key):p[key]=current[key]
        if current.get('recordedAt','')>p.get('recordedAt',''):
            for key in ('takes','profiles','demoWallets','recordedAt'):p[key]=current[key]
        tmp=path.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(p,indent=2),encoding='utf8')
        tmp.replace(path)

def load():
    path=ROOT/'deploy/proof.json'
    return json.loads(path.read_text()) if path.exists() else {'network':'StudioNet','chainId':61999,'contracts':{},'transactions':{},'takes':[],'releaseStatus':'IN_PROGRESS'}

def success(r):
    leader=(r.get('consensus_data',{}).get('leader_receipt') or [{}])[0] if r.get('consensus_data') else {}
    native=r.get('value_credited') is True and not r.get('consensus_data') and str(r.get('type'))=='0'
    finalized=r.get('status_name',r.get('status')) in ('FINALIZED',7,'7')
    return finalized and (native or r.get('txExecutionResultName',leader.get('execution_result')) in ('SUCCESS','FINISHED_WITH_RETURN') and r.get('result_name') in (None,'AGREE','MAJORITY_AGREE','SUCCESS'))

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

def tx(p,label,contract=None,method=None,args=None,code=None,index=0,value=0,wait=True):
    global _broadcast_context
    c=client(index)
    if value:
        approval=ROOT/'.secrets/deposit-approval.json'
        if not approval.exists() or json.loads(approval.read_text()).get('approvedTotalWei')!=20:
            raise RuntimeError('Owner must approve the 20-wei cumulative demo deposit budget')
        with journal_lock('proof'):
            current=load()
            journal=current.setdefault('deposits',{})
            if label not in journal:
                if sum(journal.values())+value>20:raise RuntimeError('Deposit budget exhausted')
                journal[label]=value
            elif journal[label]!=value:raise RuntimeError('Saved deposit amount differs from this attempt')
            p['deposits']=journal.copy()
            temporary=ROOT/'deploy/proof.json.tmp'
            temporary.write_text(json.dumps(current,indent=2),encoding='utf8')
            temporary.replace(ROOT/'deploy/proof.json')
    if label not in p['transactions']:
        with journal_lock('submit'):
            latest=load()
            if label in latest['transactions']:
                p['transactions'][label]=latest['transactions'][label]
            else:
                if broadcast_marker(label):
                    raise RuntimeError('Broadcast outcome is unknown for '+label+'. Reconcile the wallet and Explorer before any retry; no duplicate submission was sent.')
                _broadcast_context={'label':label,'contract':contract,'method':method,'walletIndex':index,'valueWei':str(value)}
                try:
                    h=c.deploy_contract(code,args=args or [],fees=fees(c)) if code is not None else c.write_contract(contract,method,args=args or [],value=value,fees=fees(c))
                    h=h.hex() if hasattr(h,'hex') else str(h)
                    h=h if h.startswith('0x') else '0x'+h
                    if re.fullmatch(r'0x[0-9a-fA-F]{64}',h) is None:
                        raise RuntimeError('Unrecognized broadcast response; reconcile before retrying '+label)
                    p['transactions'][label]=h
                    save(p)
                    broadcast_marker(label,remove=True)
                finally:_broadcast_context=None
    if not wait:return {'hash':p['transactions'][label],'status':'SUBMITTED'}
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
