# Verification record

**Revision 4 awaits genuine timeout recovery. The isolated v2 diagnostic passed all three replays; the financial and production release remains incomplete.** The four configured contracts are unchanged. Production still serves revision 2, and nothing was submitted to the Portal.

## Latest v2 diagnostic

[The v2 report](../deploy/consensus-diagnostics.json) records real Nintendo NO / JUDGED_NO, Grammy VOID / VOID_INSUFFICIENT_EVIDENCE and Apple YES / JUDGED_YES. All 14 zero-value diagnostic writes and callbacks finalized successfully. Every ruling has a matching FINAL state read, unchanged frozen rule hash and unchanged evidence URL. Each ruling had three agreeing validators. The exact deployed candidate code matches its local source hash.

The correction restores a substantive NO for documented nonqualifying reports or unnamed/unannounced status. The future-schedule VOID exception requires a specific dated plan for the exact claimed event. Generic development intentions do not qualify. Exact quotations and independently rerun validator judgments are preserved. [Detailed diagnosis, addresses and hashes](CONSENSUS-DIAGNOSIS.md).

The diagnostic is isolated from the canonical Takes configuration and escrow. It cannot settle the original bet or create a public win. The failed v1 Nintendo VOID regression remains in [its archive](../deploy/consensus-diagnostics-v1.json), with its source, address and receipts unchanged. Neither sampled success nor agreeing model narratives establish universal reliability.

## Canonical revision-4 outcomes and funds

| Demonstration | Canonical finalized state |
| --- | --- |
| Apple announcement | YES, JUDGED_YES |
| Nintendo announcement | NO, JUDGED_NO |
| No submitted evidence | Frozen NO default, DEFAULT_NO_EVIDENCE |
| Subjective claim | REJECTED before funding |
| Funded Grammy announcement | Resolver OPEN; escrow MATCHED, two wei held; no accepted ruling |

The original 36 writes and callbacks include 35 finalized successes and [one finalized MAJORITY_DISAGREE](https://explorer-studio.genlayer.com/tx/0xb97d441634f38c048daf936a1569bf41fd1851d3e2dc591baf744f31780003ad). Its unaccepted leader proposal is not a ruling. No canonical model retry, stake transfer or binding change occurred during either diagnostic replay.

Fresh reads before and after v2 show author 6, counterparty 6 and canonical escrow 2 wei, with no claims or payouts. Cumulative deposits remain 22/22 approved wei. These reads prove unchanged funds, not native payout or refund completion. The earlier revision-3 matched bet separately holds two wei; the two revision-2 live takes hold four wei total on their old contracts.

The original resolver becomes eligible for VOID_TIMEOUT on **23 October 2026 at 22:04:35 Africa/Lagos**, and escrow fallback is one hour later. The [readiness check](../deploy/timeout-recovery.json) sends nothing before eligibility. The owner-approved [one-time follow-up](../deploy/recovery-followup.json) resumes this chat at **22:06 Lagos** to execute the original code-driven timeout, settle and verify both one-wei native refunds, then continue the originally requested publication checks and rollout only after verification passes. It adds no deposits, retries no model judgment and cannot substitute a diagnostic address for the configured resolver.

The two older live takes retain deadlines 29 October and 4 November 2026 at 23:59:59 UTC. They were not migrated or reopened and retain their original immutable failure-default policy. Details remain in [the revision-2 proof](../deploy/releases/v2-proof.json).

## Implementation and browser checks

- The current configured contracts passed 69 direct tests; their source files are unchanged. The new v2 candidate separately passed the same 69 direct tests.
- All 21 release tests pass, covering exact and one-time timeout refunds, premature execution prevention, failed-claim stopping, durable version archives and bounded HTTP retries with failed-audit preservation.
- On 20 October, all seven app tests and ESLint passed again. The production build passed, including its TypeScript check. [Readiness record](../deploy/release-readiness.json). Later source changes still require their appropriate final release checks.
- All four configured contracts passed GenVM lint previously. V2 also passed lint with the explicitly pinned runner; cached catalog warnings are retained. [V2 local check record](../deploy/consensus-local-checks-v2.json).
- The [source audit](../deploy/source-verification.json) verified all four canonical deployed hashes; subsequent diagnostics did not change those local files or deployed bindings.

The previous local Read live browser check displayed canonical Apple's final YES, exact quotations and JUDGED_YES with no warnings or errors. Screenshot capture was unavailable in that run; its accessibility state is retained locally. Current mobile visual certification and an interactive browser-extension approval popup remain unverified.

## Link and release scope

The [v2 partial Explorer audit](../deploy/diagnostic-link-audit.json) passed 15/15 checks: candidate API type CONTRACT and all 14 exact finalized transaction identifiers, each returning HTTP 200 through canonical address/transaction routes. The separate earlier canonical-deployment audit passed 40 checks. The [v1 audit](../deploy/diagnostic-link-audit-v1.json) remains failed with nine HTTP 502/503 responses; it was not edited into success. A [separate v1 recheck](../deploy/diagnostic-link-recheck-v1.json) now passes all 15 canonical contract/transaction API links and records the unchanged failed audit's SHA-256. Its Nintendo semantic regression remains failed.

The [HTTP readiness audit](../deploy/http-readiness.json) returned 200 for all 13 already-published non-Explorer links, including all three evidence URLs. New local artifacts remain explicitly pending publication. The public site's 200 response confirms availability of revision 2, not deployment of revision 4. The full historical/publication audit remains pending verified recovery and publication.

The [current proof report](../deploy/proof-verification.json) is explicitly passed:false, complete:false. Real VOID_SOURCES_UNREACHABLE is still unproven: the real admitted article fetched successfully. Neither mocked 401/403 tests nor the candidate's readable-insufficient-evidence VOID establishes that network proof. Settlement, native refunds and current production rollout also remain unproven today. [Release evidence](RELEASE.md) and [bounded Portal draft](submission/portal-fields.json) record the actual status.

## Historical releases

Revision 3's quote-guard and schema failures remain in [its historical report](FAIRNESS-REVISION.md), [archived proof](../deploy/releases/v3-proof.json) and [failed audit](../deploy/releases/v3-proof-verification.json). The [model-output repair](MODEL-OUTPUT-REPAIR.md) was deployed in revision 4 and passed the canonical core rulings; later isolated diagnostics do not erase earlier failures.

Revision 2's successful 596-check audit is preserved in [its archived report](../deploy/releases/v2-proof-verification.json), with [its production record](../deploy/releases/v2-production-verification.json). Those results apply to revision 2, not this incomplete release.
