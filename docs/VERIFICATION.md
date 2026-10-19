# Verification record

This report describes the real StudioNet release and the checks performed on its implementation. The machine-readable [proof audit](../deploy/proof-verification.json) records the independent network audit; [release evidence](RELEASE.md) lists every canonical Explorer link.

## Implementation checks

- 38 direct contract tests passed with mocked web and model responses. Coverage includes excluded and compound claims, evidence timestamps and domains, independent verdict and quote checks, injection, odds, deadlines, refunds, authorization, duplicate counterparties and claims, and finalized records.
- Four release-script tests passed, including cumulative deposit accounting, journal merging and locking, failed payable classification, and preventing a second broadcast after a lost submission response.
- Five app tests passed: transaction finality and native-credit classification, exact integer payout arithmetic, unsafe evidence URLs, canonical Explorer URLs, and wallet chain addition followed by verified switching.
- TypeScript, ESLint and the local production build passed.
- GenVM lint passed for all four deployed contracts using the cached pinned runner. The linter could not refresh its remote runner catalog in the sandbox; the explicitly requested runner pin remains unchanged.

## Browser checks

Every flow was inspected at 1440 × 960 and 390 × 844: feed and filters, post form and compilation review, opposite-side stake review, evidence preflight, YES/NO/default receipts, rejection, profile, proof ledger and transaction tracker. Captures and viewport/overflow measurements are retained locally under `.impeccable/review/`.

A fresh visual reviewer inspected 25 required captures. Its four material findings were fixed and rescored as resolved: wallet connection at the stake point, Share in normal header flow, meaningful profile-history titles, and recovery guidance alongside raw transaction diagnostics. The final visual disposition was `ship`, with no remaining material findings from that batch. This is a visual verdict, not a substitute for chain or wallet verification.

The evidence preview fetched the exact Apple archive capture, verified its CDX record and displayed extracted text before the evidence window was sealed. The final receipts now correctly close evidence submission. Shares preserve the selected take, and profile reads do not substitute another wallet's record.

Real receipts exercised the tracker: a successful contract call, an unauthorized call, a native payout and a runtime-failed payable call. The native payout displays finalized success; native credit on the failed contract call does not turn that call into success. A submitted hash survived reload and resumed polling to its finalized error. Successful finality triggered a fresh contract-state read.

The real EIP-1193 software-wallet adapter signed successful and failed zero-value StudioNet calls. An interactive browser-extension approval popup was **not exercised**. Browser verification therefore covers inspection, forms, preflight and receipt tracking, with real adapter signing verified separately; it does not certify every extension's popup behavior.

## Real money and outcomes

The owner approved up to 20 wei of simulated GEN deposits. The release deposited 18 wei: 12 across three matched historical bets, four across two live author stakes, and two for refundable-deposit tests. Winner claims returned 12 wei and the refund claim returned two; four wei remain in the two live open takes. The two-wei contingency was unused.

The Apple replay resolved YES. The Nintendo replay resolved NO. The evidence-free replay applied its frozen NO default. All three matched bets settled, native payouts were independently verified and public records were updated. The subjective claim was rejected without funding.

The Nintendo NO required two failed zero-value resolution attempts before the third succeeded against the unchanged frozen rule and evidence. Both failures remain public. The Disney live compilation incorrectly rejected a valid future publication window; that false negative is retained and was never funded. These are model reliability limitations, not hidden successful outcomes.

## Independent network audit

The read-only verifier checks each deployed source hash, every canonical contract and transaction URL against its actual Explorer API record, finalized take/escrow/resolution/profile state, frozen rule hashes, evidence URL accessibility, payout conservation and exact native credits. It also verifies the failed payable recovery and the two funded future open takes.

The first complete audit passed 595 of 596 checks; the Apple archive availability request returned HTTP 429. That report is retained as `deploy/audit-first-attempt.json`. The exact immutable URL subsequently opened in the browser and returned HTTP 200 to the verifier's HTTP client after backoff. Evidence availability checks now retry transient 429/5xx responses up to three times, without changing the URL or accepting an exhausted error as success. Local retry checks covered recovery, exhaustion and a permanent 404. The final report records a new complete audit rather than editing the failed result.

Finalized agreeing consensus receipts are bound to live Explorer fields, votes and leader output. Native credits, expected errors and missing quorums are reread directly from RPC. The verifier does not load signing keys or send transactions. Its final timestamp, count and failures are in `deploy/proof-verification.json`; a started but incomplete audit is explicitly marked failed.

The final deployment is built remotely by Vercel in `wattxs-projects`. The Portal fields are a draft only; no Portal submission was made.

The final complete network audit passed **596 checks with zero failures**. Vercel deployment `dpl_6nMxdwQk4ick3yfdKE5UmA8yf2PD` then completed its remote production build and was aliased to `https://called-it-genlayer.vercel.app`. Public HTTP checks returned 200 for the feed, native-payout success, failed-payable error, author profile (1W/2L) and a fresh finalized take read. The production browser confirmed the live-read label and VERIFIED proof badge at the required viewport sizes, with no console errors or warnings. See [production-verification.json](../deploy/production-verification.json) for the deployment and check record.
