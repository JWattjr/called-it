"""Read-only partial Explorer audit; no release verdict or signing keys."""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}


def fetch_api(url):
    attempts = []
    for index in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=60)
            status = response.status_code
            attempts.append({'httpStatus': status})
            if status == 200:
                try:
                    data = response.json()
                except ValueError:
                    attempts[-1]['error'] = 'Invalid JSON'
                    return status, {}, attempts
                return status, data if isinstance(data, dict) else {}, attempts
            if status not in (429, 502, 503, 504) or index == 2:
                return status, {}, attempts
        except requests.RequestException as error:
            attempts.append({'transportError': type(error).__name__})
            if index == 2:
                return None, {}, attempts
        time.sleep(10 * (index + 1))
    raise AssertionError('Unreachable retry state')


def main(diagnostic=None):
    p = json.loads((ROOT / 'deploy/proof.json').read_text())
    if diagnostic is None:
        diagnostic = '--diagnostic' in sys.argv
    current = p.get('consensusDiagnostics', {})
    prefix = current.get('journalPrefix', 'diagnostic-schedule-v1-') if diagnostic else p.get('deploymentPrefix', 'r3-')
    contracts = {'Unfunded consensus candidate': current} if diagnostic else p['contracts']
    targets = [(name, 'address', item['address']) for name, item in contracts.items()]
    targets += [(label, 'tx', value) for label, value in p['transactions'].items() if label.startswith(prefix)]
    checks = []
    for label, kind, identifier in targets:
        url = 'https://explorer-studio.genlayer.com/' + kind + '/' + identifier
        api = url.replace('/address/', '/api/address/').replace('/tx/', '/api/transactions/')
        status, data, attempts = fetch_api(api)
        check = {'label': label, 'url': url, 'apiHttpStatus': status, 'attempts': attempts}
        if kind == 'address':
            check.update(type=data.get('type'), passed=status == 200 and data.get('type') == 'CONTRACT')
        else:
            actual = data.get('transaction', data)
            stored = json.loads((ROOT / 'deploy/receipts' / (label + '.json')).read_text())
            passed = status == 200 and str(actual.get('hash', '')).lower() == identifier.lower() and actual.get('status') == stored.get('status') == 'FINALIZED'
            check.update(status=actual.get('status'), savedResult=stored.get('result_name'), passed=passed)
        checks.append(check)
        if not check['passed']:
            break
        time.sleep(2.2)
    syntax = all(re.fullmatch(r'0x[0-9a-fA-F]{64}', value) for value in p['transactions'].values())
    complete = len(checks) == len(targets)
    report = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'releaseAttempt': p['releaseAttempt'],
              'readOnly': True, 'prefix': prefix, 'scope': str(len(contracts)) + ' contract API records and all ' + prefix + 'transaction API records. Valid links do not imply successful execution or correct rulings.',
              'passed': bool(syntax and complete and all(c['passed'] for c in checks)), 'complete': complete,
              'expectedChecks': len(targets), 'allTransactionIdentifiersCanonical': syntax, 'checks': checks,
              'notReaudited': ['Earlier release transaction records', 'Other published HTTP links', 'Full contract source and state audit'],
              'executionFailures': [c for c in checks if c.get('savedResult') == 'MAJORITY_DISAGREE'],
              'note': 'Transient HTTP failures retry at the identical URL up to three times. An exhausted or permanent failure stops the audit; a failed report is never green.'}
    destination = ROOT / ('deploy/diagnostic-link-audit.json' if diagnostic else 'deploy/fairness-link-audit.json')
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(len(checks), 'of', len(targets), 'link checks;', sum(not c['passed'] for c in checks), 'failures; partial link audit only.')
    return report


if __name__ == '__main__':
    raise SystemExit(0 if main()['passed'] else 1)
