"""Unfunded, isolated replay; cannot reconfigure or settle the canonical escrow.

Every write uses value=0 and a durable diagnostic label. Polling resumes the
saved hash. A finalized failure stops immediately; there is no retry loop.
"""
import base64
import hashlib
import json
import sys
from datetime import datetime, timezone

from genlayer_py.abi.calldata import decode
from chain import ROOT, load, save, tx, read, client

VERSION = 2 if '--candidate-v2' in sys.argv else 1
PREFIX = 'diagnostic-schedule-v' + str(VERSION) + '-'
CANDIDATE = ROOT / ('diagnostics/consensus_candidate_v2.py' if VERSION == 2 else 'diagnostics/consensus_candidate.py')
REPORT = ROOT / 'deploy/consensus-diagnostics.json'


def persist(p, diagnostic):
    diagnostic['updatedAt'] = datetime.now(timezone.utc).isoformat()
    p['consensusDiagnostics'] = diagnostic
    save(p)
    REPORT.write_text(json.dumps(diagnostic, indent=2) + '\n', encoding='utf8')


def history():
    receipt = json.loads((ROOT / 'deploy/receipts/r4-resolve-take-5.json').read_text())
    rounds = []
    for index, item in enumerate(receipt['consensus_history']['consensus_results']):
        leader = next(v for v in item['leader_result'] if v['mode'] == 'leader')
        proposal = decode(base64.b64decode(leader['eq_outputs']['0'])[1:])
        rounds.append({
            'round': index, 'verdict': proposal['verdict'],
            'case': proposal['resolution_case'], 'quotes': proposal['quotes'],
            'reason': proposal['reason'], 'execution': leader['execution_result'],
            'validatorVotes': [v['vote'] for v in item['validator_results']],
        })
    return {'hash': receipt['hash'], 'result': receipt['result_name'], 'rounds': rounds}


def snapshot(p):
    escrow = p['contracts']['TakeEscrow']['address']
    bet = read(escrow, 'get_bet', ['take-5'])
    resolution = read(p['contracts']['TakeResolver']['address'], 'get_resolution', ['take-5'])
    balances = {}
    for label, address in {'author': bet['author'], 'counterparty': bet['counterparty'], 'escrow': escrow}.items():
        value = client().provider.make_request('eth_getBalance', [address, 'latest'])['result']
        balances[label] = str(int(value, 0) if isinstance(value, str) else int(value))
    assert bet['status'] == 'MATCHED' and bet['total'] == '2' and not bet['claims']
    assert resolution['status'] == 'OPEN' and not resolution['outcome']
    return {'checkedAt': datetime.now(timezone.utc).isoformat(), 'nativeBalancesWei': balances,
            'bet': bet, 'resolution': resolution}


def prepare_version(p, version):
    previous = p.get('consensusDiagnostics')
    if previous and previous.get('version', 1) != version:
        prior = previous.get('version', 1)
        assert prior < version, 'Do not replace a newer diagnostic with an older version'
        archived = ROOT / ('deploy/consensus-diagnostics-v' + str(prior) + '.json')
        assert not archived.exists(), 'Diagnostic archive already exists; reconcile before replacement'
        archived.write_text(json.dumps(previous, indent=2) + '\n', encoding='utf8')
        p.setdefault('previousConsensusDiagnostics', []).append(previous)
        p['consensusDiagnostics'] = {}
        audit = ROOT / 'deploy/diagnostic-link-audit.json'
        if audit.exists():
            audit_archive = ROOT / ('deploy/diagnostic-link-audit-v' + str(prior) + '.json')
            assert not audit_archive.exists()
            audit_archive.write_bytes(audit.read_bytes())
        save(p)


def main():
    p = load()
    assert p['releaseAttempt'] == 4 and sum(p['deposits'].values()) == 22
    canonical = p['contracts']['TakeResolver']
    canonical_source = ROOT / 'contracts' / canonical['source']
    assert hashlib.sha256(canonical_source.read_bytes()).hexdigest() == canonical['sha256']
    digest = hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()
    prepare_version(p, VERSION)
    diagnostic = p.get('consensusDiagnostics') or {
        'status': 'IN_PROGRESS', 'version': VERSION, 'journalPrefix': PREFIX,
        'candidateSource': str(CANDIDATE.relative_to(ROOT)).replace('\\', '/'),
        'candidateSha256': digest, 'canonicalResolver': canonical['address'],
        'canonicalResolverSha256': canonical['sha256'], 'canonicalChanged': False,
        'depositBudgetWei': 22, 'newDepositsWei': 0,
        'authorization': 'Owner said run it asap after the Nintendo regression correction and three unfunded replays plan.' if VERSION == 2 else 'Owner said Run it after the diagnosis/unfunded-replay recovery plan.',
        'recordedFailure': history(), 'cases': {},
        'scope': 'Candidate replay only. Its results cannot settle the configured escrow or update a public record.',
    }
    assert diagnostic['candidateSha256'] == digest, 'Deployed diagnostic candidate is immutable'
    if 'before' not in diagnostic:
        diagnostic['before'] = snapshot(p)
        persist(p, diagnostic)
    try:
        if 'address' not in diagnostic:
            receipt = tx(p, PREFIX + 'deploy', code=CANDIDATE.read_bytes().decode('utf8'),
                         args=[p['contracts']['Takes']['address']], value=0)
            diagnostic['address'] = receipt.get('recipient', receipt.get('to_address'))
            persist(p, diagnostic)
        deployed = client().provider.make_request('gen_getContractCode', [diagnostic['address']])['result']
        assert hashlib.sha256(base64.b64decode(deployed)).hexdigest() == digest
        diagnostic['deployedSourceMatches'] = True
        persist(p, diagnostic)

        # Prespecified hypotheses, starting with the disputed case. A different
        # answer or a failed consensus stops, without running later cases.
        plans = [('take-2', 'NO', 'JUDGED_NO'),
                 ('take-5', 'VOID', 'VOID_INSUFFICIENT_EVIDENCE'), ('take-1', 'YES', 'JUDGED_YES')] if VERSION == 2 else [
                 ('take-5', 'VOID', 'VOID_INSUFFICIENT_EVIDENCE'), ('take-1', 'YES', 'JUDGED_YES'), ('take-2', 'NO', 'JUDGED_NO')]
        if '--grammy-only' in sys.argv:
            plans = [plan for plan in plans if plan[0] == 'take-5']
        for key, outcome, case in plans:
            if diagnostic['cases'].get(key, {}).get('passed'):
                continue
            entry = next(e for e in p['takes'] if e['take']['id'] == key)
            original = read(p['contracts']['Takes']['address'], 'get_take', [key])
            assert original['rule_hash'] == entry['take']['rule_hash']
            evidence = entry['resolution']['evidence']
            for index, item in enumerate(evidence):
                tx(p, PREFIX + key + '-evidence-' + str(index), diagnostic['address'],
                   'submit_evidence', [key, item['url'], item['argument']], value=0)
            tx(p, PREFIX + key + '-seal-author', diagnostic['address'], 'seal_evidence', [key], value=0)
            if entry['bet'].get('counterparty'):
                tx(p, PREFIX + key + '-seal-counter', diagnostic['address'], 'seal_evidence', [key], index=1, value=0)
            tx(p, PREFIX + key + '-resolve', diagnostic['address'], 'resolve', [key], value=0)
            result = read(diagnostic['address'], 'get_resolution', [key])
            diagnostic['cases'][key] = {
                'expectedOutcome': outcome, 'expectedCase': case, 'resolution': result,
                'ruleHashMatches': result['rule_hash'] == original['rule_hash'],
                'sourceUrlsUnchanged': [e['url'] for e in result['evidence']] == [e['url'] for e in evidence],
                'passed': result['status'] == 'FINAL' and result['outcome'] == outcome
                          and result['resolution_case'] == case,
            }
            persist(p, diagnostic)
            assert diagnostic['cases'][key]['passed'], 'Unexpected diagnostic ruling; STOP'
            assert diagnostic['cases'][key]['ruleHashMatches'] and diagnostic['cases'][key]['sourceUrlsUnchanged']
            print('Diagnostic', key, result['outcome'], result['resolution_case'], 'FINALIZED_READBACK', flush=True)
        diagnostic['after'] = snapshot(p)
        diagnostic['fundsUnchanged'] = diagnostic['before']['nativeBalancesWei'] == diagnostic['after']['nativeBalancesWei']
        assert diagnostic['fundsUnchanged']
        diagnostic['status'] = 'PASSED_UNFUNDED_DIAGNOSTICS'
        diagnostic['remaining'] = 'Canonical sealed bet still needs its original resolver or the actual timeout/refund deadline; candidate has no settlement authority.'
        persist(p, diagnostic)
    except Exception as error:
        diagnostic['status'] = 'PENDING_SAVED_HASH' if str(error).startswith('Still pending; resume saved hash') else 'STOPPED_DIAGNOSTIC_FAILURE'
        diagnostic['error'] = type(error).__name__ + ': ' + str(error)
        persist(p, diagnostic)
        raise


if __name__ == '__main__':
    main()
