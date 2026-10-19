import test from "node:test";
import assert from "node:assert/strict";
import { connectWallet } from "../../lib/wallet";

test("adding StudioNet must leave the wallet on the verified signing chain", async () => {
  const previous = Object.getOwnPropertyDescriptor(globalThis, "window");
  let chain = "0x1",
    added = false,
    refuseSwitch = false;
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: {
      ethereum: {
        request: async ({ method }: { method: string }) => {
          if (method === "eth_requestAccounts") return ["0x" + "12".repeat(20)];
          if (method === "eth_chainId") return chain;
          if (method === "wallet_addEthereumChain") {
            added = true;
            return null;
          }
          if (method === "wallet_switchEthereumChain") {
            if (!added)
              throw Object.assign(new Error("Unknown chain"), { code: 4902 });
            if (!refuseSwitch) chain = "0xf22f";
            return null;
          }
          throw Error("Unexpected wallet request: " + method);
        },
      },
    },
  });
  try {
    const connected = await connectWallet();
    assert.equal(chain, "0xf22f");
    assert.equal(connected.account, "0x" + "12".repeat(20));
    chain = "0x1";
    refuseSwitch = true;
    await assert.rejects(connectWallet(), /StudioNet.*61999/);
  } finally {
    if (previous) Object.defineProperty(globalThis, "window", previous);
    else Reflect.deleteProperty(globalThis, "window");
  }
});
