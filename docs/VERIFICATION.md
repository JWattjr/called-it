# Verification record

**Revision 5: the v2 judge is promoted into four fresh, fully wired contracts.** Real finalized replays show Apple YES, Nintendo NO, the no-evidence frozen NO default, subjective rejection and Grammy scheduling evidence VOID_INSUFFICIENT_EVIDENCE. The separate two-wallet Apple bet used exactly 1+1 wei, settled to the winner and paid a verified two-wei native credit. Production serves revision 5 and its live API reads the new Takes address. Nothing was submitted to the Portal.

| Contract | Revision-5 address |
| --- | --- |
| Takes | [0xF1615c3dE4e472c855d5BB7a38151790f13aFCb1](https://explorer-studio.genlayer.com/address/0xF1615c3dE4e472c855d5BB7a38151790f13aFCb1) |
| TakeEscrow | [0x759FAa1540280A01877b63d680B833101dBfb2D4](https://explorer-studio.genlayer.com/address/0x759FAa1540280A01877b63d680B833101dBfb2D4) |
| TakeResolver | [0x6df78000eb25a880d1980aA99Bd6859C86deDA93](https://explorer-studio.genlayer.com/address/0x6df78000eb25a880d1980aA99Bd6859C86deDA93) |
| CalledItRecord | [0xc4d80b678DFAAf1810c7957D13CE4b1316aa6e71](https://explorer-studio.genlayer.com/address/0xc4d80b678DFAAf1810c7957D13CE4b1316aa6e71) |

## Real revision-5 replays

| Case | Final state | Receipt |
| --- | --- | --- |
| official-yes | YES / JUDGED_YES | [Finalized receipt](https://explorer-studio.genlayer.com/tx/0xf7bc3c23e9616da3d07a676d8a000553ba9a315a212fc8e0a0ce3e136e768c32) |
| rumours-no | NO / JUDGED_NO | [Finalized receipt](https://explorer-studio.genlayer.com/tx/0x4e9259c8606b72358e9cc7cc9826bff7e82b9b67f22501c945a3a7ee280ae815) |
| no-evidence-default | NO / DEFAULT_NO_EVIDENCE | [Finalized receipt](https://explorer-studio.genlayer.com/tx/0xfeb8ef50f4c20815b799419c095ae7c70b5a1a6cd9332ba4c1d69394b34a22d1) |
| subjective-rejection | REJECTED | [Finalized receipt](https://explorer-studio.genlayer.com/tx/0x4003f16b2ad71a62ae3d9efab855b3e1b085ecedfa62a0f572fc85da68d29107) |
| scheduling-void | VOID / VOID_INSUFFICIENT_EVIDENCE | [Finalized receipt](https://explorer-studio.genlayer.com/tx/0xd31e48a7c23e7763dbdae0c5535caa1fc2ded833b39e7cb16afb83345bad755c) |

All 44 revision-5 writes, native transfers and callbacks finalized successfully, with matching source, frozen-rule and state reads. [Every revision-5 hash](../deploy/r5-hashes.json). The Grammy case uses a new rule and configured resolver on this release; its scheduling evidence yields VOID, not the frozen default. It is not an unreachable-source demonstration.

## Matched bet and actual native credit

The owner approved exactly one new wei from each demo wallet, raising cumulative deposits from 22 to 24 wei. Apple take-1 matched two distinct wallets and settled YES. Its payout map gives the author exactly two wei. The claim is PAID after its native child was verified; the losing wallet has no payout.

- [Settlement](https://explorer-studio.genlayer.com/tx/0x5a23f02662f622075fc3b5078a5fac5faa75e94dd5334904f7c9182ff4c79594)
- [Winner claim](https://explorer-studio.genlayer.com/tx/0x18297a4c5b9326d1b43e7bb40c3ec762c1eddb554d31340b05bc82ef7d02ad99)
- [Native credit](https://explorer-studio.genlayer.com/tx/0xf1e0d16da650ea181bcfb4fa6936bfbbd2a049edeabfdf9a096db226e638ff63)
- [Credit verification](https://explorer-studio.genlayer.com/tx/0x7fa6113ecf8b605a5a1d0dada52d25fcdf7b305d3c1aa69d2ff76fa62de8f857)
- [Public record](https://explorer-studio.genlayer.com/tx/0x4cd2d89555b9f1731248a8c2546645d5bd8601c0b2d67dc42ead44d5dde06ea3)

Exact native balances before the claim: `{"author": "5", "counterparty": "5", "escrow": "2"}`; after: `{"author": "7", "counterparty": "5", "escrow": "0"}`. The author gains two wei, counterparty changes by zero after funding, and escrow loses two. [Balance proof](../deploy/native-balance-proof.json). The record shows one historical win and one loss; unfunded replays do not add wins.

## Implementation checks

- 69 contract tests and 31 release tests passed, including exact and once-only refunds, the 24-wei cap, isolated original-release recovery and Explorer hints that never replace actual RPC/native-credit confirmation.
- All four GenVM lint checks passed with the pinned runner. Cached catalog/newer-runner warnings are retained.
- AST comparison confirms the promoted judge is exactly v2 and all remaining resolver code is unchanged. Diagnostic printing and the diagnostic docstring are absent.
- App tests, ESLint, TypeScript and build results: [current local check record](../deploy/r5-local-checks.json).
- All four actual deployed source hashes match local files and manifest. [Source audit](../deploy/source-verification.json).

Each deployed address is also a separate Portal evidence entry with preferred type GenLayer Explorer Contract. All four direct pages returned HTTP 200; their Explorer APIs returned CONTRACT and the exact requested addresses. The actual RPC chain ID is StudioNet 61999. [Contract evidence check](../deploy/r5-contract-evidence.json).

## Prior contracts and recovery

The [immutable revision-4 proof](../deploy/releases/v4-proof.json) preserves the failed funded Grammy ruling and original addresses. No revision-4 ruling was retried and no original contract was rewired. Its two wei remain on Escrow 0xC5BeB6B171f37f2c7101EDc83eA2905615415e12. The approved follow-up runs on 23 October 2026 at 22:06 Africa/Lagos, after actual eligibility at 22:04:35, using `python scripts/recover_timeout.py --revision-4 --execute`. It reads archived sources and writes only its isolated working journal. It will not replace revision-5 production. [Follow-up](../deploy/recovery-followup.json).

The separate revision-3 matched bet still holds two wei. The two revision-2 live takes keep deadlines 29 October and 4 November at 23:59:59 UTC and their original immutable failure-default policy. They were not migrated. [Earlier release](../deploy/releases/v2-proof.json).

## Audit, publication and limits

The [full read-only proof audit](../deploy/proof-verification.json) verifies actual Explorer CONTRACT types, canonical /address/ and /tx/ links, every saved transaction, deployed bytes, finalized states, native credits, exact balances, old held bets and HTTP 200 for other published links. Consult its passed field; a partial audit is not a completed release audit. Production serves revision 5 and its live API reads the new Takes address. [Production evidence](../deploy/production-verification.json).

The [Portal draft](submission/portal-fields.json) describes the v2 judge and Grammy VOID and enforces 180/1000/500 characters. Nothing was submitted. Real VOID_SOURCES_UNREACHABLE, the future revision-4 timeout refunds, complete mobile action flows and an interactive browser-extension approval popup remain unproven. The production feed was checked at 1440x960 and 390x844; the desktop receipt also completed its Read live query and displayed Paid & verified. Earlier consensus failures and the v1 semantic regression remain preserved.
