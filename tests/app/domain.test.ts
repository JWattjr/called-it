import test from "node:test";
import assert from "node:assert/strict";
import {
  transactionState,
  amount,
  payout,
  evidenceShape,
  type Rule,
} from "../../lib/domain";
import { explorer } from "../../lib/explorer";
import { formatTransaction } from "viem";
test("finalized error never becomes a successful bet", () => {
  assert.equal(transactionState({ status: "ACCEPTED" }), "ACCEPTED");
  assert.equal(
    transactionState({
      status: "FINALIZED",
      consensus_data: { leader_receipt: [{ execution_result: "ERROR" }] },
      result_name: "AGREE",
    }),
    "FINALIZED_ERROR",
  );
  assert.equal(
    transactionState({
      status: "FINALIZED",
      consensus_data: { leader_receipt: [{ execution_result: "SUCCESS" }] },
      result_name: "AGREE",
    }),
    "FINALIZED_SUCCESS",
  );
  assert.equal(
    transactionState({
      status: "FINALIZED",
      consensus_data: { leader_receipt: [{ execution_result: "SUCCESS" }] },
      result_name: "MAJORITY_DISAGREE",
    }),
    "FINALIZED_ERROR",
  );
  assert.equal(
    transactionState({ status: "FINALIZED", value_credited: true, type: 0 }),
    "FINALIZED_SUCCESS",
  );
  assert.equal(
    transactionState({ status: "FINALIZED", value_credited: true, type: 2 }),
    "FINALIZED_ERROR",
  );
  const rawNative = {
    status: "FINALIZED",
    type: 0,
    value_credited: true,
    consensus_data: null,
  };
  assert.equal(transactionState(rawNative), "FINALIZED_SUCCESS");
  // The pinned Ethereum formatter erases a numeric StudioNet type 0; the
  // receipt API must classify the raw RPC response, not infer its missing type.
  assert.equal(
    transactionState(
      formatTransaction(rawNative as never) as unknown as Record<
        string,
        unknown
      >,
    ),
    "FINALIZED_ERROR",
  );
});
test("payout arithmetic preserves integer wei beyond JS safe numbers", () => {
  assert.equal(payout("9007199254740993", 4), "45035996273704965");
  assert.equal(payout("2", 1), "4");
  assert.equal(amount("9007199254740993"), "0.009007199254740993 GEN");
  assert.equal(amount("1000000000000000001"), "1.000000000000000001 GEN");
  assert.equal(amount("2"), "2 wei GEN");
  assert.throws(() => payout("0", 1));
  assert.throws(() => payout("1.1", 1));
  assert.throws(() => payout("2", 5));
});
test("evidence preflight refuses live sources and domain suffix attacks", () => {
  const rule = { domains: ["apple.com", "en.wikipedia.org"] } as Rule;
  assert.match(
    evidenceShape(
      "https://web.archive.org/web/20230605190503id_/https://www.apple.com/newsroom/a",
      rule,
    ),
    /CDX/,
  );
  assert.match(
    evidenceShape(
      "https://en.wikipedia.org/w/index.php?title=Apple&oldid=123",
      rule,
    ),
    /revision/,
  );
  for (const u of [
    "https://apple.com/newsroom/a",
    "https://web.archive.org/web/20230605190503/https://apple.com/a",
    "https://web.archive.org/web/20230605190503id_/https://apple.com.evil.test/a",
    "https://user:pass@web.archive.org/web/20230605190503id_/https://apple.com/a",
  ])
    assert.throws(() => evidenceShape(u, rule));
});
test("canonical explorer links validate identifiers", () => {
  const address = "0x" + "12".repeat(20),
    hash = "0x" + "ab".repeat(32);
  assert.equal(
    explorer("address", address),
    "https://explorer-studio.genlayer.com/address/" + address,
  );
  assert.equal(
    explorer("tx", hash),
    "https://explorer-studio.genlayer.com/tx/" + hash,
  );
  assert.throws(() => explorer("address", hash));
  assert.throws(() => explorer("tx", "javascript:alert(1)"));
});
