# Local repair of the stopped resolver

Implemented after the owner asked who would fix the failed release. This repair is local, linted and tested; it has not been deployed or proven with real consensus. The revision-3 addresses and failed receipts remain unchanged. The deployment manifest intentionally retains the hashes of the contracts actually deployed, so its resolver hash differs from this pending source.

Observed failures were `quote missing from fetched evidence` and `invalid resolution schema`. Receipts expose those validation errors, not the rejected raw model answers. Tests therefore reproduce the failure classes; they do not claim to replay an unavailable exact model response.

The parser now selects and validates required verdict, quotes and reason fields instead of rejecting an otherwise valid answer because it contains unused metadata. Extra fields, including payouts, outcomes and resolution cases, never enter contract state. JSON strings and an exact JSON code fence are accepted; missing required fields, invalid verdicts, invalid indices, overlong reasons and invented quotes still fail.

One bounded correction is allowed inside each nondeterministic judgment. It receives the same frozen rule and fetched documents with an explicit instruction to copy contiguous exact passages. It does not receive the invalid answer as instructions. A second invalid answer raises an LLM error. There is no new transaction, automatic resubmission, guessed ruling, default or technical VOID caused by malformed model output.

Each validator independently performs the same bounded judgment. It must still agree on verdict and resolution case and find every leader quotation verbatim in its own fetched evidence. No fuzzy matching, fabricated date, stitched quote or paraphrase is accepted. The existing fairness cases and refund accounting are unchanged.

Validation: **69 direct contract tests and four release tests passed** (73 combined), including 19 new regression cases. The changed resolver passed GenVM lint with the pinned runner. Full-validator tests demonstrate that a repaired leader answer is rejected when the independently repaired validator chooses another verdict. Existing exact-quote, mocked HTTP 401/403, timeout, default, conservation and duplicate-refund tests continue to pass.

Next release work remains the agent's responsibility: deploy fresh contracts and repeat real consensus, state reads and settlement proof before production publication. Additional deposits are not authorized: the cumulative 20 wei budget is exhausted, and the current revision-3 matched bet still holds two wei. A repaired deployment can be created with zero value; funding another 1+1 wei matched demonstration would require owner approval for two additional wei. Production and the Portal remain untouched.
