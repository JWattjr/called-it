"""Read the public production API; never sign or submit a transaction."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deployment', required=True)
    args = parser.parse_args()
    proof = json.loads((ROOT / 'deploy/proof.json').read_text(encoding='utf8'))
    assert proof['releaseAttempt'] == 5
    site = proof['website'].rstrip('/')
    endpoint = site + '/api/state?take=take-1&fresh=1'
    report = {
        'checkedAt': datetime.now(timezone.utc).isoformat(),
        'releaseAttempt': 5, 'passed': False, 'readOnly': True,
        'site': site, 'deployment': args.deployment,
        'api': endpoint, 'sourceCommit': proof['sourceCommit'], 'checks': [],
    }
    destination = ROOT / 'deploy/production-verification.json'
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')

    def check(ok, description):
        report['checks'].append({'passed': bool(ok), 'check': description})
        print('PASS' if ok else 'FAIL', description, flush=True)
        if not ok:
            raise AssertionError(description)

    try:
        headers = {'User-Agent': 'Mozilla/5.0 CalledIt-ReadOnly-Release-Verification'}
        page = requests.get(site, headers=headers, timeout=90)
        report['siteHttpStatus'] = page.status_code
        check(page.status_code == 200, 'Production homepage HTTP 200')
        response = requests.get(endpoint, headers=headers, timeout=300)
        report['apiHttpStatus'] = response.status_code
        check(response.status_code == 200, 'Fresh production state API HTTP 200')
        live = response.json()
        check(live.get('releaseAttempt') == 5, 'Production snapshot is revision 5')
        check(live.get('chainId') == 61999, 'Production uses StudioNet 61999')
        check(live.get('contracts') == proof['contracts'], 'All four production contract bindings match revision 5')
        takes_address = proof['contracts']['Takes']['address']
        check(takes_address.lower() in page.text.lower(), 'Production HTML includes the new Takes address')
        expected = next(e for e in proof['takes'] if e['take']['id'] == 'take-1')
        check(len(live.get('takes', [])) == 1, 'API returns the requested live take only')
        actual = live['takes'][0]
        for key in ('take', 'bet', 'resolution'):
            check(actual[key] == expected[key], 'Fresh finalized ' + key + ' matches recorded chain proof')
        check(live['profiles'] == proof['profiles'], 'Fresh winner and counterparty records match')
        check(live['recordedAt'] != proof['recordedAt'], 'Live read timestamp replaces the packaged snapshot timestamp')
        report.update(passed=True, productionRevision=5, contracts=live['contracts'],
                      liveReadAt=live['recordedAt'], liveEntry=actual, profiles=live['profiles'])
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        report['checkedAt'] = datetime.now(timezone.utc).isoformat()
        destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
