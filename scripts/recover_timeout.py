"""Inspect timeout readiness; --execute refunds only a genuinely eligible bet.

No clock changes, new deposits, alternative evidence or model retries. Every
write is journalled, uses zero value, and follows finality and native credits.
"""
import hashlib
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

from chain import ROOT, load, save, read, tx, client, signer
import chain

KEY = 'take-5'
EXPECTED_ESCROW = '0xC5BeB6B171f37f2c7101EDc83eA2905615415e12'


def select_revision_four():
    """Keep recovery bound to its own journal after a newer release is promoted."""
    current = load()
    if current.get('releaseAttempt') != 4 or '--revision-4' in sys.argv:
        isolated = ROOT / 'deploy/recovery-v4/proof.json'
        assert isolated.exists(), 'The isolated revision-4 recovery journal is required'
        chain.PROOF_RELATIVE = Path('deploy/recovery-v4/proof.json')
        current = load()
    assert current.get('releaseAttempt') == 4
    return current


def readiness(take, resolution, bet, at):
    deadline = int(take['evidence_deadline']) + 48 * 3600
    finalized = resolution.get('status') == 'FINAL'
    already_timeout = finalized and resolution.get('resolution_case') == 'VOID_TIMEOUT'
    return {
        'status': 'READY' if already_timeout or (not finalized and at >= deadline) else 'ALREADY_RESOLVED' if finalized else 'WAITING_FOR_CHAIN_DEADLINE',
        'eligible': already_timeout or (not finalized and at >= deadline),
        'resolverTimeoutUTC': datetime.fromtimestamp(deadline, timezone.utc).isoformat(),
        'resolverTimeoutLagos': datetime.fromtimestamp(deadline, timezone(timedelta(hours=1))).isoformat(),
        'escrowFallbackUTC': datetime.fromtimestamp(int(bet['refund_deadline']), timezone.utc).isoformat(),
        'secondsUntilResolverTimeout': max(0, deadline - int(at)),
        'newDepositsWei': 0,
    }


def balances(p, bet):
    addresses = {'author': bet['author'], 'counterparty': bet['counterparty'],
                 'escrow': p['contracts']['TakeEscrow']['address']}
    values = {}
    for label, address in addresses.items():
        value = client().provider.make_request('eth_getBalance', [address, 'latest'])['result']
        values[label] = str(int(value, 0) if isinstance(value, str) else int(value))
    return addresses, {'checkedAt': datetime.now(timezone.utc).isoformat(), 'balancesWei': values}


def recover(p, at=None, execute=False):
    assert p['releaseAttempt'] == 4 and sum(p['deposits'].values()) == 22
    contracts = p['contracts']
    assert contracts['TakeEscrow']['address'].lower() == EXPECTED_ESCROW.lower(), 'Recovery is bound to the original funded escrow'
    take = read(contracts['Takes']['address'], 'get_take', [KEY])
    resolution = read(contracts['TakeResolver']['address'], 'get_resolution', [KEY])
    bet = read(contracts['TakeEscrow']['address'], 'get_bet', [KEY])
    plan = readiness(take, resolution, bet, time.time() if at is None else at)
    plan.update(checkedAt=datetime.now(timezone.utc).isoformat(), executeRequested=execute,
                canonicalResolver=contracts['TakeResolver']['address'], escrow=contracts['TakeEscrow']['address'],
                originalFailedHash=p['transactions']['r4-resolve-take-5'],
                note='No transaction is sent before the actual timeout. --execute uses a new, explicit timeout label and never resubmits the failed judgment.')
    target = ROOT / 'deploy/timeout-recovery.json'
    target.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf8')
    if not execute or not plan['eligible']:
        print(plan['status'], 'resolver timeout:', plan['resolverTimeoutLagos'], flush=True)
        return plan

    for item in contracts.values():
        folder = 'deploy/releases/v4/contracts' if chain.PROOF_RELATIVE != Path('deploy/proof.json') else 'contracts'
        assert hashlib.sha256((ROOT / folder / item['source']).read_bytes()).hexdigest() == item['sha256']
    assert bet.get('counterparty') and bet['total'] == '2'
    addresses, before = balances(p, bet)
    if 'nativeBalanceProof' not in p:
        p['nativeBalanceProof'] = {'addresses': addresses, 'before': before}
        save(p)
    assert p['nativeBalanceProof']['addresses'] == addresses, 'Native proof must identify these same wallets and escrow'

    if resolution.get('status') != 'FINAL':
        tx(p, 'r4-timeout-resolve-' + KEY, contracts['TakeResolver']['address'], 'resolve', [KEY], value=0)
        resolution = read(contracts['TakeResolver']['address'], 'get_resolution', [KEY])
    assert resolution['status'] == 'FINAL' and resolution['outcome'] == 'VOID' and resolution['resolution_case'] == 'VOID_TIMEOUT'
    assert resolution['rule_hash'] == take['rule_hash'] == bet['rule_hash']
    if bet['status'] != 'SETTLED':
        tx(p, 'r4-settle-' + KEY, contracts['TakeEscrow']['address'], 'settle', [KEY], value=0)
        bet = read(contracts['TakeEscrow']['address'], 'get_bet', [KEY])
    assert bet['status'] == 'SETTLED' and bet['resolution_case'] == 'VOID_TIMEOUT'
    assert bet['payouts'] == bet['deposits'] and sum(map(int, bet['payouts'].values())) == 2

    for index in range(2):
        wallet = signer(index).address.lower()
        assert bet['payouts'][wallet] == '1'
        claim = bet.get('claims', {}).get(wallet, {})
        if claim.get('status') == 'PAID':
            continue
        assert claim.get('status') in (None, 'PENDING'), 'Failed native transfer requires separate review; no automatic second claim'
        label = 'r4-claim-' + KEY + '-' + str(index)
        receipt = tx(p, label, contracts['TakeEscrow']['address'], 'claim', [KEY, 1], index=index, value=0)
        children = receipt.get('triggered_transactions') or []
        assert len(children) == 1
        tx(p, 'r4-verify-' + KEY + '-' + str(index), contracts['TakeEscrow']['address'],
           'verify_claim', [KEY, wallet, 1, p['transactions'][label], children[0]], index=index, value=0)
        bet = read(contracts['TakeEscrow']['address'], 'get_bet', [KEY])
        assert bet['claims'][wallet]['status'] == 'PAID' and bet['claims'][wallet]['amount'] == '1'

    tx(p, 'r4-record-' + KEY, contracts['CalledItRecord']['address'], 'sync', [KEY], value=0)
    for entry in p['takes']:
        if entry['take']['id'] == KEY:
            entry.update(take=take, resolution=resolution, bet=bet)
    p['profiles'] = [read(contracts['CalledItRecord']['address'], 'get_profile', [signer(i).address]) for i in range(2)]
    _, after = balances(p, bet)
    proof = p['nativeBalanceProof']
    proof['after'] = after
    initial = proof['before']['balancesWei']; final = after['balancesWei']
    proof['checks'] = [
        {'wallet': 'author', 'passed': int(final['author']) - int(initial['author']) == 1},
        {'wallet': 'counterparty', 'passed': int(final['counterparty']) - int(initial['counterparty']) == 1},
        {'wallet': 'escrow', 'passed': int(initial['escrow']) - int(final['escrow']) == 2},
    ]
    proof['passed'] = all(item['passed'] for item in proof['checks'])
    p['recordedAt'] = datetime.now(timezone.utc).isoformat()
    save(p)
    (ROOT / chain.PROOF_RELATIVE.parent / 'native-balance-proof.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf8')
    assert proof['passed'], 'Native balance differences do not match both original stakes; STOP'
    plan.update(status='RECOVERED_VERIFIED_REFUND', refundWeiEach='1', nativeBalancesPassed=True,
                releaseVerified=False, note='Timeout refund proven; full release audit and production publication remain separate checks.')
    target.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf8')
    print('TIMEOUT_VOID: both original stakes refunded with verified native credits.', flush=True)
    return plan


if __name__ == '__main__':
    try:
        recover(select_revision_four(), execute='--execute' in sys.argv)
    except Exception as error:
        target = ROOT / 'deploy/timeout-recovery.json'
        report = json.loads(target.read_text()) if target.exists() else {}
        report.update(status='PENDING_SAVED_HASH' if str(error).startswith('Still pending; resume saved hash') else 'STOPPED_RECOVERY_FAILURE',
                      error=type(error).__name__ + ': ' + str(error), releaseVerified=False)
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
        raise
