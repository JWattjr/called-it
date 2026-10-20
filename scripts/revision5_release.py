"""Revision 5: configured v2 judge, five real replays and one approved 1+1 bet.

Each durable r5 label resumes its saved hash; finalized failures stop the run.
Revision-4 archives, receipts and isolated recovery journal are never written.
"""
import base64
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone

from genlayer_py.abi.calldata import decode
from chain import ROOT, load, save, tx, read, signer, client, journal_lock

PREFIX = 'r5-'
FILES = {'Takes': 'takes.py', 'TakeEscrow': 'take_escrow.py',
         'TakeResolver': 'take_resolver.py', 'CalledItRecord': 'called_it_record.py'}


def stamp(value):
    return int(datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp())


CASES = [
    {'label': 'official-yes', 'text': 'Apple officially announces Apple Vision Pro.', 'category': 'tech', 'as_of': stamp('2023-06-03T00:00:00Z'), 'deadline': stamp('2023-06-06T23:59:59Z'), 'evidence': 'https://web.archive.org/web/20230605190503id_/https://www.apple.com/newsroom/2023/06/introducing-apple-vision-pro/', 'outcome': 'YES', 'case': 'JUDGED_YES'},
    {'label': 'rumours-no', 'text': 'Nintendo officially reveals its next console under the retail name Nintendo Switch 2.', 'category': 'tech', 'as_of': stamp('2025-01-01T00:00:00Z'), 'deadline': stamp('2025-01-09T23:59:59Z'), 'evidence': 'https://en.wikipedia.org/w/index.php?title=Nintendo_Switch_2&oldid=1268215322', 'outcome': 'NO', 'case': 'JUDGED_NO'},
    {'label': 'no-evidence-default', 'text': 'Apple officially announces a foldable iPhone.', 'category': 'tech', 'as_of': stamp('2025-01-01T00:00:00Z'), 'deadline': stamp('2025-01-09T23:59:59Z'), 'outcome': 'NO', 'case': 'DEFAULT_NO_EVIDENCE'},
    {'label': 'subjective-rejection', 'text': "Apple's next headset will be a flop.", 'category': 'tech', 'as_of': stamp('2025-01-01T00:00:00Z'), 'deadline': stamp('2025-01-09T23:59:59Z')},
    {'label': 'scheduling-void', 'text': 'The Recording Academy officially announces the nominations for the 67th GRAMMY Awards.', 'category': 'entertainment', 'as_of': stamp('2024-11-01T00:00:00Z'), 'deadline': stamp('2024-11-10T23:59:59Z'), 'evidence': 'https://web.archive.org/web/20241108004348id_/https://www.grammy.com/news/2025-grammys-nominations-full-winners-nominees-list', 'outcome': 'VOID', 'case': 'VOID_INSUFFICIENT_EVIDENCE'},
]


def address(p, name):
    return p['contracts'][name]['address']


def write(p, label, name, method, args, index=0, value=0):
    if value:
        assert label in ('deposit-author-take-1', 'deposit-counter-take-1') and value == 1
    return tx(p, PREFIX + label, address(p, name), method, args, index=index, value=value)


def record(p, keys=None):
    entries = []
    ids = read(address(p, 'Takes'), 'get_ids', [0, 100]) if keys is None else keys
    for key in ids:
        take = read(address(p, 'Takes'), 'get_take', [key])
        case = next(item for item in CASES if item['text'] == take['text'])
        entries.append({'take': take, 'label': case['label'],
                        'bet': read(address(p, 'TakeEscrow'), 'get_bet', [key]),
                        'resolution': read(address(p, 'TakeResolver'), 'get_resolution', [key])})
    if keys is not None:
        refreshed = {entry['take']['id']: entry for entry in entries}
        entries = [refreshed.get(entry['take']['id'], entry) for entry in p['takes']]
    p.update(takes=entries, profiles=[read(address(p, 'CalledItRecord'), 'get_profile', [signer(i).address]) for i in range(2)], recordedAt=datetime.now(timezone.utc).isoformat())
    save(p)


def initialize(p):
    if p.get('releaseAttempt') == 5:
        return
    assert p['releaseAttempt'] == 4 and sum(p['deposits'].values()) == 22
    archived = json.loads((ROOT / 'deploy/releases/v4-proof.json').read_text())
    assert archived == p, 'Revision-4 archive must exactly preserve the previous proof'
    p.setdefault('previousReleases', []).append({'attempt': 4, 'contracts': p['contracts'], 'proof': 'deploy/releases/v4-proof.json', 'reason': 'Preserved original revision-4 failure and scheduled isolated timeout recovery.'})
    for entry in p['takes']:
        if entry['bet'].get('status') == 'MATCHED':
            p.setdefault('previousUnsettledBets', []).append({'attempt': 4, 'contracts': p['contracts'], 'entry': entry})
    p.setdefault('expectedFailures', {})['r4-resolve-take-5'] = 'CONSENSUS_DISAGREEMENT'
    p.update(releaseAttempt=5, deploymentPrefix=PREFIX, contracts={}, takes=[], profiles=[],
             releaseStatus='IN_PROGRESS', blockers=['Revision 5 live proofs and publication in progress.'],
             sourceCommit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
             judgeImplementation='Exact v2 ordered four-step judge and archive capture-time block, promoted into the configured resolver without diagnostic output.',
             approvedDepositBudgetWei=24)
    for key in ('nativeBalanceProof', 'recordedAt', 'stopFailure', 'failedResolutionAttempts', 'authorizedRecovery'):
        p.pop(key, None)
    p['unreachableProof'] = {'proven': False, 'actualCase': 'NOT_DEMONSTRATED', 'note': 'Grammy readable scheduling VOID is not an unreachable-source proof. Owner approved honest reporting when an unlisted host is reachable.'}
    with journal_lock('proof'):
        (ROOT / 'deploy/proof.json').write_text(json.dumps(p, indent=2) + '\n', encoding='utf8')
    (ROOT / 'deploy/proof-verification.json').write_text(json.dumps({'passed': False, 'complete': False, 'failures': ['Revision 5 not yet audited.']}) + '\n')


def native_snapshot(p):
    addresses = {'author': signer(0).address.lower(), 'counterparty': signer(1).address.lower(), 'escrow': address(p, 'TakeEscrow')}
    values = {}
    for name, wallet in addresses.items():
        value = client().provider.make_request('eth_getBalance', [wallet, 'latest'])['result']
        values[name] = str(int(value, 0) if isinstance(value, str) else int(value))
    return addresses, {'checkedAt': datetime.now(timezone.utc).isoformat(), 'balancesWei': values}


def resolve(p, plans):
    for case in plans:
        key = 'take-' + str(CASES.index(case) + 1)
        entry = next(e for e in p['takes'] if e['take']['id'] == key)
        bet = entry['bet']
        result = read(address(p, 'TakeResolver'), 'get_resolution', [key])
        if result.get('status') != 'FINAL':
            write(p, 'seal-author-' + key, 'TakeResolver', 'seal_evidence', [key])
            bet = read(address(p, 'TakeEscrow'), 'get_bet', [key])
            if bet.get('counterparty'):
                write(p, 'seal-counter-' + key, 'TakeResolver', 'seal_evidence', [key], index=1)
            write(p, 'resolve-' + key, 'TakeResolver', 'resolve', [key])
            result = read(address(p, 'TakeResolver'), 'get_resolution', [key])
        assert result['status'] == 'FINAL' and result['outcome'] == case['outcome'] and result['resolution_case'] == case['case'], 'Unexpected ruling; STOP: ' + key + ' ' + json.dumps(result)
        take = read(address(p, 'Takes'), 'get_take', [key])
        assert result['rule_hash'] == take['rule_hash']
        entry.update(take=take, resolution=result, bet=bet)
        print(key, result['outcome'], result['resolution_case'], 'FINALIZED_READBACK', flush=True)
    p['recordedAt'] = datetime.now(timezone.utc).isoformat()
    save(p)


def main(stage):
    p = load()
    try:
        if stage == 'init':
            initialize(p)
            return
        assert p['releaseAttempt'] == 5
        # A state may already be FINAL even if the previous poller stopped
        # before saving its RPC receipt. Follow every known parent/child first.
        for label in list(p['transactions']):
            if label.startswith(PREFIX) and '-child-' not in label:
                tx(p, label, value=0)
        if stage == 'deploy':
            for name, file in FILES.items():
                code = (ROOT / 'contracts' / file).read_bytes()
                digest = hashlib.sha256(code).hexdigest()
                if name not in p['contracts']:
                    receipt = tx(p, PREFIX + 'deploy-' + name, code=code.decode(), args=[] if name == 'Takes' else [address(p, 'Takes')])
                    p['contracts'][name] = {'address': receipt.get('recipient', receipt.get('to_address')), 'source': file, 'sha256': digest}
                    save(p)
                assert p['contracts'][name]['sha256'] == digest
                actual = client().provider.make_request('gen_getContractCode', [address(p, name)])['result']
                assert hashlib.sha256(base64.b64decode(actual)).hexdigest() == digest
            write(p, 'configure', 'Takes', 'configure', [address(p, n) for n in ('TakeResolver', 'TakeEscrow', 'CalledItRecord')])
            config = read(address(p, 'Takes'), 'get_config')
            assert all(config[k].lower() == address(p, n).lower() for k, n in [('resolver', 'TakeResolver'), ('escrow', 'TakeEscrow'), ('record', 'CalledItRecord')])
        elif stage == 'compile':
            for i, case in enumerate(CASES):
                write(p, 'compile-' + case['label'], 'Takes', 'compile', [case['text'], case['category'], case['deadline'], 1, 1, 'NO', case['as_of']])
                take = read(address(p, 'Takes'), 'get_take', ['take-' + str(i + 1)])
                assert take['status'] == ('REJECTED' if case['label'] == 'subjective-rejection' else 'COMPILED'), 'Unexpected compilation; STOP'
            record(p)
        elif stage == 'evidence':
            for i, case in enumerate(CASES):
                if case.get('evidence'):
                    write(p, 'evidence-take-' + str(i + 1), 'TakeResolver', 'submit_evidence', ['take-' + str(i + 1), case['evidence'], 'Apply only the frozen rule and supplied immutable evidence.'])
            record(p)
        elif stage == 'resolve-grammy':
            resolve(p, [CASES[4]])
        elif stage == 'fund':
            key = 'take-1'
            write(p, 'prepare-' + key, 'TakeEscrow', 'prepare_open', [key])
            write(p, 'deposit-author-' + key, 'TakeEscrow', 'deposit', [key], value=1)
            write(p, 'accept-' + key, 'TakeEscrow', 'prepare_accept', [key], index=1)
            write(p, 'deposit-counter-' + key, 'TakeEscrow', 'deposit', [key], index=1, value=1)
            bet = read(address(p, 'TakeEscrow'), 'get_bet', [key])
            assert bet['status'] == 'MATCHED' and bet['total'] == '2'
            if 'nativeBalanceProof' not in p:
                addresses, before = native_snapshot(p)
                p['nativeBalanceProof'] = {'takeId': key, 'addresses': addresses, 'before': before}
                save(p)
            record(p)
        elif stage == 'resolve':
            resolve(p, CASES[:3] + [CASES[4]])
        elif stage == 'settle':
            key = 'take-1'
            bet = read(address(p, 'TakeEscrow'), 'get_bet', [key])
            if bet['status'] != 'SETTLED':
                write(p, 'settle-' + key, 'TakeEscrow', 'settle', [key])
                bet = read(address(p, 'TakeEscrow'), 'get_bet', [key])
            author = signer(0).address.lower()
            assert bet['status'] == 'SETTLED' and bet['outcome'] == 'YES' and bet['payouts'] == {author: '2'}
            if bet['claims'].get(author, {}).get('status') != 'PAID':
                receipt = write(p, 'claim-take-1-0', 'TakeEscrow', 'claim', [key, 1])
                children = receipt.get('triggered_transactions') or []
                assert len(children) == 1
                write(p, 'verify-take-1-0', 'TakeEscrow', 'verify_claim', [key, author, 1, p['transactions']['r5-claim-take-1-0'], children[0]])
            write(p, 'record-' + key, 'CalledItRecord', 'sync', [key])
            record(p, keys=[key])
            bet = next(e['bet'] for e in p['takes'] if e['take']['id'] == key)
            assert bet['claims'][author]['status'] == 'PAID'
            _, after = native_snapshot(p)
            proof = p['nativeBalanceProof']; proof['after'] = after
            before = proof['before']['balancesWei']; final = after['balancesWei']
            proof['checks'] = [{'wallet': wallet, 'passed': int(final[wallet]) - int(before[wallet]) == delta} for wallet, delta in [('author', 2), ('counterparty', 0), ('escrow', -2)]]
            proof['passed'] = all(c['passed'] for c in proof['checks'])
            assert proof['passed'], 'Exact native payout balances failed; STOP'
            p.update(releaseStatus='LIVE_PROOFS_PASSED_AWAITING_PUBLICATION', blockers=['Complete publication audit and production verification remain pending.'])
            p['unreachableProof']['actualCase'] = 'VOID_INSUFFICIENT_EVIDENCE'
            save(p)
            (ROOT / 'deploy/native-balance-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
        elif stage == 'record':
            record(p)
        else:
            raise ValueError('Unknown stage')
    except Exception as error:
        p['releaseStatus'] = 'PENDING_SAVED_HASH' if str(error).startswith('Still pending; resume saved hash') else 'STOPPED_REVISION_5_FAILURE'
        leaders = []
        for label, h in p.get('transactions', {}).items():
            if not label.startswith(PREFIX): continue
            path = ROOT / 'deploy/receipts' / (label + '.json')
            if not path.exists(): continue
            receipt = json.loads(path.read_text())
            if receipt.get('result_name') != 'MAJORITY_DISAGREE': continue
            for round in receipt.get('consensus_history', {}).get('consensus_results', []):
                for leader in round.get('leader_result', []):
                    if leader.get('mode') == 'leader':
                        outputs = leader.get('eq_outputs', {})
                        proposal = decode(base64.b64decode(outputs['0'])[1:]) if outputs.get('0') else outputs
                        leaders.append({'label': label, 'hash': h, 'output': proposal, 'execution': leader.get('execution_result')})
        p['stopFailure'] = {'error': str(error), 'leaderOutputs': leaders}
        save(p)
        print(json.dumps(p['stopFailure'], indent=2), flush=True)
        raise


if __name__ == '__main__':
    main(sys.argv[1])
