import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path('scripts').resolve()))
import audit_fairness_links as audit


def responses(monkeypatch, statuses):
    sequence = iter(statuses)
    urls = []
    delays = []

    def get(url, **kwargs):
        urls.append(url)
        return SimpleNamespace(status_code=next(sequence), json=lambda: {'type': 'CONTRACT'})

    monkeypatch.setattr(audit.requests, 'get', get)
    monkeypatch.setattr(audit.time, 'sleep', delays.append)
    return urls, delays


def test_transient_api_errors_retry_identical_url_and_can_recover(monkeypatch):
    urls, delays = responses(monkeypatch, [503, 502, 200])
    status, data, attempts = audit.fetch_api('https://example.test/exact')
    assert status == 200 and data == {'type': 'CONTRACT'}
    assert urls == ['https://example.test/exact'] * 3 and delays == [10, 20]
    assert [a['httpStatus'] for a in attempts] == [503, 502, 200]


def test_exhausted_transient_errors_remain_failure(monkeypatch):
    urls, _ = responses(monkeypatch, [503, 503, 503])
    status, data, attempts = audit.fetch_api('https://example.test/exact')
    assert status == 503 and data == {} and len(attempts) == len(urls) == 3


def test_permanent_http_error_is_not_retried(monkeypatch):
    urls, delays = responses(monkeypatch, [404])
    status, _, attempts = audit.fetch_api('https://example.test/missing')
    assert status == 404 and len(urls) == len(attempts) == 1 and delays == []


def test_audit_stops_at_first_broken_link_and_replaces_stale_success(tmp_path, monkeypatch):
    folder = tmp_path / 'deploy'
    folder.mkdir()
    proof = {'releaseAttempt': 4, 'deploymentPrefix': 'r4-',
             'contracts': {'Example': {'address': '0x' + '1' * 40}},
             'transactions': {'r4-saved': '0x' + '2' * 64}}
    (folder / 'proof.json').write_text(json.dumps(proof))
    report = folder / 'fairness-link-audit.json'
    report.write_text('{"passed":true}')
    urls, _ = responses(monkeypatch, [404])
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    result = audit.main(diagnostic=False)
    assert len(urls) == 1 and not result['passed'] and not result['complete']
    assert result['expectedChecks'] == 2 and len(result['checks']) == 1
    assert not json.loads(report.read_text())['passed']
