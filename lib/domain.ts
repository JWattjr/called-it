export type Rule = {
  proposition: string;
  yes: string;
  does_not_count: string;
  as_of: number;
  deadline: number;
  default: "NO" | "VOID";
  domains: string[];
};
export type Take = {
  id: string;
  author: string;
  text: string;
  category: string;
  created_at: number;
  historical: boolean;
  rule: Rule;
  rule_hash: string;
  stake_wei: string;
  ratio: number;
  accept_deadline: number;
  evidence_deadline: number;
  status: string;
  decision: string;
  reason: string;
};
export type NativeClaim = {
  amount: string;
  attempt: number;
  status: string;
  parent?: string;
  child?: string;
};
export type Bet = {
  id?: string;
  author?: string;
  counterparty?: string;
  status?: string;
  author_stake?: string;
  counter_stake?: string;
  total?: string;
  outcome?: string;
  refund_deadline?: number;
  intent_wallet?: string;
  intent_expires?: number;
  payouts?: Record<string, string>;
  claims?: Record<string, NativeClaim>;
};
export type Resolution = {
  status?: string;
  outcome?: string;
  verdict?: string;
  quotes?: { index: number; text: string }[];
  reason?: string;
  default_applied?: boolean;
  sealed?: string[];
  evidence?: { party: string; url: string; argument: string }[];
  rule_hash?: string;
};
export type Profile = {
  wallet: string;
  wins: number;
  losses: number;
  voids: number;
  streak: number;
  categories: Record<string, { wins: number; losses: number; voids: number }>;
  history: {
    id: string;
    result: string;
    historical: boolean;
    category: string;
  }[];
};
export type Entry = {
  take: Take;
  bet: Bet;
  resolution: Resolution;
  label?: string;
  context?: { url: string; summary: string };
};
export type Proof = {
  network: string;
  chainId: number;
  releaseStatus: string;
  contracts: Record<
    string,
    { address: string; source: string; sha256: string }
  >;
  transactions: Record<string, string>;
  takes: Entry[];
  profiles?: Profile[];
  recordedAt?: string;
  sourceCommit?: string;
  website?: string;
  github?: string;
  blockers?: string[];
  limitations?: string[];
  demoWallets?: string[];
};
export type TxState =
  | "SUBMITTED"
  | "PENDING"
  | "ACCEPTED"
  | "FINALIZED_SUCCESS"
  | "FINALIZED_ERROR";
export type TrackedTx = {
  hash: string;
  label: string;
  state: TxState;
  created: number;
  children?: string[];
  error?: string;
  appealDeadline?: number | null;
};
export function transactionState(r: Record<string, unknown>): TxState {
  const s = String(r.status_name ?? r.statusName ?? r.status ?? "");
  if (s === "FINALIZED" || s === "7") {
    const c = r.consensus_data as
      | { leader_receipt?: { execution_result?: string }[] }
      | undefined;
    if (r.value_credited === true && !c && String(r.type) === "0")
      return "FINALIZED_SUCCESS";
    const e = String(
      r.txExecutionResultName ?? c?.leader_receipt?.[0]?.execution_result ?? "",
    );
    const a = String(r.result_name ?? r.resultName ?? "");
    return ["SUCCESS", "FINISHED_WITH_RETURN"].includes(e) &&
      (!a || ["AGREE", "MAJORITY_AGREE", "SUCCESS"].includes(a))
      ? "FINALIZED_SUCCESS"
      : "FINALIZED_ERROR";
  }
  return s === "ACCEPTED" || s === "6"
    ? "ACCEPTED"
    : s
      ? "PENDING"
      : "SUBMITTED";
}
export const short = (v: string) => v.slice(0, 6) + "…" + v.slice(-4);
export const date = (n: number) =>
  new Date(n * 1000).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
export const datetime = (n: number) =>
  new Date(n * 1000).toLocaleString("en-GB", { timeZone: "UTC" }) + " UTC";
export function amount(wei: string) {
  const n = BigInt(wei);
  if (n < 1000000000000n) return `${n} wei GEN`;
  const fraction = (n % 1000000000000000000n)
    .toString()
    .padStart(18, "0")
    .replace(/0+$/, "");
  return `${n / 1000000000000000000n}${fraction ? "." + fraction : ""} GEN`;
}
export function payout(stake: string, ratio: number) {
  if (
    !/^[1-9]\d*$/.test(stake) ||
    !Number.isInteger(ratio) ||
    ratio < 1 ||
    ratio > 4
  )
    throw Error("Positive whole wei stake and ratio 1–4 required");
  return (BigInt(stake) * BigInt(1 + ratio)).toString();
}
export function evidenceShape(url: string, rule: Rule) {
  const p = new URL(url);
  if (p.protocol !== "https:" || p.username || p.password || p.hash)
    throw Error(
      "Use an HTTPS permanent snapshot without credentials or fragment.",
    );
  if (
    p.hostname === "en.wikipedia.org" &&
    p.pathname === "/w/index.php" &&
    /^\d+$/.test(p.searchParams.get("oldid") ?? "")
  )
    return "Wikipedia revision; chain preflight will verify its timestamp.";
  const m = p.pathname.match(/^\/web\/(\d{14})id_\/(https?:\/\/.+)$/);
  if (p.hostname !== "web.archive.org" || !m || p.search)
    throw Error("Use an archive.org id_ capture or Wikipedia oldid revision.");
  const host = new URL(m[2]).hostname.replace(/^www\./, "");
  if (!rule.domains.includes(host))
    throw Error("The original source domain is outside this frozen rule.");
  return "Archive snapshot; chain preflight will verify the exact capture in CDX.";
}
