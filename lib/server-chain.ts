import "server-only";
import { createClient, decodeLocalnetTransaction } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import {
  TransactionHashVariant,
  type TransactionHash,
} from "genlayer-js/types";
import source from "@/deploy/proof.json";
import {
  transactionState,
  type Proof,
  type Entry,
  type Take,
  type Bet,
  type Resolution,
  type Profile,
} from "./domain";
export const recorded = source as unknown as Proof;
const marker = Symbol.for("called-it.rpc-v2");
const global = globalThis as typeof globalThis & { [marker]?: boolean };
if (!global[marker]) {
  const original = globalThis.fetch;
  let stamps: number[] = [];
  let queue = Promise.resolve();
  function reserveRead() {
    const next = queue.then(async () => {
      stamps = stamps.filter((t) => Date.now() - t < 3600000);
      if (stamps.length >= 440)
        throw Error(
          "StudioNet hourly read budget reached. Try again after " +
            new Date(stamps[0] + 3600000).toISOString(),
        );
      const minute = stamps.filter((t) => Date.now() - t < 60000);
      if (minute.length >= 24)
        await new Promise((resolve) =>
          setTimeout(resolve, Math.max(0, minute[0] + 60050 - Date.now())),
        );
      stamps.push(Date.now());
    });
    queue = next.catch(() => {});
    return next;
  }
  globalThis.fetch = async (input, init) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : input.url;
    if (url === "https://studio.genlayer.com/api") {
      await reserveRead();
      const headers = new Headers(init?.headers);
      headers.set("User-Agent", "Mozilla/5.0 CalledIt/1.0");
      return original(input, { ...init, headers });
    }
    return original(input, init);
  };
  global[marker] = true;
}
const chain = createClient({
  chain: studionet,
  endpoint: "https://studio.genlayer.com/api",
});
const cache = new Map<string, { at: number; data: unknown }>(),
  pending = new Map<string, Promise<unknown>>();
async function limited<T>(
  key: string,
  fn: () => Promise<T>,
  ttl = 30000,
): Promise<T> {
  const old = cache.get(key);
  if (old && Date.now() - old.at < ttl) return old.data as T;
  if (pending.has(key)) return pending.get(key) as Promise<T>;
  const p = fn()
    .then((data) => {
      cache.set(key, { at: Date.now(), data });
      return data;
    })
    .finally(() => pending.delete(key));
  pending.set(key, p);
  return p;
}
export async function read<T>(
  contract: string,
  method: string,
  args: unknown[] = [],
): Promise<T> {
  const address = recorded.contracts[contract]?.address;
  if (!address) throw Error("Contract deployment is not recorded yet.");
  return limited(contract + method + JSON.stringify(args), async () => {
    const r = await chain.readContract({
      address: address as `0x${string}`,
      functionName: method,
      args: args as never[],
      transactionHashVariant: TransactionHashVariant.LATEST_FINAL,
    });
    return (typeof r === "string" && /^[\[{]/.test(r) ? JSON.parse(r) : r) as T;
  });
}
export async function snapshot(id?: string, fresh = false) {
  if (fresh) cache.clear();
  const ids = id
    ? [id]
    : (await read<string[]>("Takes", "get_ids", [0, 100])).slice(-25);
  const entries: Entry[] = [];
  for (const key of ids) {
    const take = await read<Take>("Takes", "get_take", [key]);
    if (!take.id) continue;
    const bet = await read<Bet>("TakeEscrow", "get_bet", [key]);
    const resolution = await read<Resolution>(
      "TakeResolver",
      "get_resolution",
      [key],
    );
    const old = recorded.takes.find((e) => e.take.id === key);
    entries.push({
      take,
      bet,
      resolution,
      label: old?.label,
      context: old?.context,
    });
  }
  const wallets = [
    ...new Set(
      entries.flatMap((e) =>
        [e.take.author, e.bet.counterparty].filter((w): w is string => !!w),
      ),
    ),
  ].slice(0, 8);
  const profiles: Profile[] = [];
  for (const wallet of wallets) profiles.push(await profile(wallet));
  return {
    ...recorded,
    takes: entries,
    profiles,
    recordedAt: new Date().toISOString(),
  };
}
export async function profile(wallet: string) {
  return read<Profile>("CalledItRecord", "get_profile", [wallet]);
}
export async function transaction(hash: string) {
  return limited(
    "tx" + hash,
    async () => {
      // Viem's Ethereum formatter drops StudioNet's numeric type 0. Keep the
      // original RPC fields so native credits cannot become false errors.
      const raw = await chain.request({
        method: "eth_getTransactionByHash",
        params: [hash as TransactionHash],
      });
      if (!raw)
        return {
          hash,
          state: "SUBMITTED" as const,
          children: [],
          appealDeadline: null,
          error: null,
        };
      const r = decodeLocalnetTransaction(raw as never) as unknown as Record<
        string,
        unknown
      >;
      const state = transactionState(r);
      let appealDeadline: number | null = null;
      if (state === "ACCEPTED") {
        const window = await limited(
          "window",
          () => chain.request({ method: "sim_getFinalityWindowTime" as never }),
          300000,
        );
        const start = Number(r.timestamp_awaiting_finalization),
          seconds = Number(window),
          failed = Number(r.appeal_failed ?? 0),
          processing = Number(r.appeal_processing_time ?? 0);
        if (
          r.leader_only === false &&
          r.appealed !== true &&
          start > 0 &&
          seconds > 0
        )
          appealDeadline = start + processing + seconds * 0.8 ** failed;
      }
      const c = r.consensus_data as
        | {
            leader_receipt?: {
              result?: { payload?: { readable?: string } | string };
              genvm_result?: unknown;
            }[];
          }
        | undefined;
      const leader = c?.leader_receipt?.[0];
      const payload = leader?.result?.payload;
      const details = leader?.genvm_result as
        | { error_description?: string; raw_error?: string; stderr?: string }
        | undefined;
      const readable =
        typeof payload === "object" ? payload?.readable : payload;
      const executionError =
        readable ||
        details?.error_description ||
        details?.raw_error ||
        details?.stderr;
      const disagreement =
        String(r.result_name ?? r.resultName) === "MAJORITY_DISAGREE";
      let createdId: string | undefined;
      if (state === "FINALIZED_SUCCESS" && typeof payload === "object") {
        try {
          const id = JSON.parse(payload?.readable ?? "null");
          if (typeof id === "string" && /^take-\d+$/.test(id)) createdId = id;
        } catch {}
      }
      return {
        hash,
        state,
        createdId,
        children:
          state === "FINALIZED_SUCCESS" ? (r.triggered_transactions ?? []) : [],
        appealDeadline,
        error:
          state === "FINALIZED_ERROR"
            ? disagreement
              ? "Validators did not agree. No finalized ruling was applied. Open the receipt before retrying."
              : String(
                  executionError ||
                    "Execution failed. Open the receipt for validator details.",
                ).slice(0, 600)
            : null,
      };
    },
    10000,
  );
}
