# Isolated consensus candidate

`consensus_candidate.py` is an unfunded diagnostic copy of the revision-4 resolver, linked to the existing Takes contract only to replay its immutable rules and evidence. It is **not** the resolver configured in Takes or TakeEscrow. Its rulings cannot settle a bet, transfer stakes, migrate a take or update a public record.

The candidate distinguishes completed announcements from future schedules, supplies the verified archive timestamp as an ISO UTC value, and clarifies the difference between contrary evidence and an unresolved future event. It retains the same exact-quote parser, bounded model correction, independently rerun validator judgment, blocked-host policy and timeout/refund cases. Validator stdout exposes the independently derived decision for diagnosis.

The deployed candidate is immutable. Its exact bytes and SHA-256 are recorded in `deploy/consensus-diagnostics.json`; changes require a different diagnostic deployment and journal namespace. The initial deployment sent LF-normalized text while the local file used CRLF. A read-only comparison proved the deployed bytes exactly matched the LF normalization. The local file and manifest were reconciled to those bytes without another deployment or a semantic change; both hashes remain in the report.

Run all resolver regression tests against this file with:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:CALLED_IT_TEST_RESOLVER='diagnostics/consensus_candidate.py'
python -m pytest -p gltest.direct.pytest_plugin tests/direct -q --basetemp=.secrets/pytest-candidate
```

The real replay uses `python scripts/diagnose_consensus.py`. Every write explicitly sends zero value, saves its hash before polling, and resumes that hash. It stops on failed consensus or an unexpected result. It does not clear or waive the original failed ruling.

The original sealed bet requires its configured resolver or its genuine timeout. `python scripts/recover_timeout.py` only inspects readiness. `--execute` additionally permits zero-value timeout resolution, settlement and one-time verified native refunds **after** the actual 48-hour deadline. It cannot accelerate that deadline or use the diagnostic ruling as authority.
