import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path('scripts').resolve()))
import recover_timeout as recovery

A = '0x' + '1' * 40
B = '0x' + '2' * 40


@pytest.mark.parametrize('status', ['OPEN', 'RESOLVING'])
@pytest.mark.parametrize('offset,eligible', [(-1, False), (0, True)])
def test_real_48_hour_boundary_is_required(status, offset, eligible):
    plan = recovery.readiness({'evidence_deadline': 100000}, {'status': status},
                              {'refund_deadline': 100000 + 49 * 3600}, 100000 + 48 * 3600 + offset)
    assert plan['eligible'] is eligible


@pytest.fixture
def fake_chain(tmp_path, monkeypatch):
    (tmp_path / 'deploy').mkdir()
    (tmp_path / 'contracts').mkdir()
    code = b'# fixture for release transport tests\n'
    (tmp_path / 'contracts/test.py').write_bytes(code)
    names = ('Takes', 'TakeResolver', 'TakeEscrow', 'CalledItRecord')
    contracts = {name: {'address': name, 'source': 'test.py', 'sha256': hashlib.sha256(code).hexdigest()} for name in names}
    take = {'id': 'take-5', 'evidence_deadline': 100000, 'rule_hash': 'frozen'}
    resolution = {'status': 'OPEN', 'outcome': None, 'rule_hash': 'frozen'}
    bet = {'id': 'take-5', 'author': A, 'counterparty': B, 'status': 'MATCHED', 'total': '2',
           'deposits': {A: '1', B: '1'}, 'payouts': {}, 'claims': {},
           'refund_deadline': 100000 + 49 * 3600, 'rule_hash': 'frozen'}
    native = {A: 6, B: 6, 'TakeEscrow': 2}
    p = {'releaseAttempt': 4, 'deposits': {'historical': 22}, 'contracts': contracts,
         'transactions': {'r4-resolve-take-5': 'original-failed-hash'},
         'takes': [{'take': take.copy(), 'resolution': resolution.copy(), 'bet': bet.copy()}]}
    writes = []

    def read(address, method, args):
        value = {'get_take': take, 'get_resolution': resolution, 'get_bet': bet,
                 'get_profile': {'wallet': args[0], 'history': [{'resolution_case': 'VOID_TIMEOUT'}]}}[method]
        return json.loads(json.dumps(value))

    def tx(proof, label, address, method, args, index=0, value=0):
        assert value == 0
        if label in proof['transactions']:
            return {'triggered_transactions': ['native-' + str(index)]}
        writes.append((method, index)); proof['transactions'][label] = label
        if method == 'resolve':
            resolution.update(status='FINAL', outcome='VOID', resolution_case='VOID_TIMEOUT')
        elif method == 'settle':
            bet.update(status='SETTLED', outcome='VOID', resolution_case='VOID_TIMEOUT', payouts=bet['deposits'].copy())
        elif method == 'claim':
            wallet = (A, B)[index]
            assert not bet['claims'].get(wallet)
            bet['claims'][wallet] = {'status': 'PENDING', 'amount': '1'}
            native[wallet] += 1; native['TakeEscrow'] -= 1
        elif method == 'verify_claim':
            bet['claims'][args[1]]['status'] = 'PAID'
        return {'triggered_transactions': ['native-' + str(index)] if method == 'claim' else []}

    def request(method, args):
        assert method == 'eth_getBalance'
        return {'result': hex(native[args[0]])}

    monkeypatch.setattr(recovery, 'ROOT', tmp_path)
    monkeypatch.setattr(recovery, 'EXPECTED_ESCROW', 'TakeEscrow')
    monkeypatch.setattr(recovery, 'read', read)
    monkeypatch.setattr(recovery, 'tx', tx)
    monkeypatch.setattr(recovery, 'save', lambda proof: None)
    monkeypatch.setattr(recovery, 'signer', lambda index: SimpleNamespace(address=(A, B)[index]))
    monkeypatch.setattr(recovery, 'client', lambda: SimpleNamespace(provider=SimpleNamespace(make_request=request)))
    return p, writes, native, resolution, bet


def test_premature_execute_sends_no_transaction(fake_chain):
    p, writes, *_ = fake_chain
    plan = recovery.recover(p, at=100000 + 48 * 3600 - 1, execute=True)
    assert plan['status'] == 'WAITING_FOR_CHAIN_DEADLINE'
    assert writes == [] and 'nativeBalanceProof' not in p


def test_timeout_refunds_one_each_and_resume_never_claims_twice(fake_chain):
    p, writes, native, _, bet = fake_chain
    first = recovery.recover(p, at=100000 + 48 * 3600, execute=True)
    assert first['status'] == 'RECOVERED_VERIFIED_REFUND'
    assert native == {A: 7, B: 7, 'TakeEscrow': 0}
    assert bet['payouts'] == bet['deposits']
    assert all(c['status'] == 'PAID' for c in bet['claims'].values())
    assert p['nativeBalanceProof']['passed']
    count = len(writes)
    recovery.recover(p, at=100000 + 48 * 3600 + 1, execute=True)
    assert len(writes) == count
    assert [method for method, _ in writes].count('claim') == 2


def test_final_judged_outcome_is_not_overwritten_by_timeout(fake_chain):
    p, writes, _, resolution, _ = fake_chain
    resolution.update(status='FINAL', outcome='YES', resolution_case='JUDGED_YES')
    plan = recovery.recover(p, at=100000 + 50 * 3600, execute=True)
    assert plan['status'] == 'ALREADY_RESOLVED' and writes == []


def test_first_failed_native_claim_stops_before_other_wallet_or_record(fake_chain, monkeypatch):
    p, writes, _, _, _ = fake_chain
    original = recovery.tx

    def fail_claim(*args, **kwargs):
        if args[3] == 'claim':
            raise RuntimeError('Finalized claim error')
        return original(*args, **kwargs)

    monkeypatch.setattr(recovery, 'tx', fail_claim)
    with pytest.raises(RuntimeError, match='Finalized claim error'):
        recovery.recover(p, at=100000 + 48 * 3600, execute=True)
    assert [method for method, _ in writes] == ['resolve', 'settle']


def test_revision_five_selects_only_the_isolated_original_recovery(tmp_path, monkeypatch):
    import chain
    (tmp_path/'deploy/recovery-v4').mkdir(parents=True)
    main={'releaseAttempt':5,'contracts':{'TakeEscrow':{'address':'new-release'}}}
    original={'releaseAttempt':4,'contracts':{'TakeEscrow':{'address':recovery.EXPECTED_ESCROW}}}
    (tmp_path/'deploy/proof.json').write_text(json.dumps(main))
    (tmp_path/'deploy/recovery-v4/proof.json').write_text(json.dumps(original))
    monkeypatch.setattr(chain,'ROOT',tmp_path)
    monkeypatch.setattr(chain,'PROOF_RELATIVE',Path('deploy/proof.json'))
    monkeypatch.setattr(recovery,'ROOT',tmp_path)
    selected=recovery.select_revision_four()
    assert selected==original and chain.PROOF_RELATIVE==Path('deploy/recovery-v4/proof.json')
    assert json.loads((tmp_path/'deploy/proof.json').read_text())==main
