# Verification record

**Revision 4 stopped on a funded matched-bet consensus failure. This is not a verified production release.** Four contracts were deployed and wired, and their deployed code hashes match the local files and manifest. Of 36 new writes and callbacks, 35 finalized successfully and one finalized with `MAJORITY_DISAGREE`. Chain writes stopped at that failure; there was no agent resubmission, settlement or claim afterward. Production still serves revision 2. No production deployment, push or Portal submission followed the failure.

## Latest isolated diagnostic investigation

The [candidate replay](CONSENSUS-DIAGNOSIS.md) finalized Grammy VOID_INSUFFICIENT_EVIDENCE and Apple YES, but Nintendo finalized VOID instead of the required NO. The candidate is not promoted and diagnostic writes stopped. All diagnostic transactions executed successfully; the Nintendo result still fails the semantic regression. Both resolver versions passed the same 69 mocked contract tests, which did not predict this real-model regression. Fourteen release tests pass.

A fresh read after diagnostics confirmed the canonical resolver remains OPEN, the bet remains MATCHED, and balances are author 6, counterparty 6, escrow 2 wei. The [one-time approved follow-up](../deploy/recovery-followup.json) resumes this chat on 23 October at 22:06 Lagos for the original resolver's code-driven timeout, one-time refunds and native-credit verification. It cannot use the candidate as authority or publish it. The recovery is not yet executed.

## Outcomes and failure

| Demonstration | Finalized state |
| --- | --- |
| Apple announcement | YES, `JUDGED_YES` |
| Nintendo announcement | NO, `JUDGED_NO` |
| No submitted evidence | Frozen NO default, `DEFAULT_NO_EVIDENCE` |
| Subjective claim | REJECTED before funding |
| Matched Grammy announcement | Resolver OPEN; escrow MATCHED, two wei held; no accepted ruling |

The [failed matched ruling](https://explorer-studio.genlayer.com/tx/0xb97d441634f38c048daf936a1569bf41fd1851d3e2dc591baf744f31780003ad) is FINALIZED with three disagree votes, one agree and one idle. The leader executed successfully and proposed NO / `JUDGED_NO`, but the network did not accept that proposal. It is not a finalized NO. The receipt does not expose individual validator explanations, so the precise disagreement cause is unproven. The source includes advance announcement language; interpretation ambiguity is a possible explanation, not an established diagnosis.

The article from the unlisted host passed real preflight as FETCHED. It did not establish `VOID_SOURCES_UNREACHABLE`. No blocked host was admitted, no HTTP failure was fabricated, and no successful result was substituted. The owner authorized an honest attempt and disclosure if that real-source proof could not be reproduced.

## Funds and deadlines

The owner approved an additional two simulated wei after the explicit request to raise the cumulative deposit ceiling from 20 to 22. The two deposits of one wei each finalized and credited the intended parties. All 22 approved wei of cumulative deposits have now been used; recovered payouts do not reset that limit.

[Native balance snapshots](../deploy/native-balance-proof.json), taken before the ruling and after failure, both show author 6, counterparty 6 and the new escrow 2 wei. The bet remains MATCHED with empty payouts and claims. These reads prove unchanged funds, not a payout or refund. Settlement, exact native-credit claims and the new matched public record remain unproven.

For the new matched bet, resolver timeout eligibility is 23 October 2026 at 22:04:35 Africa/Lagos; the escrow fallback refund deadline is 23 October at 23:04:35 Africa/Lagos. No refund has been invoked. The revision-3 matched bet separately holds two wei on its original escrow. Two revision-2 live takes retain four wei total, with event deadlines 29 October and 4 November 2026 at 23:59:59 UTC. They were not migrated or reopened and retain their old immutable failure-default policy.

## Implementation checks

- 69 direct contract tests passed, including mocked HTTP 401/403, no-evidence default, consensus timeout, exact balances, one-time refunds, exact quotes and 19 model-output regression cases.
- Fourteen release tests passed, including explicit deposit-limit extension and stopping the auditor on its first failed assertion rather than leaving a stale successful report.
- Seven app tests passed. TypeScript, ESLint and the local production build passed.
- All four GenVM lints passed with the pinned runner. Catalog refresh was unavailable; the cached explicitly pinned runner was used.
- The [source audit](../deploy/source-verification.json) verified all four deployed byte hashes against the local files and manifest.

Mocked failures establish implementation behavior; they do not prove real-network unreachable-source or 48-hour refund execution. A valid schema and exact quotations also do not guarantee model agreement on every claim.

## Browser and link checks

The local browser's Read live flow displayed Apple's finalized YES, exact quotations and `JUDGED_YES`, with no warnings or errors. Screenshot capture was unavailable in this run; the accessibility-state record is retained locally. Full current mobile visual certification has not been repeated. An interactive browser-extension wallet approval popup was not exercised.

The [partial link audit](../deploy/fairness-link-audit.json) passed 40 checks: four canonical `/address/` links whose actual Explorer API type is CONTRACT, and 36 canonical `/tx/` links with the matching finalized transaction identifiers. The rejected ruling's valid link does not make its execution successful. The full historical/publication/HTTP-200 audit was not repeated after this failure; those remaining links are not certified by the partial audit.

The new [diagnostic link audit](../deploy/diagnostic-link-audit.json) is failed: six checks passed, including the candidate API type CONTRACT; nine requests returned HTTP 502/503. It does not certify all diagnostic links.

The [current proof report](../deploy/proof-verification.json) is explicitly `passed: false`, `complete: false`. The [release record](RELEASE.md) lists current addresses, hashes, evidence and blockers. The [Portal fields](submission/portal-fields.json) are a bounded draft only.

## Earlier releases

Revision 3's quote-guard and schema failures remain in [its historical report](FAIRNESS-REVISION.md), [archived proof](../deploy/releases/v3-proof.json) and [failed audit](../deploy/releases/v3-proof-verification.json). The [model-output repair](MODEL-OUTPUT-REPAIR.md) was subsequently deployed in revision 4 and passed the core real rulings; it does not erase either earlier failures or the new consensus failure.

Revision 2's previously successful 596-check audit is preserved in [its archived report](../deploy/releases/v2-proof-verification.json), with [its production check record](../deploy/releases/v2-production-verification.json). Those results apply to revision 2, not the current stopped attempt.
