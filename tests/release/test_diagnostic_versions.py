import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path('scripts').resolve()))
import chain
import diagnose_consensus as diagnostic


def test_new_candidate_preserves_prior_failure_and_original_spending(tmp_path, monkeypatch):
    folder = tmp_path / 'deploy'
    folder.mkdir()
    old = {'address': 'old-candidate', 'status': 'STOPPED_DIAGNOSTIC_FAILURE',
           'candidateSha256': 'immutable', 'cases': {'take-2': {'passed': False}}}
    p = {'consensusDiagnostics': old, 'transactions': {'original': 'saved-hash'}, 'deposits': {'approved': 22}}
    (folder / 'proof.json').write_text(json.dumps(p))
    audit = '{"passed":false,"httpErrors":9}\n'
    (folder / 'diagnostic-link-audit.json').write_text(audit)
    monkeypatch.setattr(diagnostic, 'ROOT', tmp_path)
    monkeypatch.setattr(chain, 'ROOT', tmp_path)
    diagnostic.prepare_version(p, 2)
    saved = json.loads((folder / 'proof.json').read_text())
    assert saved['consensusDiagnostics'] == {}
    assert saved['previousConsensusDiagnostics'] == [old]
    assert saved['transactions'] == {'original': 'saved-hash'} and sum(saved['deposits'].values()) == 22
    assert json.loads((folder / 'consensus-diagnostics-v1.json').read_text()) == old
    assert (folder / 'diagnostic-link-audit-v1.json').read_text() == audit


def test_same_candidate_version_resumes_without_erasing_manifest(tmp_path, monkeypatch):
    old = {'version': 2, 'address': 'existing-candidate'}
    p = {'consensusDiagnostics': old}
    monkeypatch.setattr(diagnostic, 'ROOT', tmp_path)
    monkeypatch.setattr(diagnostic, 'save', lambda _: pytest.fail('No reset or save for the same version'))
    diagnostic.prepare_version(p, 2)
    assert p['consensusDiagnostics'] == old and not list(tmp_path.iterdir())


def test_older_version_cannot_replace_newer_candidate(tmp_path, monkeypatch):
    p = {'consensusDiagnostics': {'version': 2, 'address': 'existing-candidate'}}
    monkeypatch.setattr(diagnostic, 'ROOT', tmp_path)
    with pytest.raises(AssertionError, match='newer diagnostic'):
        diagnostic.prepare_version(p, 1)
    assert p['consensusDiagnostics']['address'] == 'existing-candidate'
