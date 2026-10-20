import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def setup(tmp_path, monkeypatch):
    spec=importlib.util.spec_from_file_location('polling_chain',Path('scripts/chain.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m,'ROOT',tmp_path)
    monkeypatch.setattr(m.time,'sleep',lambda _:None)
    (tmp_path/'deploy/receipts').mkdir(parents=True)
    return m


def test_pending_explorer_hints_do_not_spend_rpc_until_finality(tmp_path,monkeypatch):
    m=setup(tmp_path,monkeypatch);h='0x'+'ab'*32
    states=iter(['PENDING','ACCEPTED','FINALIZED']);calls=[]
    monkeypatch.setattr(m.provider.requests,'get',lambda *a,**kw:SimpleNamespace(status_code=200,json=lambda:{'hash':h,'status':next(states)}))
    receipt={'hash':h,'status':'FINALIZED','type':0,'value_credited':True}
    def rpc(method,args):calls.append((method,args));return {'result':receipt}
    assert m.final(SimpleNamespace(provider=SimpleNamespace(make_request=rpc)),h,'saved',seconds=40)==receipt
    assert calls==[('eth_getTransactionByHash',[h])]
    assert json.loads((tmp_path/'deploy/receipts/saved.json').read_text())==receipt


def test_wrong_explorer_hash_cannot_trigger_rpc_or_a_false_success(tmp_path,monkeypatch):
    m=setup(tmp_path,monkeypatch);h='0x'+'ab'*32
    monkeypatch.setattr(m.provider.requests,'get',lambda *a,**kw:SimpleNamespace(status_code=200,json=lambda:{'hash':'0x'+'cd'*32,'status':'FINALIZED'}))
    def rpc(*a):raise AssertionError('Wrong hash must never trigger RPC')
    with pytest.raises(RuntimeError,match='Still pending; resume saved hash'):
        m.final(SimpleNamespace(provider=SimpleNamespace(make_request=rpc)),h,'saved',seconds=10)
    assert not (tmp_path/'deploy/receipts/saved.json').exists()


def test_native_credit_is_confirmed_by_rpc_and_never_by_explorer_hint(tmp_path,monkeypatch):
    m=setup(tmp_path,monkeypatch);h='0x'+'ab'*32
    monkeypatch.setattr(m.provider.requests,'get',lambda *a,**kw:SimpleNamespace(status_code=200,json=lambda:{'hash':h,'status':'FINALIZED','value_credited':True}))
    receipt={'hash':h,'status':'FINALIZED','type':0,'value_credited':False}
    c=SimpleNamespace(provider=SimpleNamespace(make_request=lambda *a:{'result':receipt}))
    with pytest.raises(RuntimeError,match='Finalized execution error'):
        m.final(c,h,'saved',seconds=10)
    assert json.loads((tmp_path/'deploy/receipts/saved.json').read_text())['value_credited'] is False


def test_cached_rpc_success_needs_no_poll_or_resubmission(tmp_path,monkeypatch):
    m=setup(tmp_path,monkeypatch);h='0x'+'ab'*32
    receipt={'hash':h,'status':'FINALIZED','type':0,'value_credited':True}
    (tmp_path/'deploy/receipts/saved.json').write_text(json.dumps(receipt))
    def request(*a,**kw):raise AssertionError('Cached success must not make a request')
    monkeypatch.setattr(m.provider.requests,'get',request)
    assert m.final(SimpleNamespace(provider=SimpleNamespace(make_request=request)),h,'saved')==receipt
