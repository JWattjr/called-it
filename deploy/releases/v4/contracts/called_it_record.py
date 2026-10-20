# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Public records, derived only from finalized matched escrow settlements. No LLM."""
import json
from genlayer import *

def require(ok,message):
    if not ok:raise gl.vm.UserError('[EXPECTED] '+message)

def empty(wallet):
    return {'wallet':wallet,'wins':0,'losses':0,'voids':0,'streak':0,'categories':{},'history':[]}

class CalledItRecord(gl.Contract):
    takes: Address
    profiles: TreeMap[str,str]
    recorded: TreeMap[str,bool]
    wallets: DynArray[str]

    def __init__(self,takes: str):
        self.takes=Address(takes)

    @gl.public.write
    def sync(self,key: str) -> None:
        require(not self.recorded.get(key,False),'already recorded')
        source=gl.get_contract_at(self.takes).view()
        t=json.loads(source.get_take(key))
        config=source.get_config()
        b=json.loads(gl.get_contract_at(Address(config['escrow'])).view().get_bet(key))
        require(t.get('status')=='COMPILED' and b.get('status')=='SETTLED' and b.get('counterparty'),'finalized matched settlement required')
        require(t['rule_hash']==b['rule_hash'] and b.get('outcome') in ('YES','NO','VOID'),'rule or outcome mismatch')
        self.recorded[key]=True
        payload={'id':key,'category':t['category'],'historical':t['historical'],'outcome':b['outcome'],'author':b['author'],'counterparty':b['counterparty'],'rule_hash':t['rule_hash'],'resolution_case':b.get('resolution_case','LEGACY')}
        gl.get_contract_at(gl.message.contract_address).emit(on='finalized').finalize_record(json.dumps(payload))

    @gl.public.write
    def finalize_record(self,payload: str) -> None:
        require(gl.message.sender_address==gl.message.contract_address,'self finality callback only')
        t=json.loads(payload)
        for wallet in (t['author'],t['counterparty']):
            p=json.loads(self.profiles.get(wallet,json.dumps(empty(wallet))))
            if t['id'] in [h['id'] for h in p['history']]:continue
            if wallet not in self.profiles:self.wallets.append(wallet)
            win=t['outcome']=='YES' and wallet==t['author'] or t['outcome']=='NO' and wallet==t['counterparty']
            result='VOID' if t['outcome']=='VOID' else 'WIN' if win else 'LOSS'
            stat='voids' if result=='VOID' else 'wins' if win else 'losses'
            p[stat]+=1
            if result!='VOID':p['streak']=max(0,p['streak'])+1 if win else min(0,p['streak'])-1
            category=p['categories'].setdefault(t['category'],{'wins':0,'losses':0,'voids':0})
            category[stat]+=1
            p['history'].append({'id':t['id'],'result':result,'historical':t['historical'],'category':t['category'],'resolution_case':t.get('resolution_case','LEGACY')})
            self.profiles[wallet]=json.dumps(p)

    @gl.public.view
    def get_profile(self,wallet: str) -> str:
        wallet=str(Address(wallet)).lower()
        return self.profiles.get(wallet,json.dumps(empty(wallet)))

    @gl.public.view
    def get_leaderboard(self) -> list[str]:
        return [self.profiles[w] for w in self.wallets[:100]]
