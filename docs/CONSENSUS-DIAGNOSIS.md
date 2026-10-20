# Consensus diagnosis and recovery

## Latest result: v2 passed all three unfunded replays

The [v2 candidate](https://explorer-studio.genlayer.com/address/0xF311C732FB53Ee9F67aF704a48EB39fafC74B863) corrected the Nintendo regression while preserving the intended scheduling exception. All 14 deployment, evidence, seal, ruling and callback transactions finalized successfully. Every ruling has a matching FINAL state read, unchanged frozen rule hash and unchanged evidence URL.

| Replay | Actual final outcome | Ruling transaction |
| --- | --- | --- |
| Nintendo | NO / JUDGED_NO | [Finalized ruling](https://explorer-studio.genlayer.com/tx/0x3a6763049654cf879966a9ee13576630a412428fd7a5064a0487923cdee40791) |
| Grammy future scheduling evidence | VOID / VOID_INSUFFICIENT_EVIDENCE | [Finalized ruling](https://explorer-studio.genlayer.com/tx/0xdaa9d4ba32fa78f8788a7540a02857fea4d75d62cccafbb8587c0940217cc84d) |
| Apple | YES / JUDGED_YES | [Finalized ruling](https://explorer-studio.genlayer.com/tx/0xe279e9fa93ff487e05c0c14d2e2132577032ead85d5152e144c18ee7821ed027) |

Each ruling had an agreeing quorum of three validators, who independently reran the judgment and checked exact quotations. These were not unanimous votes or proof of universal model reliability. The [complete diagnostic report](../deploy/consensus-diagnostics.json) retains the outcomes, evidence and final reads. The [source and boundary](../diagnostics/README.md) describe both isolated versions.

V2 treats documented nonqualifying reports, including an explicitly unnamed/unannounced status, as a substantive NO finding. It does not require a completed alternative event. VOID applies when a source specifically schedules the exact event for a date inside the window without establishing completion. Generic promises of later information do not meet that exception. No organization, take ID or expected verdict is hardcoded into the candidate's classification logic. Exact quotes, independent verdict comparison and all financial code remain unchanged.

The candidate passed 69 direct contract tests and pinned-runner GenVM lint. All 21 release tests and TypeScript checks passed. [Local check record](../deploy/consensus-local-checks-v2.json). Mocked tests remain separate from these real model replays.

## Funds and configured contracts

The candidate is isolated: it is not the resolver configured in Takes or TakeEscrow and cannot settle the original bet, migrate a rule or update a public record. All four canonical deployed source hashes remain unchanged. No additional deposit was made; cumulative deposits remain 22/22 approved wei.

Fresh reads before and after the full v2 replay both show author 6, counterparty 6 and the original escrow 2 wei. The canonical resolver remains OPEN and its bet MATCHED with no payouts or claims. This establishes unchanged funds, not a native refund or payout. The original matched ruling remains a finalized consensus failure.

## Original failure and v1 regression

The [original revision-4 transaction](https://explorer-studio.genlayer.com/tx/0xb97d441634f38c048daf936a1569bf41fd1851d3e2dc591baf744f31780003ad) contains four leaders proposing INSUFFICIENT_EVIDENCE, YES, YES and NO. None reached agreement. The exact official archive article returned HTTP 200 and combines future announcement text with a future voting-calendar milestone that resembles a completed event when quoted without context. The capture predates the scheduled event. All leaders' quotes occur in the fresh extraction, but the original validators' private decisions and exact fetched-byte hashes are not exposed. [Source diagnostics](../deploy/consensus-source-diagnostics.json).

The [v1 candidate](https://explorer-studio.genlayer.com/address/0x0938252Bc5bB85c48E42281c9B4DCDdBCf33c664) reached Grammy VOID and Apple YES, but its [Nintendo ruling](https://explorer-studio.genlayer.com/tx/0x371b345c8c26938293c39c44f032fded7309605323e1d3d26ebfaf90e3b4311d) returned VOID instead of NO. That failed regression, source, contract and receipts remain in [the v1 archive](../deploy/consensus-diagnostics-v1.json). V2 uses a distinct source, deployment and journal namespace. No failed hash was removed or pending transaction resubmitted.

## Link checks

The [v2 partial link audit](../deploy/diagnostic-link-audit.json) passed all 15 checks: the actual contract API identifies CONTRACT, and all 14 canonical transaction API records returned HTTP 200 with matching finalized hashes. It does not certify the entire publication or historical release.

The [earlier v1 audit](../deploy/diagnostic-link-audit-v1.json) remains failed: six checks passed, then nine requests returned HTTP 502/503. It was preserved rather than edited into success. The updated auditor retries the identical URL for transient errors up to three times, then stops. The full release/publication audit remains pending genuine financial recovery.

A [separate 20 October recheck](../deploy/diagnostic-link-recheck-v1.json) passed all 15 v1 contract/transaction API links and records the preserved failed audit's hash. This establishes recovered Explorer availability; the v1 Nintendo semantic regression remains failed.

## Genuine timeout recovery and release completion

The original resolver becomes eligible for VOID_TIMEOUT on **23 October 2026 at 22:04:35 Africa/Lagos**. The escrow fallback deadline is one hour later. The [readiness report](../deploy/timeout-recovery.json) confirms this deadline; it sends no transaction before eligibility.

The owner-approved one-time same-chat follow-up is scheduled for **23 October at 22:06 Lagos**. It will run `python scripts/recover_timeout.py --execute` using the original configured resolver's code-driven timeout branch, then settle, pull each original one-wei stake, verify both native transfer receipts, check exact balances and sync the VOID_TIMEOUT record. It follows saved hashes and skips PAID claims on resume. It does not retry the failed model ruling or use a diagnostic ruling as settlement authority.

After genuine refunds verify, the follow-up will continue the originally authorized tests, source checks, complete link audit, documentation, commit/push and canonical revision-4 Vercel production deployment. It will retain prior failures and stop on unexpected state. It cannot add deposits, deploy fresh contracts, replace canonical bindings with a diagnostic address, alter the chain clock or submit to the Portal. [Follow-up record](../deploy/recovery-followup.json).

Settlement, native refunds, the full publication audit and production rollout remain unproven today. Real VOID_SOURCES_UNREACHABLE also remains unproven: the admitted article fetched successfully, and the candidate's insufficient-evidence VOID is not a blocked-source proof. Passing sampled judgments does not eliminate date errors in model narratives or guarantee future consensus.
