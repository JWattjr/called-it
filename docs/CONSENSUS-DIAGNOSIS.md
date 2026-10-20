# Consensus diagnosis and recovery

The original revision-4 matched ruling remains failed. This investigation does not replace its receipt or claim that the funded bet settled.

## Observed failure

The [original transaction](https://explorer-studio.genlayer.com/tx/0xb97d441634f38c048daf936a1569bf41fd1851d3e2dc591baf744f31780003ad) contains four leader rounds. They proposed INSUFFICIENT_EVIDENCE, YES, YES and NO. All executed successfully, but none reached agreement. The original receipt does not expose the independent validators' decisions.

A fresh fetch of the exact admitted archive URL returned HTTP 200. The official article describes a future nominations announcement and contains a voting calendar whose future milestone reads like a completed announcement when quoted without context. The archive capture precedes the scheduled event. All four leaders' quotes occur in the newly extracted text. This supports a temporal interpretation problem; it does not prove the bytes or private reasoning of each original validator. The final leader also incorrectly described a publication later on the as-of date as preceding that day's midnight boundary. See [source diagnostics](../deploy/consensus-source-diagnostics.json).

## Unfunded candidate

The [isolated candidate](https://explorer-studio.genlayer.com/address/0x0938252Bc5bB85c48E42281c9B4DCDdBCf33c664) clarifies completed events versus future schedules, gives models the archive timestamp in ISO UTC, and preserves exact quotations and independent verdict comparison. It does not hardcode the Grammy verdict or loosen the consensus gate. [Its source and boundary](../diagnostics/README.md) are separate from the four configured production contracts.

The Grammy candidate ruling [finalized with an agreeing quorum](https://explorer-studio.genlayer.com/tx/0x51ba8ed712c27ad4ec71543b9668679e5ba3e5c00def89c459f87f9ca389e2f0) on VOID_INSUFFICIENT_EVIDENCE. Three independent validators agreed and verified the leader quotes. Its finality callback and state readback also succeeded. Apple returned the required YES. Nintendo reached consensus on VOID_INSUFFICIENT_EVIDENCE instead of the required NO, so the candidate failed its regression and diagnostic writes stopped. The candidate must not be promoted. See [the complete diagnostic report](../deploy/consensus-diagnostics.json) and [Nintendo receipt](https://explorer-studio.genlayer.com/tx/0x371b345c8c26938293c39c44f032fded7309605323e1d3d26ebfaf90e3b4311d). A successful finalized transaction does not make an unexpected ruling a passing test.

The unchanged canonical resolver and the candidate each passed all 69 direct contract tests. The candidate passed GenVM lint with the pinned runner. Fourteen release tests pass, including premature recovery prevention, exact one-wei refunds, and idempotent resumption.

## Original bet recovery

The candidate is not configured as the original bet's resolver and cannot settle that escrow. No evidence or frozen rule was replaced. No additional deposits are authorized or required for timeout recovery.

The [readiness check](../deploy/timeout-recovery.json) reads the original contracts. It sends no transaction before the real deadline. The original resolver becomes eligible for VOID_TIMEOUT on **23 October 2026 at 22:04:35 Africa/Lagos**. The escrow fallback deadline is one hour later.

`python scripts/recover_timeout.py --execute` will, once eligible, use an explicit timeout label, settle the matched bet, claim each original one-wei stake, verify both native transfer credits, check exact balance changes and sync the VOID record. It follows saved hashes and skips PAID claims on resume. It does not resubmit the failed judgment or run another model interpretation. Before eligibility it returns WAITING without sending anything.

Fresh readbacks after diagnostics show author 6, counterparty 6 and escrow 2 wei, with the original resolver OPEN and bet MATCHED. All 22 approved cumulative deposit wei remain accounted for. The candidate has not changed canonical state or funds.

The owner explicitly approved automatic resumption. A one-time same-chat follow-up is active for **23 October at 22:06 Lagos** to run the tested timeout/refund command and verify both native credits. It will preserve the failed candidate and stop on unexpected state. It will not deposit, retry a model ruling, promote the candidate, push or publish production. [Follow-up record](../deploy/recovery-followup.json).

The recovery has been tested locally and checked for readiness; it has not executed on-chain. Production deployment, push, the full publication audit and Portal submission have not occurred.

Passing two real candidate examples does not establish general model reliability. Some validator narrative reasons also contain incorrect time calculations, despite agreeing on the safe VOID outcome. The required Nintendo NO regression is explicitly failed, not reclassified as an acceptable new expectation.

The [diagnostic link audit](../deploy/diagnostic-link-audit.json) checked the contract API type as CONTRACT and five transaction links successfully. Nine later transaction requests returned HTTP 502/503. The failed report is retained; these links are not certified HTTP 200, even though their saved RPC receipts finalized successfully. The original 40-check canonical-deployment link audit remains a separate earlier report.
