import importlib.util
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def module():
    spec=importlib.util.spec_from_file_location('called_it_chain',Path('scripts/chain.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_stale_workers_preserve_transaction_hashes_and_newer_state(tmp_path,monkeypatch):
    m=module();monkeypatch.setattr(m,'ROOT',tmp_path)
    (tmp_path/'deploy').mkdir()
    a={'transactions':{'a':'0xaaa'},'recordedAt':'2026-10-18T12:00:00Z','takes':[1],'profiles':[],'demoWallets':[]}
    b={'transactions':{'b':'0xbbb'},'recordedAt':'2026-10-18T13:00:00Z','takes':[1,2],'profiles':[],'demoWallets':[]}
    m.save(b);m.save(a)
    saved=json.loads((tmp_path/'deploy/proof.json').read_text())
    assert saved['transactions']=={'a':'0xaaa','b':'0xbbb'} and saved['takes']==[1,2]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(m.save,[{'transactions':{str(i):str(i)}} for i in range(12)]))
    saved=json.loads((tmp_path/'deploy/proof.json').read_text())
    assert len(saved['transactions'])==14

def test_failed_payable_credit_is_not_execution_success():
    m=module()
    failed={'status':'FINALIZED','type':2,'value_credited':True,'consensus_data':{'leader_receipt':[{'execution_result':'ERROR'}]},'result_name':'AGREE'}
    assert not m.success(failed)
    assert m.success({'status':'FINALIZED','type':0,'value_credited':True,'consensus_data':None})
    assert m.success({'status':'FINALIZED','type':0,'value_credited':True,'consensus_data':None,'result_name':'NO_MAJORITY'})

def test_concurrent_retries_submit_one_hash_and_value_budget_is_atomic(tmp_path,monkeypatch):
    import time
    m=module();monkeypatch.setattr(m,'ROOT',tmp_path)
    (tmp_path/'deploy').mkdir();(tmp_path/'.secrets').mkdir()
    (tmp_path/'.secrets/deposit-approval.json').write_text('{"approvedTotalWei":20}')
    calls=[]
    class Client:
        def write_contract(self,*args,**kwargs):
            time.sleep(.03);calls.append(kwargs['value']);return '0x'+'ab'*32
    monkeypatch.setattr(m,'client',lambda index=0:Client())
    monkeypatch.setattr(m,'fees',lambda c:{'feeValue':0})
    m.save({'transactions':{}})
    def same(_):return m.tx({'transactions':{}},'same','0x'+'11'*20,'deposit',['take-1'],value=12,wait=False)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(same,range(3)))
    assert calls==[12] and sum(m.load()['deposits'].values())==12
    try:m.tx(m.load(),'over-budget','0x'+'11'*20,'deposit',['take-2'],value=12,wait=False)
    except RuntimeError as e:assert 'budget exhausted' in str(e)
    else:raise AssertionError('Cumulative deposit ceiling must be enforced')
    assert calls==[12]

def test_lost_broadcast_response_blocks_duplicate_value_submission(tmp_path,monkeypatch):
    m=module();monkeypatch.setattr(m,'ROOT',tmp_path)
    (tmp_path/'deploy').mkdir();(tmp_path/'.secrets').mkdir()
    (tmp_path/'.secrets/deposit-approval.json').write_text('{"approvedTotalWei":20}')
    calls=[]
    def lost_response(*args,**kwargs):raise m.provider.requests.exceptions.ConnectionError('Response lost after broadcast')
    monkeypatch.setattr(m,'_post',lost_response)
    class Client:
        def write_contract(self,*args,**kwargs):
            calls.append(kwargs['value'])
            return m.browser_post('https://studio.genlayer.com/api',json={'method':'eth_sendRawTransaction','params':['0xdead']})
    monkeypatch.setattr(m,'client',lambda index=0:Client())
    monkeypatch.setattr(m,'fees',lambda c:{'feeValue':0})
    m.save({'transactions':{}})
    try:m.tx(m.load(),'lost-response','0x'+'11'*20,'deposit',['take-1'],value=1,wait=False)
    except m.provider.requests.exceptions.ConnectionError:pass
    else:raise AssertionError('The missing response must stop the caller')
    try:m.tx(m.load(),'lost-response','0x'+'11'*20,'deposit',['take-1'],value=1,wait=False)
    except RuntimeError as error:assert 'Broadcast outcome is unknown' in str(error)
    else:raise AssertionError('A retry must never send a second payable call')
    assert calls==[1] and sum(m.load()['deposits'].values())==1
