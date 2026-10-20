"""Read-only audit. Never signs, deposits, resolves or repairs chain state."""
import hashlib
import base64
import json
import re
import sys
import time
from datetime import datetime,timezone
import requests
from genlayer_py import create_client,studionet
from genlayer_py.types import TransactionHashVariant
from chain import browser_post  # Shared transport; no signing account is loaded.
from pathlib import Path
from eth_account import Account

ROOT=Path(__file__).resolve().parent.parent
p=json.loads((ROOT/'deploy/proof.json').read_text(encoding='utf8'))
links=json.loads((ROOT/'deploy/links.json').read_text(encoding='utf8'))
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
(ROOT/'deploy/proof-verification.json').write_text(json.dumps({'checkedAt':datetime.now(timezone.utc).isoformat(),'passed':False,'readOnly':True,'failures':['Audit has not completed. A network or process failure must not leave a stale green report.']}),encoding='utf8')
c=create_client(chain=studionet,account=Account.create())
failures=[];checks=[]
def check(ok,message):
    checks.append({'passed':bool(ok),'check':message})
    print('PASS' if ok else 'FAIL',message,flush=True)
    if not ok:
        failures.append(message)
        report={'checkedAt':datetime.now(timezone.utc).isoformat(),'passed':False,'checks':checks,'failures':failures,'readOnly':True,'sourceCommit':p.get('sourceCommit'),'note':'Audit stopped at the first failed check. No writes or repairs were attempted.'}
        (ROOT/'deploy/proof-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        raise SystemExit(1)
def get_json(url):
    for attempt in range(3):
        try:
            r=requests.get(url,headers=headers,timeout=60);r.raise_for_status();return r.json()
        except Exception:
            if attempt==2:raise
            time.sleep(10)

def get_evidence(url):
    # Archive availability can briefly return 429 even while the immutable
    # capture remains available. Retry bounded transient failures, preserving
    # the exact URL and reporting failure if availability does not recover.
    for attempt in range(3):
        try:
            response=requests.get(url,headers=headers,timeout=60)
        except requests.RequestException:
            if attempt==2:raise
            time.sleep(10)
            continue
        if response.status_code not in (429,500,502,503,504) or attempt==2:return response
        retry=response.headers.get('Retry-After','')
        delay=max(30,int(retry)) if retry.isdigit() else 30
        print('Transient evidence HTTP',response.status_code,'retrying after',delay,'seconds',flush=True)
        while delay>0:
            pause=min(delay,30);time.sleep(pause);delay-=pause
def read(name,method,args):
    v=c.read_contract(p['contracts'][name]['address'],method,args=args,transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
    time.sleep(2.2)
    return json.loads(v) if isinstance(v,str) and v.startswith(('{','[')) else v
def success(r):
    leader=(r.get('consensus_data',{}).get('leader_receipt') or [{}])[0] if r.get('consensus_data') else {}
    native=r.get('value_credited') is True and not r.get('consensus_data') and str(r.get('type'))=='0'
    finalized=r.get('status_name',r.get('status')) in ('FINALIZED',7,'7')
    return finalized and (native or r.get('txExecutionResultName',leader.get('execution_result')) in ('SUCCESS','FINISHED_WITH_RETURN') and r.get('result_name') in (None,'AGREE','MAJORITY_AGREE','SUCCESS'))

check(p.get('chainId')==61999,'StudioNet chain 61999')
actual_chain=c.provider.make_request('eth_chainId',[])['result']
actual_chain_id=int(actual_chain,0) if isinstance(actual_chain,str) else int(actual_chain)
check(actual_chain_id==61999,'actual RPC chain identity StudioNet 61999')
if p.get('releaseAttempt',0)>=5:
    fields=json.loads((ROOT/'docs/submission/portal-fields.json').read_text(encoding='utf8'))
    for name,url in links['contracts'].items():
        check(url in fields.get('evidence',[]) and any(entry.get('url')==url and entry.get('preferredEvidenceType')=='GenLayer Explorer Contract' and entry.get('chainId')==61999 for entry in fields.get('evidenceEntries',[])),name+' direct contract URL is a separate typed StudioNet evidence entry')
for name,contract in p['contracts'].items():
    source=(ROOT/'contracts'/contract['source']).read_bytes()
    check(hashlib.sha256(source).hexdigest()==contract['sha256'],name+' local source matches deployment manifest')
    deployed=c.provider.make_request('gen_getContractCode',[contract['address']])['result']
    check(hashlib.sha256(base64.b64decode(deployed)).hexdigest()==contract['sha256'],name+' deployed source hash')
    time.sleep(2.2)
    url=links.get('contracts',{}).get(name,'')
    check(re.fullmatch(r'https://explorer-studio\.genlayer\.com/address/0x[0-9a-fA-F]{40}',url) is not None,name+' canonical contract URL')
    result=get_json(url.replace('/address/','/api/address/'))
    check(result.get('type')=='CONTRACT' and str(result.get('address','')).lower()==contract['address'].lower(),name+' real explorer record type CONTRACT and exact address')

for label,h in p['transactions'].items():
    saved=ROOT/'deploy/receipts'/(label+'.json')
    stored=json.loads(saved.read_text(encoding='utf8')) if saved.exists() else {}
    check(stored.get('hash')==h,label+' saved receipt hash')
    url=links.get('transactions',{}).get(label,'')
    check(re.fullmatch(r'https://explorer-studio\.genlayer\.com/tx/0x[0-9a-fA-F]{64}',url) is not None,label+' canonical tx URL')
    data=get_json(url.replace('/tx/','/api/transactions/'))
    # Explorer currently returns the transaction object; explicitly bind to its hash.
    actual=data.get('transaction',data)
    check(str(actual.get('hash',actual.get('transaction_hash',''))).lower()==h.lower(),label+' real explorer transaction')
    live_consensus=actual.get('consensus_data') or {};saved_consensus=stored.get('consensus_data') or {}
    live_leader=(live_consensus.get('leader_receipt') or [{}])[0]
    saved_leader=(saved_consensus.get('leader_receipt') or [{}])[0]
    bound=all(actual.get(k)==stored.get(k) for k in ('hash','status','type','value','from_address','to_address','data')) and live_consensus.get('votes')==saved_consensus.get('votes') and all(live_leader.get(k)==saved_leader.get(k) for k in ('result','execution_result','eq_outputs'))
    check(bound,label+' live explorer binds saved RPC receipt fields and consensus output')
    votes=list((live_consensus.get('votes') or {}).values())
    # Explorer supplies immutable finalized consensus data. Native credit is
    # omitted there, so native transfers and failures always get a direct RPC
    # reread. A missing quorum or schema mismatch also falls back to RPC.
    if bound and votes.count('agree')>=3 and label not in p.get('expectedFailures',{}):r=stored
    else:r=c.provider.make_request('eth_getTransactionByHash',[h])['result']
    if label in p.get('expectedFailures',{}):
        expected=p['expectedFailures'][label]
        extra=r.get('value_credited') is True if expected=='FAILED_PAYABLE' else r.get('result_name')=='MAJORITY_DISAGREE' if expected=='CONSENSUS_DISAGREEMENT' else True
        check(bool(r) and r.get('status')=='FINALIZED' and not success(r) and extra,label+' expected finalized error: '+expected)
    else:check(bool(r) and success(r),label+' finalized execution success')
    # Explorer API reads are sequential. Actual StudioNet RPC calls already
    # enforce the shared minute/hour budget in browser_post.

for entry in p.get('takes',[]):
    t=entry['take'];key=t['id']
    live=read('Takes','get_take',[key])
    check(live==t,key+' finalized take readback')
    encoded=json.dumps(t['rule'],sort_keys=True,separators=(',',':')).encode()
    check(hashlib.sha256(encoded).hexdigest()==t['rule_hash'],key+' frozen rule SHA-256')
    resolution=read('TakeResolver','get_resolution',[key]);bet=read('TakeEscrow','get_bet',[key])
    check(resolution==entry['resolution'] and bet==entry['bet'],key+' resolution and escrow readback')
    for evidence in resolution.get('evidence',[]):
        response=get_evidence(evidence['url'])
        check(response.status_code==200,key+' reviewer evidence URL opens')
    if bet.get('status')=='SETTLED':
        check(sum(map(int,bet['payouts'].values()))==int(bet['total']),key+' settlement conserves wei')
        for wallet,claim in bet.get('claims',{}).items():
            check(claim['status']=='PAID',key+' payout receipt verified for '+wallet)
            if claim.get('child'):
                child=c.provider.make_request('eth_getTransactionByHash',[claim['child']])['result'];time.sleep(2.2)
                check(child.get('value_credited') is True and str(child.get('to_address','')).lower()==wallet.lower() and int(child['value'])==int(claim['amount']),key+' native value credited')
for profile in p.get('profiles',[]):check(read('CalledItRecord','get_profile',[profile['wallet']])==profile,'profile finalized readback '+profile['wallet'])

if p.get('nativeBalanceProof'):
    balances=p['nativeBalanceProof'];entry=next(e for e in p['takes'] if e['take']['id']==balances.get('takeId')) if balances.get('takeId') else next(e for e in p['takes'] if e.get('label')=='sources-unreachable')
    check(balances.get('passed') is True,'exact native balance proof completed')
    before=balances.get('before',{}).get('balancesWei',{})
    after=balances.get('after',{}).get('balancesWei',{})
    for label,address in balances['addresses'].items():
        result=c.provider.make_request('eth_getBalance',[address,'latest'])['result'];time.sleep(2.2)
        actual=int(result,0) if isinstance(result,str) else int(result)
        check(str(actual)==after.get(label),'live native '+label+' balance equals final recorded balance')
        expected=-sum(map(int,entry['bet']['payouts'].values())) if label=='escrow' else int(entry['bet']['payouts'].get(address.lower(),0))
        check(actual-int(before.get(label,0))==expected,'exact native '+label+' balance change matches finalized payout')

known=set(links.get('contracts',{}).values())|set(links.get('legacyContracts',{}).values())|set(links.get('previousUnsettledContracts',{}).values())|set(links.get('transactions',{}).values())
for url in links.get('documentationExplorer',[]):
    if url in known:continue
    address=re.fullmatch(r'https://explorer-studio\.genlayer\.com/address/(0x[0-9a-fA-F]{40})',url)
    transaction=re.fullmatch(r'https://explorer-studio\.genlayer\.com/tx/(0x[0-9a-fA-F]{64})',url)
    check(bool(address or transaction),'canonical additional documented explorer URL '+url)
    if address:check(get_json(url.replace('/address/','/api/address/')).get('type')=='CONTRACT','actual additional documented contract type CONTRACT '+url)
    if transaction:
        data=get_json(url.replace('/tx/','/api/transactions/'));actual=data.get('transaction',data)
        check(str(actual.get('hash','')).lower()==transaction.group(1).lower(),'actual additional documented transaction hash '+url)

labels={e.get('label'):e for e in p.get('takes',[])}
check(labels.get('official-yes',{}).get('resolution',{}).get('verdict')=='YES','real official announcement demo YES')
check(labels.get('rumours-no',{}).get('resolution',{}).get('verdict')=='NO','real nonqualifying reports demo NO')
check(labels.get('no-evidence-default',{}).get('resolution',{}).get('default_applied') is True,'no-evidence default demo')
check(labels.get('subjective-rejection',{}).get('take',{}).get('status')=='REJECTED','compile rejection demo')
if p.get('releaseAttempt')==5:
    check(labels.get('scheduling-void',{}).get('resolution',{}).get('resolution_case')=='VOID_INSUFFICIENT_EVIDENCE' and labels['scheduling-void']['resolution'].get('outcome')=='VOID','configured v2 judge resolves real Grammy scheduling evidence VOID')
check(any(e.get('bet',{}).get('counterparty') and e['bet'].get('status')=='SETTLED' and any(v.get('status')=='PAID' for v in e['bet'].get('claims',{}).values()) for e in p.get('takes',[])),'second-wallet acceptance, settlement and verified claim')
check(any(profile['wins']+profile['losses']+profile['voids']>0 for profile in p.get('profiles',[])),'public record updated')
refund=p.get('refundDemo',{})
if p.get('releaseAttempt',0)<3:
    check(int(refund.get('after',{}).get('claim',{}).get('amount',0))==2 and refund.get('after',{}).get('claim',{}).get('status')=='PAID' and int(refund.get('after',{}).get('available_wei',-1))==0,'invalid and failed payable deposits recovered and pulled')
    if refund.get('nativeChild'):
        child=c.provider.make_request('eth_getTransactionByHash',[refund['nativeChild']])['result']
        check(child.get('value_credited') is True and int(child.get('value',0))==2 and str(child.get('to_address','')).lower()==refund['wallet'].lower(),'refund native child credits both wei to original sender')
    check(len([e for e in p.get('takes',[]) if not e['take']['historical'] and e['bet'].get('status')=='OPEN' and e['take']['rule']['deadline']>time.time()])>=2,'two funded live open takes')
else:
    check(labels['no-evidence-default']['resolution'].get('resolution_case')=='DEFAULT_NO_EVIDENCE','only no submitted evidence applies default')
    for entry in p['takes']:
        r=entry['resolution'];b=entry['bet']
        if r.get('resolution_case') in ('VOID_SOURCES_UNREACHABLE','VOID_TIMEOUT','VOID_INSUFFICIENT_EVIDENCE'):
            check(r.get('outcome')=='VOID' and not r.get('default_applied'),entry['take']['id']+' technical or inconclusive outcome refunds, never default')
            if b.get('status')=='SETTLED':check(b['payouts']==b['deposits'],entry['take']['id']+' VOID refunds original deposits exactly')
    old=p.get('legacyLiveTakes',[])
    check(len(old)==2 and all(e['take']['rule']['deadline']>time.time() for e in old),'two pending live takes retained on explicitly documented earlier deployment')
    for e in old:
        value=c.read_contract(e['contracts']['TakeEscrow']['address'],'get_bet',args=[e['take']['id']],transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
        value=json.loads(value) if isinstance(value,str) else value
        check(value==e['bet'],e['take']['id']+' old funded live take readback');time.sleep(2.2)
    for name,url in links.get('legacyContracts',{}).items():
        check(re.fullmatch(r'https://explorer-studio\.genlayer\.com/address/0x[0-9a-fA-F]{40}',url) is not None,name+' canonical legacy contract URL')
        check(get_json(url.replace('/address/','/api/address/')).get('type')=='CONTRACT',name+' actual legacy contract record type CONTRACT')
    for e in p.get('previousUnsettledBets',[]):
        value=c.read_contract(e['contracts']['TakeEscrow']['address'],'get_bet',args=[e['entry']['take']['id']],transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
        value=json.loads(value) if isinstance(value,str) else value
        check(value==e['entry']['bet'],'previous revision '+str(e['attempt'])+' matched bet and held balance readback');time.sleep(2.2)
    for name,url in links.get('previousUnsettledContracts',{}).items():
        check(re.fullmatch(r'https://explorer-studio\.genlayer\.com/address/0x[0-9a-fA-F]{40}',url) is not None,name+' canonical earlier matched-bet contract URL')
        check(get_json(url.replace('/address/','/api/address/')).get('type')=='CONTRACT',name+' actual earlier matched-bet contract record type CONTRACT')
    for url in links.get('other',[]):
        response=get_evidence(url);check(response.status_code==200,'published non-explorer URL HTTP 200: '+url)
budget=p.get('approvedDepositBudgetWei',20)
check(type(budget) is int and budget in (20,22,24) and sum(p.get('deposits',{}).values())<=budget,'cumulative simulated deposits within recorded approved '+str(budget)+' wei')
unproven=[]
if p.get('releaseAttempt',0)>=3 and not p.get('unreachableProof',{}).get('proven'):
    unproven.append('The full real blocked-host VOID proof is unproven; actual case: '+p.get('unreachableProof',{}).get('actualCase','pending')+'. Source preflights and the additional access probe are retained. Mocked 401/403 coverage is not live proof.')
report={'checkedAt':datetime.now(timezone.utc).isoformat(),'passed':not failures,'checks':checks,'failures':failures,'readOnly':True,'unproven':unproven,'sourceCommit':p.get('sourceCommit'),'contractHashes':{name:contract['sha256'] for name,contract in p['contracts'].items()},'receiptVerification':'Live Explorer fields, leader output and quorum bound to saved RPC receipts; direct RPC for native credits, expected failures and missing quorum. Contract source and finalized state are read directly by RPC.'}
(ROOT/'deploy/proof-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(len(checks),'checks;',len(failures),'failures')
sys.exit(1 if failures else 0)
