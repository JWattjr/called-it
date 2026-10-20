# Fairness revision: stopped live proof

Revision 3 deployed all four fresh contracts and verified their wiring, but it is not a verified production release. The first Apple resolution finalized with `MAJORITY_DISAGREE` and `[EXPECTED] quote missing from fetched evidence`. Work stopped and this failure was reported. After the owner said "proceed", one explicitly journalled zero-value recovery on the unchanged frozen rule and evidence finalized with `MAJORITY_DISAGREE` and `[EXPECTED] invalid resolution schema`. Chain writes stopped again. Neither failure was a polling timeout; no pending transaction was resubmitted. No quote guard was relaxed and no successful result was invented.

| Contract | New address |
| --- | --- |
| Takes | `0xD76544422810c399fD955f2d15B9c0DcEBa4591E` |
| TakeEscrow | `0x4f7519b441c80244cb3Cf381b6A3a44A574412BB` |
| TakeResolver | `0x858802957e255EAB9E339a53a811ea34aAa70bDB` |
| CalledItRecord | `0xe6D86D8C6F1E0dF9b9e612677B90938342790561` |

First failed resolution: `0x36649536c59b8200099e86f45b34211bf07596fe7a0a0b617649cf1e20238658`.

Owner-authorized recovery: `0x3dca649b6555c2f1817b4628f8e0958d99c1da06730022b2ff1ca329b0bddfbd`.

The frozen default applies only to absent submitted evidence (`DEFAULT_NO_EVIDENCE`). All admitted source fetches failing returns `VOID_SOURCES_UNREACHABLE`. An unfinalized resolution becomes `VOID_TIMEOUT` 48 hours after the evidence deadline, including a resolution waiting in RESOLVING. Readable but inconclusive submitted evidence becomes `VOID_INSUFFICIENT_EVIDENCE`. Escrow copies the case and refunds original deposits on VOID through pull claims and native-credit verification; the public record retains the case without awarding a win.

Reuters, AP and Oscars archive origins are rejected before fetching. Immutable capture metadata must verify before an unlisted source can be admitted. Article preflight status, length, time and error are stored and displayed before the submitter acknowledges them and seals. The owner approved an honest unlisted-host attempt. The actual Apple, Nintendo and Recording Academy preflights were all FETCHED; the additional Netflix probe also returned HTTP 200. No real blocked-source VOID occurred. This proof remains unproven, and mocked failures are not presented as live evidence.

All five real compilations and their finality callbacks succeeded: Apple, Nintendo, no-evidence and Recording Academy compiled; the subjective claim was rejected. Apple remains unresolved after the two failures. Nintendo, no-evidence and Recording Academy resolution were not attempted after the stop. The Recording Academy bet is MATCHED with one wei from each wallet, two wei total; settlement, verified claims and the new public record remain unproven.

The cumulative owner approval is exhausted: revision 2 deposited 18 wei and revision 3 deposited two. No further deposit is authorized. The two earlier live takes, with event deadlines 29 October and 4 November 2026, remain funded on revision 2 with its original immutable policy; they were not migrated or reopened. Four wei remain in those older live takes. The current new matched bet holds two wei. Its escrow refund deadline is Unix `1792787857` (23 October 2026 at 21:37:37 in Africa/Lagos); no refund was initiated during the stopped run.

At the stopped revision-3 checkpoint, local validation passed: 50 direct contract tests, four release tests and seven app tests; all four GenVM lints, TypeScript, ESLint and the production build passed. Tests cover default-only-with-no-evidence, mocked 401/403, retained failed preflights after valid metadata, timeout, exact balances, no duplicate refunds and verified native-credit claims. A subsequent [local model-output repair](MODEL-OUTPUT-REPAIR.md) now passes 69 contract tests and four release tests. Its resolver source differs from the deployed revision-3 hash and requires a fresh deployment; the manifest still records the code actually deployed.

The read-only partial link report checks all four new contract API records as CONTRACT and all 28 revision-3 transaction records as FINALIZED with matching hashes. Link validity does not imply execution success. The report explicitly excludes the older transaction links, remaining HTTP links and complete source/state audit. The full revision-3 verification is not green. See [the archived link audit](../deploy/releases/v3-link-audit.json) for actual results.

README, RELEASE, VERIFICATION, proof.json and portal-fields.json describe this stopped attempt locally. Portal fields measure 67 / 989 / 467 characters against limits of 180 / 1000 / 500. Nothing was submitted to the Portal. Production still serves revision 2; revision-3 changes have not been pushed or deployed to Vercel. A future continuation must address model-output reliability and preserve these failed receipts.
