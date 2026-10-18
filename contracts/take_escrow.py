# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Deterministic stake arithmetic and native pulls. No LLM; payable bodies do no external reads."""
import json
import re
import base64
from datetime import datetime
from genlayer import *

def now():
    return int(datetime.fromisoformat(str(gl.message_raw['datetime']).replace('Z','+00:00')).timestamp())

def require(ok,message):
    if not ok:raise gl.vm.UserError('[EXPECTED] '+message)

def receipt(h):
    require(re.fullmatch(r'0x[0-9a-fA-F]{64}',h) is not None,'transaction hash required')
    r=gl.nondet.web.post('https://studio.genlayer.com/api',body=json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_getTransactionByHash','params':[h]}).encode(),headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0 CalledIt/1.0'})
    require(r.status==200,'receipt RPC unavailable')
    data=json.loads(r.body.decode('utf8'))
    require(data.get('result') is not None and not data.get('error'),'receipt unavailable')
    return data['result']

@gl.evm.contract_interface
class Recipient:
    class View:
        pass
    class Write:
        pass

class TakeEscrow(gl.Contract):
    takes: Address
    bets: TreeMap[str,str]
    credits: TreeMap[str,u256]
    credit_claims: TreeMap[str,str]
    accounted: u256
    recovered: TreeMap[str,bool]

    def __init__(self,takes: str):
        self.takes=Address(takes)
        self.accounted=u256(0)

    def _take(self,key):
        t=json.loads(gl.get_contract_at(self.takes).view().get_take(key))
        require(t.get('status')=='COMPILED','finalized compiled take required')
        return t

    def _unresolved(self,key):
        config=gl.get_contract_at(self.takes).view().get_config()
        r=json.loads(gl.get_contract_at(Address(config['resolver'])).view().get_resolution(key))
        require(r.get('status','OPEN')=='OPEN','take already resolving')

    @gl.public.write
    def prepare_open(self,key: str) -> None:
        t=self._take(key)
        require(str(gl.message.sender_address).lower()==t['author'],'author only')
        existing=json.loads(self.bets.get(key,'{}'))
        require(now()<t['accept_deadline'] and (not existing or existing['status']=='PREPARED' and not existing['deposits']),'take already funded or expired')
        self._unresolved(key)
        r={'id':key,'author':t['author'],'counterparty':'','rule_hash':t['rule_hash'],'author_stake':t['stake_wei'],'counter_stake':str(int(t['stake_wei'])*t['ratio']),'accept_deadline':t['accept_deadline'],'refund_deadline':t['evidence_deadline']+49*3600,'status':'PREPARED','deposits':{},'payouts':{},'claims':{},'intent_wallet':t['author'],'intent_expires':min(now()+900,t['accept_deadline']),'intent_kind':'AUTHOR','total':'0'}
        self.bets[key]=json.dumps(r)

    @gl.public.write
    def prepare_accept(self,key: str) -> None:
        require(key in self.bets,'author must fund first')
        r=json.loads(self.bets[key])
        wallet=str(gl.message.sender_address).lower()
        require(r['status']=='OPEN' and now()<r['accept_deadline'] and wallet!=r['author'],'open take; different counterparty required')
        require(not r['intent_wallet'] or now()>=r['intent_expires'],'another counterparty has a 15-minute reservation')
        self._unresolved(key)
        r['intent_wallet'],r['intent_expires'],r['intent_kind']=wallet,min(now()+900,r['accept_deadline']),'COUNTER'
        self.bets[key]=json.dumps(r)

    @gl.public.write.payable
    def deposit(self,key: str) -> None:
        # Deliberately no require, cross-contract access, web or model call here.
        # Even a stale, repeated, wrong-wallet or wrong-value payment is accounted for.
        wallet=str(gl.message.sender_address).lower()
        value=int(gl.message.value)
        self.accounted=u256(int(self.accounted)+value)
        r=json.loads(self.bets.get(key,'{}'))
        expected=int(r.get('author_stake' if r.get('intent_kind')=='AUTHOR' else 'counter_stake','0'))
        valid=value>0 and r.get('status') in ('PREPARED','OPEN') and r.get('intent_wallet')==wallet and now()<r.get('intent_expires',0) and value==expected and wallet not in r.get('deposits',{})
        if not valid:
            self.credits[wallet]=u256(int(self.credits.get(wallet,u256(0)))+value)
            return
        r['deposits'][wallet]=str(value)
        r['total']=str(int(r['total'])+value)
        r['status']='FUNDING' if r['intent_kind']=='AUTHOR' else 'MATCHING'
        if r['intent_kind']=='COUNTER':r['counterparty']=wallet
        r['intent_wallet']=''
        self.bets[key]=json.dumps(r)
        gl.get_contract_at(gl.message.contract_address).emit(on='finalized').finalize_deposit(key)

    @gl.public.write
    def finalize_deposit(self,key: str) -> None:
        require(gl.message.sender_address==gl.message.contract_address,'self finality callback only')
        r=json.loads(self.bets[key])
        if r['status'] not in ('FUNDING','MATCHING'):return
        r['status']='OPEN' if r['status']=='FUNDING' else 'MATCHED'
        r['funded_at']=now()
        self.bets[key]=json.dumps(r)

    @gl.public.write
    def settle(self,key: str) -> None:
        require(key in self.bets,'no escrow')
        r=json.loads(self.bets[key])
        require(r['status'] in ('PREPARED','OPEN','MATCHED','FUNDING','MATCHING'),'escrow already settled')
        if r['status'] in ('FUNDING','MATCHING'):
            require(now()>=r['refund_deadline'],'deposit finality pending; wait for refund deadline')
            r['outcome']='VOID'
            r['payouts']=r['deposits'].copy()
            r['reason']='Deposit finality callback timeout; recorded deposits refundable.'
        elif r['status'] in ('PREPARED','OPEN'):
            require(now()>=r['accept_deadline'],'acceptance deadline not reached')
            r['outcome']='VOID'
            r['payouts']=r['deposits'].copy()
            r['reason']='No counterparty before acceptance deadline.'
        else:
            config=gl.get_contract_at(self.takes).view().get_config()
            resolution=json.loads(gl.get_contract_at(Address(config['resolver'])).view().get_resolution(key))
            if resolution.get('status')=='FINAL':
                require(resolution['rule_hash']==r['rule_hash'],'frozen rule mismatch')
                outcome=resolution['outcome']
                require(outcome in ('YES','NO','VOID'),'invalid finalized outcome')
                r['outcome']=outcome
                winner=r['author'] if outcome=='YES' else r['counterparty']
                r['payouts']=r['deposits'].copy() if outcome=='VOID' else {winner:r['total']}
                r['reason']=resolution['reason']
            else:
                require(now()>=r['refund_deadline'],'wait for finalized result or refund deadline')
                r['outcome']='VOID'
                r['payouts']=r['deposits'].copy()
                r['reason']='Resolution timeout; both stakes refundable.'
        require(sum(int(v) for v in r['payouts'].values())==int(r['total']),'wei conservation')
        r['status']='SETTLING'
        self.bets[key]=json.dumps(r)
        gl.get_contract_at(gl.message.contract_address).emit(on='finalized').finalize_settlement(key)

    @gl.public.write
    def finalize_settlement(self,key: str) -> None:
        require(gl.message.sender_address==gl.message.contract_address,'self finality callback only')
        r=json.loads(self.bets[key])
        if r['status']!='SETTLING':return
        r['status']='SETTLED'
        r['finalized_at']=now()
        self.bets[key]=json.dumps(r)

    @gl.public.write
    def claim(self,key: str,attempt: int) -> None:
        r=json.loads(self.bets[key])
        wallet=str(gl.message.sender_address).lower()
        require(r['status']=='SETTLED','settlement not final')
        amount=int(r['payouts'].get(wallet,'0'))
        previous=r['claims'].get(wallet)
        require(amount>0 and (not previous or previous['status']=='FAILED'),'no unclaimed payout or transfer pending')
        require(attempt==(previous['attempt']+1 if previous else 1),'next claim attempt required')
        require(int(self.balance)>=amount,'native funds unavailable')
        r['claims'][wallet]={'amount':str(amount),'attempt':attempt,'status':'PENDING','requested_at':now()}
        self.bets[key]=json.dumps(r)
        self.accounted=u256(int(self.accounted)-amount)
        Recipient(Address(wallet)).emit_transfer(value=u256(amount),on='finalized')

    @gl.public.write
    def claim_credit(self,attempt: int) -> None:
        wallet=str(gl.message.sender_address).lower()
        amount=int(self.credits.get(wallet,u256(0)))
        previous=json.loads(self.credit_claims.get(wallet,'{}'))
        require(amount>0 and previous.get('status')!='PENDING','no available credit or transfer pending')
        require(attempt==previous.get('attempt',0)+1,'next credit attempt required')
        require(int(self.balance)>=amount,'native funds unavailable')
        self.credit_claims[wallet]=json.dumps({'amount':str(amount),'attempt':attempt,'status':'PENDING','requested_at':now()})
        self.credits[wallet]=u256(0)
        self.accounted=u256(int(self.accounted)-amount)
        Recipient(Address(wallet)).emit_transfer(value=u256(amount),on='finalized')

    @gl.public.write
    def verify_claim(self,key: str,wallet: str,attempt: int,parent_hash: str,child_hash: str) -> None:
        wallet=str(Address(wallet)).lower()
        credit=key=='CREDIT'
        r={} if credit else json.loads(self.bets[key])
        claim=json.loads(self.credit_claims.get(wallet,'{}')) if credit else r['claims'].get(wallet)
        require(claim and claim['status']=='PENDING' and claim['attempt']==attempt,'matching pending claim required')
        contract=str(gl.message.contract_address).lower()
        def verify():
            parent,child=receipt(parent_hash),receipt(child_hash)
            require(parent.get('status_name',parent.get('status'))=='FINALIZED' and child.get('status_name',child.get('status'))=='FINALIZED','native child not final')
            require(str(parent.get('from_address','')).lower()==wallet and str(parent.get('to_address','')).lower()==contract,'parent origin mismatch')
            require(child_hash in parent.get('triggered_transactions',[]) and child.get('triggered_by')==parent_hash,'unrelated transfer')
            require(str(child.get('from_address','')).lower()==contract and str(child.get('to_address','')).lower()==wallet and int(child.get('value',0))==int(claim['amount']),'transfer fields mismatch')
            from genlayer.py import calldata
            data=parent.get('data',{}).get('calldata')
            decoded=data if isinstance(data,dict) else calldata.decode(base64.b64decode(data))
            expected=[attempt] if credit else [key,attempt]
            require(decoded.get('method')==('claim_credit' if credit else 'claim') and list(decoded.get('args',[]))==expected,'wrong claim attempt')
            return child.get('value_credited') is True
        paid=gl.eq_principle.strict_eq(verify)
        if not paid:self.accounted=u256(int(self.accounted)+int(claim['amount']))
        claim.update({'status':'PAID' if paid else 'FAILED','parent':parent_hash,'child':child_hash})
        if credit:
            self.credit_claims[wallet]=json.dumps(claim)
            if not paid:self.credits[wallet]=u256(int(self.credits.get(wallet,u256(0)))+int(claim['amount']))
        else:
            r['claims'][wallet]=claim
            self.bets[key]=json.dumps(r)

    @gl.public.write
    def recover_failed_deposit(self,parent_hash: str) -> None:
        require(not self.recovered.get(parent_hash,False),'failed deposit already recovered')
        contract=str(gl.message.contract_address).lower()
        def verify():
            r=receipt(parent_hash)
            require(r.get('status_name',r.get('status'))=='FINALIZED','finalized failed deposit required')
            leader=(r.get('consensus_data',{}).get('leader_receipt') or [{}])[0]
            require(leader.get('execution_result') not in (None,'SUCCESS','FINISHED_WITH_RETURN'),'failed execution required')
            require(r.get('value_credited') is True and int(r.get('value',0))>0,'actual native credit required')
            require(str(r.get('to_address','')).lower()==contract,'deposit recipient mismatch')
            from genlayer.py import calldata
            data=r.get('data',{}).get('calldata')
            decoded=data if isinstance(data,dict) else calldata.decode(base64.b64decode(data))
            require(decoded.get('method')=='deposit','only failed deposit calls recoverable')
            return {'wallet':str(Address(r['from_address'])).lower(),'amount':str(int(r['value']))}
        found=gl.eq_principle.strict_eq(verify)
        amount=int(found['amount'])
        require(int(self.balance)>=int(self.accounted)+amount,'unaccounted backing required')
        wallet=found['wallet']
        self.credits[wallet]=u256(int(self.credits.get(wallet,u256(0)))+amount)
        self.accounted=u256(int(self.accounted)+amount)
        self.recovered[parent_hash]=True

    @gl.public.view
    def get_bet(self,key: str) -> str:
        return self.bets.get(key,'{}')

    @gl.public.view
    def get_credit(self,wallet: str) -> dict:
        wallet=str(Address(wallet)).lower()
        return {'available_wei':str(int(self.credits.get(wallet,u256(0)))),'claim':json.loads(self.credit_claims.get(wallet,'{}'))}
