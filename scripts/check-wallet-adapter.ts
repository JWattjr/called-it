/** Actual EIP-1193 signing through the app adapter, with zero GEN value only. */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { privateKeyToAccount } from "viem/accounts";
import { connectWallet } from "../lib/wallet";
const rpcURL = "https://studio.genlayer.com/api";
const expectedError = process.argv.includes("--expected-error");
const path = expectedError
  ? "deploy/wallet-adapter-error.json"
  : "deploy/wallet-adapter-success.json";
const proof = JSON.parse(readFileSync("deploy/proof.json", "utf8"));
const keys = JSON.parse(readFileSync(".secrets/demo-accounts.json", "utf8"));
const account = privateKeyToAccount(
  ("0x" + keys[1].replace(/^0x/, "")) as `0x${string}`,
);
const saved = existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : null;
const output = saved ?? {
  scope:
    "Real local software-wallet EIP-1193 signing through lib/wallet.ts; browser extension popup is not exercised.",
  wallet: account.address,
  valueWei: "0",
  hash: null,
  status: "NOT_SUBMITTED",
  expectedState: expectedError ? "FINALIZED_ERROR" : "FINALIZED_SUCCESS",
};
const persist = () =>
  writeFileSync(path, JSON.stringify(output, null, 2) + "\n");
let last = 0;
async function rpc(method: string, params: unknown[] = []) {
  await new Promise((resolve) =>
    setTimeout(resolve, Math.max(0, 4000 - (Date.now() - last))),
  );
  last = Date.now();
  const r = await fetch(rpcURL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "User-Agent": "Mozilla/5.0 CalledItWallet/1.0",
    },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
  });
  const data = await r.json();
  if (!r.ok || data.error)
    throw Error(data.error?.message ?? "RPC unavailable");
  return data.result;
}
Object.defineProperty(globalThis, "window", {
  value: {
    ethereum: {
      request: async ({
        method,
        params = [],
      }: {
        method: string;
        params?: unknown[];
      }) => {
        if (method === "eth_requestAccounts") return [account.address];
        if (method === "eth_sendTransaction") {
          const tx = params[0] as Record<string, string>;
          if (BigInt(tx.value) !== 0n)
            throw Error("Only a zero-value adapter check is allowed.");
          const raw = await account.signTransaction({
            chainId: 61999,
            type: "legacy",
            to: tx.to as `0x${string}`,
            data: tx.data as `0x${string}`,
            nonce: Number(BigInt(tx.nonce)),
            gas: BigInt(tx.gas),
            gasPrice: BigInt(tx.gasPrice),
            value: 0n,
          });
          return rpc("eth_sendRawTransaction", [raw]);
        }
        return rpc(method, params);
      },
    },
  },
});
if (!output.status.startsWith("FINALIZED")) {
  const wallet = await connectWallet((hash) => {
    output.hash = hash;
    output.status = "SUBMITTED";
    persist();
  });
  if (!output.hash) {
    const address = expectedError
      ? proof.contracts.Takes.address
      : proof.probeContract;
    output.hash = await wallet.client.writeContract({
      address,
      functionName: expectedError ? "configure" : "probe",
      args: expectedError
        ? [
            proof.contracts.TakeResolver.address,
            proof.contracts.TakeEscrow.address,
            proof.contracts.CalledItRecord.address,
          ]
        : ["https://thewaltdisneycompany.com/"],
      value: 0n,
      consensusMaxRotations: 2,
    });
    output.status = "SUBMITTED";
    persist();
  }
  for (let i = 0; i < 180; i++) {
    const receipt = await rpc("eth_getTransactionByHash", [output.hash]);
    if (receipt?.status === "FINALIZED") {
      const leader = receipt.consensus_data?.leader_receipt?.[0];
      output.status =
        ["SUCCESS", "FINISHED_WITH_RETURN"].includes(
          leader?.execution_result,
        ) &&
        [undefined, "AGREE", "MAJORITY_AGREE", "SUCCESS"].includes(
          receipt.result_name,
        )
          ? "FINALIZED_SUCCESS"
          : "FINALIZED_ERROR";
      output.receipt = receipt;
      persist();
      break;
    }
    console.log(
      "Adapter transaction",
      output.hash,
      receipt?.status ?? "SUBMITTED",
    );
    await new Promise((resolve) => setTimeout(resolve, 10000));
  }
}
if (output.status !== output.expectedState)
  throw Error(
    "Adapter check has not reached its expected finalized execution state; saved hash must be resumed.",
  );
console.log(output.status, output.hash);
