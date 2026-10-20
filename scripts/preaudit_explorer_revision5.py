"""Bound final Explorer records to saved RPC receipts using four read workers."""
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
proof = json.loads((ROOT / 'deploy/proof.json').read_text())
assert proof['releaseAttempt'] == 5
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'}


def inspect(item):
    label, tx_hash = item
    url = 'https://explorer-studio.genlayer.com/api/transactions/' + tx_hash
    attempts = []
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=60)
            attempts.append({'httpStatus': response.status_code})
            response.raise_for_status()
            data = response.json()
            actual = data.get('transaction', data)
            saved = json.loads((ROOT / 'deploy/receipts' / (label + '.json')).read_text())
            live_consensus = actual.get('consensus_data') or {}
            saved_consensus = saved.get('consensus_data') or {}
            live_leader = (live_consensus.get('leader_receipt') or [{}])[0]
            saved_leader = (saved_consensus.get('leader_receipt') or [{}])[0]
            assert actual.get('hash') == saved.get('hash') == tx_hash
            assert actual.get('status') == 'FINALIZED'
            assert all(actual.get(k) == saved.get(k) for k in ('hash', 'status', 'type', 'value', 'from_address', 'to_address', 'data'))
            assert live_consensus.get('votes') == saved_consensus.get('votes')
            assert all(live_leader.get(k) == saved_leader.get(k) for k in ('result', 'execution_result', 'eq_outputs'))
            at = datetime.now(timezone.utc).isoformat()
            check = {'label': label, 'url': url.replace('/api/transactions/', '/tx/'), 'apiHttpStatus': 200,
                     'attempts': attempts, 'checkedAt': at, 'exactReceiptFieldsBound': True, 'passed': True}
            return url, {'httpStatus': 200, 'fetchedAt': at, 'data': data}, check
        except Exception as error:
            if attempt == 2:
                return url, None, {'label': label, 'url': url, 'attempts': attempts, 'passed': False, 'error': str(error)}
            time.sleep(10)


def main():
    responses, checks = {}, []
    with ThreadPoolExecutor(max_workers=4) as workers:
        for url, entry, check in workers.map(inspect, proof['transactions'].items()):
            checks.append(check)
            if entry:
                responses[url] = entry
            print(len(checks), check['label'], 'PASS' if check['passed'] else 'FAIL', flush=True)
    passed = len(checks) == len(proof['transactions']) and all(c['passed'] for c in checks)
    cache = {'releaseAttempt': 5, 'sourceCommit': proof['sourceCommit'], 'responses': responses}
    raw = (json.dumps(cache) + '\n').encode('utf8')
    (ROOT / '.secrets/r5-explorer-cache.json').write_bytes(raw)
    report = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'releaseAttempt': 5, 'readOnly': True,
              'sourceCommit': proof['sourceCommit'], 'expectedChecks': len(proof['transactions']),
              'passed': passed, 'checks': checks, 'cacheSha256': hashlib.sha256(raw).hexdigest(),
              'scope': 'Every canonical transaction API must return HTTP 200 and bind exact finalized receipt fields, votes and leader output. Maximum cache age 30 minutes. Native credit and contract state require direct RPC.',
              'priorFailures': ['deploy/r5-publication-audit-attempt-1.json', 'deploy/r5-publication-audit-attempt-2.json']}
    (ROOT / 'deploy/r5-explorer-audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
