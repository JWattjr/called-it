"use client";
import Link from "next/link";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCheck,
  ChevronDown,
  Clock3,
  Copy,
  Flame,
  Home,
  LoaderCircle,
  Plus,
  Receipt,
  RefreshCw,
  Scale,
  ShieldCheck,
  Trophy,
  UserRound,
  Wallet,
  X,
} from "lucide-react";
import { connectWallet } from "@/lib/wallet";
import {
  amount,
  date,
  datetime,
  evidenceShape,
  payout,
  short,
  type Entry,
  type Profile,
  type Proof,
  type TrackedTx,
} from "@/lib/domain";
import { explorer } from "@/lib/explorer";

const NAV = [
  { view: "feed", href: "/", label: "The feed", Icon: Home },
  { view: "resolve", href: "/resolve", label: "Settle a take", Icon: Scale },
  { view: "profile", href: "/profile", label: "Your record", Icon: UserRound },
  { view: "proof", href: "/proof", label: "The receipts", Icon: Receipt },
];
const TXLABEL = {
  SUBMITTED: "Submitted",
  PENDING: "Validators working",
  ACCEPTED: "Accepted · appeal window",
  FINALIZED_SUCCESS: "Finalized · success",
  FINALIZED_ERROR: "Finalized · error",
};
const CATEGORIES = ["all", "tech", "entertainment", "sports", "company"];
const EMPTY: Profile = {
  wallet: "",
  wins: 0,
  losses: 0,
  voids: 0,
  streak: 0,
  categories: {},
  history: [],
};
function receiptError(value: string) {
  try {
    const data = JSON.parse(value);
    if (data && typeof data === "object")
      return (
        data.error_description ||
        data.raw_error ||
        data.stderr ||
        "Execution failed. Open the receipt for validator details."
      );
  } catch {}
  return `Execution failed. Open the receipt for validator details. Diagnostic: ${value}`;
}
function rejectionLabel(decision: string) {
  return (
    (
      {
        SUBJECTIVE:
          "Subjective claims cannot be settled from an official announcement.",
        COMPOUND: "Use one claim with one outcome.",
        EXCLUDED: "This claim is in an excluded topic.",
        UNRESOLVABLE:
          "The compiler could not find a valid evidence path for this event window.",
      } as Record<string, string>
    )[decision] ?? "The compiler rejected this take."
  );
}
function External({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <a href={href} target="_blank" rel="noreferrer">
      {children}
      <ArrowUpRight size={14} />
    </a>
  );
}
function Avatar({
  wallet,
  large = false,
}: {
  wallet: string;
  large?: boolean;
}) {
  return (
    <span className={"avatar " + (large ? "large" : "")} aria-hidden="true">
      {wallet.slice(2, 4).toUpperCase()}
    </span>
  );
}
function Stamp({ outcome }: { outcome: string }) {
  return (
    <span
      className={
        "stamp " +
        (outcome === "YES" ? "yes" : outcome === "NO" ? "no" : "void")
      }
    >
      {outcome === "YES" ? "CALLED IT" : outcome === "NO" ? "MISSED" : "VOID"}
    </span>
  );
}

export default function CalledIt({
  initial,
  view,
  takeId,
  profileWallet,
}: {
  initial: Proof;
  view: string;
  takeId?: string;
  profileWallet?: string;
}) {
  const [proof, setProof] = useState(initial),
    [live, setLive] = useState(false),
    [liveScope, setLiveScope] = useState(""),
    [loading, setLoading] = useState(false),
    [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [account, setAccount] = useState(""),
    [filter, setFilter] = useState("all"),
    [tab, setTab] = useState("all"),
    [txs, setTxs] = useState<TrackedTx[]>([]),
    [hydrated, setHydrated] = useState(false),
    [profile, setProfile] = useState<Profile | null>(null),
    [selected, setSelected] = useState(
      takeId ?? initial.takes[0]?.take.id ?? "",
    ),
    [copied, setCopied] = useState(false),
    [profileQuery, setProfileQuery] = useState("");
  const cursor = useRef(0);
  const current = proof.takes.find((e) => e.take.id === selected);
  const profileAddress = profileQuery || profileWallet || account || "";
  const update = useCallback(async (id?: string) => {
    setLoading(true);
    setError("");
    try {
      const r = await fetch(
        "/api/state?fresh=1" + (id ? "&take=" + encodeURIComponent(id) : ""),
        { cache: "no-store" },
      );
      const p = await r.json();
      if (!r.ok) throw Error(p.error);
      setProof((old) =>
        id
          ? {
              ...p,
              takes: [...old.takes.filter((e) => e.take.id !== id), ...p.takes],
            }
          : p,
      );
      setLive(true);
      setLiveScope(id ?? "");
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Could not read the chain. Retry when the network recovers.",
      );
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    // External browser storage is restored after hydration so SSR stays deterministic.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAccount(sessionStorage.getItem("called-it-account") ?? "");
    try {
      const saved = JSON.parse(
        localStorage.getItem("called-it-transactions") ?? "[]",
      );
      if (Array.isArray(saved))
        setTxs(saved.filter((t) => /^0x[\da-f]{64}$/i.test(t.hash)).slice(-40));
    } catch {}
    setHydrated(true);
  }, []);
  useEffect(() => {
    if (hydrated)
      localStorage.setItem("called-it-transactions", JSON.stringify(txs));
  }, [txs, hydrated]);
  useEffect(() => {
    const p = window.ethereum;
    const reset = () => {
      setAccount("");
      sessionStorage.removeItem("called-it-account");
    };
    p?.on?.("accountsChanged", reset);
    p?.on?.("chainChanged", reset);
    return () => {
      p?.removeListener?.("accountsChanged", reset);
      p?.removeListener?.("chainChanged", reset);
    };
  }, []);
  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      const active = txs.filter((t) => !t.state.startsWith("FINALIZED"));
      if (!active.length) return;
      const batch = Array.from(
        { length: Math.min(2, active.length) },
        (_, i) => active[(cursor.current + i) % active.length],
      );
      cursor.current += batch.length;
      for (const tx of batch) {
        try {
          const r = await fetch("/api/transaction/" + tx.hash);
          const data = await r.json();
          if (!r.ok) continue;
          if (cancelled) return;
          setTxs((old) => {
            const next = old.map((t) =>
              t.hash === tx.hash ? { ...t, ...data } : t,
            );
            for (const h of (data.children ?? []) as string[])
              if (!next.some((t) => t.hash === h))
                next.push({
                  hash: h,
                  label: "Finality callback / native transfer",
                  state: "SUBMITTED",
                  created: Date.now(),
                });
            return next;
          });
          if (data.state === "FINALIZED_SUCCESS") {
            if (data.createdId) setSelected(data.createdId);
            void update(
              data.createdId ??
                (view === "take" || view === "resolve" ? selected : undefined),
            );
          }
        } catch {}
      }
    };
    const timer = setInterval(() => void poll(), 10000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [txs, update, view, selected]);
  // Loading a new URL synchronizes the view with external finalized chain state.
  useEffect(() => {
    if (!takeId || initial.takes.some((e) => e.take.id === takeId)) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void update(takeId);
  }, [initial.takes, takeId, update]);
  const track = (hash: string, label: string, refresh = false) =>
    setTxs((old) =>
      old.some((t) => t.hash === hash)
        ? refresh
          ? old.map((t) =>
              t.hash === hash
                ? {
                    ...t,
                    state: "SUBMITTED",
                    error: undefined,
                    appealDeadline: null,
                  }
                : t,
            )
          : old
        : [...old, { hash, label, state: "SUBMITTED", created: Date.now() }],
    );
  async function connect() {
    setError("");
    setBusy("wallet");
    try {
      const w = await connectWallet();
      setAccount(w.account);
      sessionStorage.setItem("called-it-account", w.account);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Wallet connection cancelled.");
    } finally {
      setBusy("");
    }
  }
  async function send(
    label: string,
    contract: string,
    method: string,
    args: unknown[],
    value = 0n,
  ) {
    setBusy(label);
    setError("");
    let submitted = "";
    try {
      const addr = proof.contracts[contract]?.address;
      if (!addr)
        throw Error(
          "Deployment is not recorded. Open The receipts for release status.",
        );
      const w = await connectWallet((h) => {
        submitted = h;
        track(h, label);
      });
      setAccount(w.account);
      sessionStorage.setItem("called-it-account", w.account);
      const hash = await w.client.writeContract({
        address: addr as `0x${string}`,
        functionName: method,
        args: args as never[],
        value,
        consensusMaxRotations: 2,
      });
      if (typeof hash !== "string" || !/^0x[\da-f]{64}$/i.test(hash))
        throw Error("Wallet returned an unrecognized transaction hash.");
      track(hash, label);
    } catch (e) {
      setError(
        (e instanceof Error ? e.message : "Transaction cancelled.") +
          (submitted ? " Your submitted hash is saved in Transactions." : ""),
      );
    } finally {
      setBusy("");
    }
  }
  function action(
    label: string,
    contract: string,
    method: string,
    args: unknown[],
    disabled = false,
    value = 0n,
  ) {
    return (
      <button
        className="button"
        disabled={!!busy || disabled}
        onClick={() => void send(label, contract, method, args, value)}
      >
        {busy === label ? <LoaderCircle size={17} className="spin" /> : null}
        {label}
        <ArrowUpRight size={16} />
      </button>
    );
  }
  const liveProfile =
    profile?.wallet.toLowerCase() === profileAddress.toLowerCase()
      ? profile
      : null;
  const p = liveProfile ??
    proof.profiles?.find(
      (p) =>
        p.wallet.toLowerCase() ===
        (profileAddress || proof.demoWallets?.[0] || "").toLowerCase(),
    ) ?? { ...EMPTY, wallet: profileAddress };
  const profileKnown =
    !!liveProfile ||
    !!proof.profiles?.some(
      (record) => record.wallet.toLowerCase() === p.wallet.toLowerCase(),
    );
  async function loadProfile(wallet: string) {
    setLoading(true);
    setError("");
    try {
      const r = await fetch("/api/profile/" + wallet, { cache: "no-store" });
      const data = await r.json();
      if (!r.ok) throw Error(data.error);
      setProfile(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Profile unavailable");
    } finally {
      setLoading(false);
    }
  }
  const entries = proof.takes.filter(
    (e) =>
      (filter === "all" || e.take.category === filter) &&
      (tab === "all" ||
        (tab === "open" &&
          !e.take.historical &&
          e.take.status === "COMPILED" &&
          e.bet.status === "OPEN" &&
          !e.resolution.outcome) ||
        (tab === "resolved" && e.resolution.status === "FINAL") ||
        (tab === "rejected" && e.take.status === "REJECTED")),
  );
  const open = proof.takes.filter(
    (e) =>
      !e.take.historical &&
      e.take.status === "COMPILED" &&
      !e.resolution.outcome,
  );
  const resolved = proof.takes.filter((e) => e.resolution.status === "FINAL");
  const board = [...(proof.profiles ?? [])].sort(
    (a, b) => b.wins - a.wins || a.losses - b.losses,
  );
  const title =
    view === "feed"
      ? "Talk is cheap."
      : view === "post"
        ? "Put it on the record."
        : view === "resolve"
          ? "Bring your receipts."
          : view === "profile"
            ? "Your takes. Your record."
            : view === "proof"
              ? "Nothing behind the curtain."
              : view === "transactions"
                ? "Follow the final word."
                : "The full receipt.";
  return (
    <div className="shell">
      <a className="skip" href="#main">
        Skip to content
      </a>
      <aside className="sidebar">
        <Link className="logo" href="/" aria-label="Called It home">
          CALLED
          <span>
            IT<span className="logo-dot">.</span>
          </span>
          <span className="logo-check">
            <CheckCheck size={30} />
          </span>
        </Link>
        <p className="brand-line">A take. A stake. A receipt.</p>
        <nav aria-label="Main navigation">
          {NAV.map(({ view: v, href, label, Icon }) => (
            <Link
              key={v}
              href={href}
              className={view === v ? "nav active" : "nav"}
            >
              <Icon size={19} />
              {label}
              {view === v && <span className="nav-dot" />}
            </Link>
          ))}
        </nav>
        <Link href="/post" className="button post-button">
          <Plus size={20} />
          Post a take
        </Link>
        <div className="sidebar-bottom">
          <ShieldCheck size={22} />
          <p>
            Judgment by GenLayer.
            <br />
            The record is yours.
          </p>
          <span>STUDIONET · 61999</span>
          <small>Demo GEN has no real-world value.</small>
        </div>
      </aside>
      <div className="body">
        <header className="topbar">
          <Link href="/" className="mobile-logo">
            CALLED IT.
          </Link>
          <span className="network">
            <i />
            THE RECEIPTS DON’T LIE.
          </span>
          <button
            className="share-page"
            onClick={async () => {
              const path =
                (view === "take" || view === "resolve") && current
                  ? "/take/" + current.take.id
                  : view === "profile" && /^0x[\da-f]{40}$/i.test(p.wallet)
                    ? "/profile/" + p.wallet
                    : window.location.pathname;
              const shareURL = new URL(path, window.location.origin).href;
              try {
                await navigator.clipboard.writeText(shareURL);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              } catch {
                setError("Copy this link to share the receipt: " + shareURL);
              }
            }}
            aria-label="Copy page link"
          >
            {copied ? <Check size={17} /> : <Copy size={17} />}
            <span>{copied ? "Copied" : "Share"}</span>
          </button>
          <button
            className="wallet"
            disabled={!!busy}
            onClick={() => void connect()}
          >
            <Wallet size={16} />
            {account ? short(account) : "Connect wallet"}
          </button>
        </header>
        <main id="main">
          {!!proof.legacyLiveTakes?.length &&
            (view === "feed" || view === "proof") && (
              <div className="notice">
                <strong>
                  Two earlier live takes remain on the previous contracts.
                </strong>
                <p>
                  The fairness policy below applies to this deployment. The
                  funded October 29 and November 4 takes retain their original
                  immutable rules and refund deadlines.{" "}
                  <External
                    href={
                      (proof.github ?? "https://github.com/JWattjr/called-it") +
                      "/blob/main/deploy/releases/v2-proof.json"
                    }
                  >
                    Read the previous deployment and live-take receipts
                  </External>
                  .
                </p>
              </div>
            )}
          <div className="heading">
            <div>
              <h1>{title}</h1>
              <p>
                {view === "feed"
                  ? "Put GEN on your hot take. Let the evidence do the talking."
                  : view === "post"
                    ? "Say it plainly. Review the rule. Then back yourself."
                    : view === "resolve"
                      ? "Official announcements count. “In talks” doesn’t."
                      : view === "profile"
                        ? "A public record built from finalized, head-to-head results."
                        : view === "proof"
                          ? "Frozen rules, evidence and finalized on-chain transactions."
                          : view === "transactions"
                            ? "Accepted is provisional. Finalized is the receipt."
                            : "Every rule, source and ruling in one place."}
              </p>
            </div>
            {view === "feed" && (
              <Link href="/post" className="button heading-post">
                <Plus size={19} />
                Post a take
              </Link>
            )}
          </div>
          {error && (
            <div className="error" role="alert">
              <span>{error}</span>
              <button onClick={() => setError("")} aria-label="Dismiss error">
                <X size={18} />
              </button>
            </div>
          )}
          <div className="provenance">
            <span>
              <ShieldCheck size={14} />
              {live
                ? liveScope
                  ? `Live read for ${liveScope} · other takes recorded`
                  : "Live finalized-state read"
                : "Recorded chain proof"}
              {proof.recordedAt
                ? " · " +
                  new Date(proof.recordedAt).toLocaleDateString("en-GB", {
                    timeZone: "UTC",
                  })
                : " · deployment in progress"}
            </span>
            <button
              disabled={loading}
              onClick={() => {
                if (
                  view === "profile" &&
                  /^0x[\da-f]{40}$/i.test(profileAddress || p.wallet)
                ) {
                  if (!profileAddress) setProfileQuery(p.wallet);
                  void loadProfile(profileAddress || p.wallet);
                } else
                  void update(
                    view === "take" || view === "resolve"
                      ? selected
                      : undefined,
                  );
              }}
            >
              <RefreshCw size={14} className={loading ? "spin" : ""} />
              {loading ? "Reading…" : "Read live"}
            </button>
          </div>
          <div className={view === "feed" ? "content-grid" : "content-single"}>
            <section className="primary">
              {view === "feed" && (
                <>
                  <div
                    className="feed-tabs"
                    role="group"
                    aria-label="Take status"
                  >
                    {[
                      ["all", "All takes"],
                      ["open", "Open to challenge"],
                      ["resolved", "The verdicts"],
                      ["rejected", "Rejected"],
                    ].map(([id, label]) => (
                      <button
                        key={id}
                        aria-pressed={tab === id}
                        className={tab === id ? "selected" : ""}
                        onClick={() => setTab(id)}
                      >
                        {label}
                        {id === "open" && <span>{open.length}</span>}
                      </button>
                    ))}
                  </div>
                  <div
                    className="category-filter"
                    aria-label="Filter by category"
                  >
                    {CATEGORIES.map((c) => (
                      <button
                        aria-pressed={filter === c}
                        className={filter === c ? "selected" : ""}
                        key={c}
                        onClick={() => setFilter(c)}
                      >
                        {c === "all"
                          ? "Everything"
                          : c === "tech"
                            ? "Tech & products"
                            : c === "sports"
                              ? "Sports business"
                              : c[0].toUpperCase() + c.slice(1)}
                      </button>
                    ))}
                  </div>
                  {!entries.length && (
                    <div className="empty">
                      <Receipt size={30} />
                      <h2>No takes here yet.</h2>
                      <p>
                        {proof.takes.length
                          ? "Try another category or status."
                          : "The release is in progress. New takes will appear once their compiled rules finalize."}
                      </p>
                      <Link href="/post" className="text-link">
                        Be the first to call it <ArrowRight size={16} />
                      </Link>
                    </div>
                  )}
                  <div className="take-feed">
                    {[...entries]
                      .sort(
                        (a, b) =>
                          Number(a.take.historical) -
                            Number(b.take.historical) ||
                          Number(a.take.status === "REJECTED") -
                            Number(b.take.status === "REJECTED"),
                      )
                      .map((e) => (
                        <TakeCard
                          key={e.take.id}
                          entry={e}
                          profiles={proof.profiles ?? []}
                        />
                      ))}
                  </div>
                </>
              )}
              {view === "post" && (
                <PostForm
                  busy={busy}
                  send={send}
                  compiled={current}
                  select={setSelected}
                  entries={proof.takes}
                  action={action}
                  account={account}
                />
              )}
              {(view === "take" || view === "resolve") && (
                <>
                  <label className="field">
                    Choose a take
                    <select
                      value={selected}
                      onChange={(e) => setSelected(e.target.value)}
                    >
                      <option value="">Select a take</option>
                      {proof.takes.map((e) => (
                        <option key={e.take.id} value={e.take.id}>
                          {e.take.id} · {e.take.text.slice(0, 75)}
                        </option>
                      ))}
                    </select>
                  </label>
                  {current ? (
                    <ReceiptDetail
                      key={current.take.id}
                      entry={current}
                      account={account}
                      action={action}
                      proof={proof}
                      busy={busy}
                      connect={() => void connect()}
                    />
                  ) : (
                    <div className="empty">
                      <h2>
                        {loading
                          ? "Reading this take…"
                          : "Take not in this snapshot."}
                      </h2>
                      <p>
                        Read live state to load a take created after this
                        release.
                      </p>
                      <button
                        className="button"
                        onClick={() => void update(takeId)}
                      >
                        Read this take <RefreshCw size={16} />
                      </button>
                    </div>
                  )}
                </>
              )}
              {view === "profile" && (
                <>
                  <RefundCredit account={account} action={action} />
                  <div className="profile-controls">
                    <label className="field">
                      Wallet address
                      <input
                        placeholder="0x… or connect your wallet"
                        value={profileAddress}
                        onChange={(e) => setProfileQuery(e.target.value)}
                      />
                    </label>
                    <button
                      className="button"
                      disabled={
                        !/^0x[\da-f]{40}$/i.test(profileAddress) || loading
                      }
                      onClick={() => void loadProfile(profileAddress)}
                    >
                      Read live profile <RefreshCw size={16} />
                    </button>
                  </div>
                  {!profileAddress && (
                    <p className="notice">
                      Showing the recorded demo profile. Connect a wallet to
                      read your own record.
                    </p>
                  )}
                  <div className="profile-head">
                    <Avatar wallet={p.wallet || "0x00"} large />
                    <div>
                      <h2>
                        {p.wallet ? short(p.wallet) : "Your record starts here"}
                      </h2>
                      <p>
                        {liveProfile ||
                        (live &&
                          proof.profiles?.some(
                            (record) =>
                              record.wallet.toLowerCase() ===
                              p.wallet.toLowerCase(),
                          ))
                          ? "Live finalized record"
                          : proof.profiles?.some(
                                (record) =>
                                  record.wallet.toLowerCase() ===
                                  p.wallet.toLowerCase(),
                              )
                            ? "Recorded profile"
                            : "No recorded profile · read live to load"}{" "}
                        ·{" "}
                        <span className="streak">
                          <Flame size={14} />
                          {profileKnown
                            ? `${Math.abs(p.streak)} ${p.streak < 0 ? "loss" : "win"} streak`
                            : "Record not loaded"}
                        </span>
                      </p>
                    </div>
                  </div>
                  <div className="record-stats">
                    <div>
                      <strong>{profileKnown ? p.wins : "—"}</strong>
                      <span>Called it</span>
                    </div>
                    <div>
                      <strong>{profileKnown ? p.losses : "—"}</strong>
                      <span>Missed</span>
                    </div>
                    <div>
                      <strong>{profileKnown ? p.voids : "—"}</strong>
                      <span>Void</span>
                    </div>
                    <div>
                      <strong>
                        {profileKnown
                          ? `${p.wins + p.losses ? Math.round((p.wins / (p.wins + p.losses)) * 100) : 0}%`
                          : "—"}
                      </strong>
                      <span>Accuracy</span>
                    </div>
                  </div>
                  <h2 className="section-title">Where you call it</h2>
                  <div className="category-records">
                    {Object.entries(p.categories).map(([c, v]) => (
                      <div key={c}>
                        <strong>{c}</strong>
                        <span>
                          {v.wins}W / {v.losses}L / {v.voids}V
                        </span>
                        <span>
                          {v.wins + v.losses
                            ? Math.round((v.wins / (v.wins + v.losses)) * 100)
                            : 0}
                          % accuracy
                        </span>
                      </div>
                    ))}
                  </div>
                  <h2 className="section-title">The paper trail</h2>
                  {p.history.length ? (
                    p.history.map((h) => (
                      <Link
                        className="history-row"
                        key={h.id}
                        href={"/take/" + h.id}
                      >
                        <span>
                          <strong>
                            {proof.takes.find((entry) => entry.take.id === h.id)
                              ?.take.text ?? h.id}
                          </strong>
                          <small>
                            {h.id} ·{" "}
                            {h.historical ? "Historical replay" : "Live take"} ·{" "}
                            {h.category}
                            {h.resolution_case ? " · " + h.resolution_case : ""}
                          </small>
                        </span>
                        <span
                          className={
                            h.result === "WIN"
                              ? "green"
                              : h.result === "LOSS"
                                ? "red"
                                : ""
                          }
                        >
                          {h.result}
                        </span>
                        <ArrowUpRight size={17} />
                      </Link>
                    ))
                  ) : (
                    <p className="notice">
                      {profileKnown
                        ? "Only finalized matched settlements enter the record. Open or unfunded takes add no wins."
                        : "Read this wallet’s live record to load its finalized history."}
                    </p>
                  )}
                </>
              )}
              {view === "proof" && (
                <>
                  <div className="proof-intro">
                    <Receipt size={35} />
                    <h2>Trust the trail.</h2>
                    <p>
                      Each judgment is narrow. Each stake is counted by code.
                      Historical replays use past event windows and are labelled
                      throughout.
                    </p>
                    <span className="status-tag">
                      {proof.releaseStatus.replaceAll("_", " ")}
                    </span>
                  </div>
                  <h2 className="section-title">
                    Four contracts. Two judgments.
                  </h2>
                  {proof.limitations?.length ? (
                    <div className="notice">
                      <strong>What this demo proves</strong>
                      <ul>
                        {proof.limitations.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  <div className="contract-list">
                    {[
                      "Takes",
                      "TakeEscrow",
                      "TakeResolver",
                      "CalledItRecord",
                    ].map((name, i) => (
                      <div key={name}>
                        <span className="contract-num">{i + 1}</span>
                        <div>
                          <h3>{name}</h3>
                          <p>
                            {
                              [
                                "Compiles and freezes the rule · AI judgment",
                                "Holds stakes, settles, refunds and pays · code",
                                "Checks frozen evidence and rules · AI judgment",
                                "Counts finalized wins, losses and voids · code",
                              ][i]
                            }
                          </p>
                          {proof.contracts[name] ? (
                            <External
                              href={explorer(
                                "address",
                                proof.contracts[name].address,
                              )}
                            >
                              {short(proof.contracts[name].address)}
                            </External>
                          ) : (
                            <small>Deployment not recorded</small>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  <h2 className="section-title">Transaction receipts</h2>
                  <p className="muted">
                    Lifecycle finality and execution success are checked
                    separately. Native transfers and finality callbacks have
                    their own receipts.
                  </p>
                  <div className="receipt-list">
                    {Object.entries(proof.transactions).map(([name, h]) => (
                      <div key={name}>
                        <span>{name.replaceAll("-", " ")}</span>
                        <External href={explorer("tx", h)}>{short(h)}</External>
                      </div>
                    ))}
                  </div>
                  {proof.github && (
                    <External href={proof.github}>
                      Source code & read-only proof verifier
                    </External>
                  )}
                  {proof.blockers?.length ? (
                    <div className="notice">
                      <strong>Release blockers</strong>
                      <ul>
                        {proof.blockers.map((b) => (
                          <li key={b}>{b}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </>
              )}
              {(view === "transactions" || txs.length > 0) && (
                <section
                  className="transactions"
                  aria-label="Transaction tracker"
                >
                  <TransactionImport
                    track={(hash) => track(hash, "Tracked transaction", true)}
                  />
                  <div className="section-heading">
                    <h2>Your transactions</h2>
                    <span>10s polling</span>
                  </div>
                  {!txs.length ? (
                    <p>
                      Submitted hashes persist across reloads. Callbacks and
                      native payouts are tracked separately.
                    </p>
                  ) : (
                    txs
                      .slice()
                      .reverse()
                      .map((t) => (
                        <div className="transaction" key={t.hash}>
                          <div>
                            <strong>{t.label}</strong>
                            <span
                              className={
                                t.state === "FINALIZED_SUCCESS"
                                  ? "green"
                                  : t.state === "FINALIZED_ERROR"
                                    ? "red"
                                    : ""
                              }
                            >
                              {TXLABEL[t.state]}
                              {t.appealDeadline && t.state === "ACCEPTED"
                                ? " · appeal until " +
                                  datetime(t.appealDeadline)
                                : ""}
                            </span>
                            {t.error && (
                              <p className="red">{receiptError(t.error)}</p>
                            )}
                          </div>
                          <External href={explorer("tx", t.hash)}>
                            {short(t.hash)}
                          </External>
                        </div>
                      ))
                  )}
                  <Link className="text-link" href="/transactions">
                    Open transaction tracker <ArrowRight size={15} />
                  </Link>
                </section>
              )}
            </section>
            {view === "feed" && (
              <aside className="right-rail">
                <div className="put-up">
                  <h2>
                    Got a take?
                    <br />
                    Make it count.
                  </h2>
                  <p>
                    Your friend takes NO.
                    <br />
                    The evidence picks a side.
                  </p>
                  <Link className="ink-button" href="/post">
                    Put it on the record <ArrowUpRight size={18} />
                  </Link>
                  <span className="receipt-cut" />
                </div>
                <section className="leaderboard">
                  <div className="section-heading">
                    <h2>The ones who called it</h2>
                    <Trophy size={18} />
                  </div>
                  <p>Finalized matched bets only</p>
                  {board.length ? (
                    board.map((p, i) => (
                      <Link
                        href={"/profile/" + p.wallet}
                        className="leader"
                        key={p.wallet}
                      >
                        <span className="rank">{i + 1}</span>
                        <Avatar wallet={p.wallet} />
                        <span>
                          <strong>{short(p.wallet)}</strong>
                          <small>
                            {p.wins} called · {p.losses} missed
                          </small>
                        </span>
                        <b>
                          {p.wins + p.losses
                            ? Math.round((p.wins / (p.wins + p.losses)) * 100)
                            : 0}
                          %
                        </b>
                      </Link>
                    ))
                  ) : (
                    <div className="board-empty">
                      <Trophy size={22} />
                      <p>
                        The record starts after the first funded bet settles.
                      </p>
                    </div>
                  )}
                </section>
                <section className="how">
                  <h2>No moving goalposts.</h2>
                  <p>
                    <Check size={16} />
                    The rule freezes before you stake.
                  </p>
                  <p>
                    <Check size={16} />
                    Archived evidence. Official sources.
                  </p>
                  <p>
                    <Check size={16} />
                    Code owns the payout.
                  </p>
                  <Link className="text-link" href="/proof">
                    See how it’s judged <ArrowRight size={15} />
                  </Link>
                </section>
                <div className="feed-count">
                  <span>{open.length} open takes</span>
                  <span>{resolved.length} on the record</span>
                </div>
              </aside>
            )}
          </div>
          <footer>
            <span>YOU SAID IT. NOW PROVE IT.</span>
            <Link href="/proof">StudioNet demo · proof & limitations</Link>
          </footer>
        </main>
      </div>
      <nav className="mobile-nav" aria-label="Mobile navigation">
        <Link href="/">
          <Home size={20} />
          Feed
        </Link>
        <Link href="/post">
          <Plus size={20} />
          Post
        </Link>
        <Link href="/resolve">
          <Scale size={20} />
          Settle
        </Link>
        <Link href="/profile">
          <UserRound size={20} />
          Record
        </Link>
      </nav>
    </div>
  );
}

function TakeCard({ entry, profiles }: { entry: Entry; profiles: Profile[] }) {
  const { take: t, bet: b, resolution: r } = entry;
  const p = profiles.find((p) => p.wallet === t.author);
  const final = r.status === "FINAL";
  const rejected = t.status === "REJECTED";
  return (
    <article className={"take-card " + (final ? "settled-card" : "")}>
      <div className="card-top">
        <Link className="author" href={"/profile/" + t.author}>
          <Avatar wallet={t.author} />
          <span>
            <strong>{short(t.author)}</strong>
            <small>
              {p
                ? `${p.wins} called · ${p.losses} missed`
                : "View public record"}
            </small>
          </span>
        </Link>
        <span className="category">{t.category}</span>
      </div>
      <Link href={"/take/" + t.id} className="take-title">
        <h2>{t.text}</h2>
      </Link>
      <div className="take-meta">
        <span>
          <Clock3 size={14} />
          {date(t.rule.deadline)}
        </span>
        <span>{t.historical ? "Historical replay" : "Live take"}</span>
        {rejected ? (
          <span className="red">Rejected at compile</span>
        ) : (
          <span>
            <ShieldCheck size={14} />
            Rule frozen
          </span>
        )}
      </div>
      {final ? (
        <div className="verdict-strip">
          <Stamp outcome={r.outcome ?? "VOID"} />
          <p>
            {r.default_applied
              ? "Frozen default applied"
              : r.outcome === "YES"
                ? "The official announcement settled it."
                : r.outcome === "NO"
                  ? "Reports didn’t meet the rule."
                  : "Both stakes go back."}
          </p>
        </div>
      ) : rejected ? (
        <p className="rejected-reason">{rejectionLabel(t.decision)}</p>
      ) : (
        <div className="stake-line">
          <span>
            <strong>{amount(t.stake_wei)}</strong>
            <small>author’s stake</small>
          </span>
          <span className="odds">
            1 : {t.ratio}
            <small>odds</small>
          </span>
          <Link className="button" href={"/take/" + t.id}>
            {b.status === "OPEN"
              ? "Take the other side"
              : b.status === "MATCHED"
                ? "View head-to-head"
                : b.status === "PREPARED"
                  ? "Review & fund"
                  : "Review the rule"}
            <ArrowUpRight size={17} />
          </Link>
        </div>
      )}
      <div className="card-bottom">
        <span>
          {t.id.toUpperCase()} · {t.rule_hash.slice(0, 8)}
        </span>
        <Link href={"/take/" + t.id}>
          {final ? "Open the receipt" : "Read the frozen rule"}
          <ArrowRight size={14} />
        </Link>
      </div>
    </article>
  );
}

type Action = (
  label: string,
  contract: string,
  method: string,
  args: unknown[],
  disabled?: boolean,
  value?: bigint,
) => React.ReactNode;
function ReceiptDetail({
  entry,
  account,
  action,
  proof,
  busy,
  connect,
}: {
  entry: Entry;
  account: string;
  action: Action;
  proof: Proof;
  busy: string;
  connect: () => void;
}) {
  const { take: t, bet: b, resolution: r } = entry;
  const [url, setUrl] = useState(""),
    [argument, setArgument] = useState(""),
    [preview, setPreview] = useState(""),
    [checking, setChecking] = useState(false),
    [reviewedPreflight, setReviewedPreflight] = useState("");
  const [clock, setClock] = useState(0);
  useEffect(() => {
    const tick = () => setClock(Date.now() / 1000);
    const first = setTimeout(tick, 0),
      timer = setInterval(tick, 10000);
    return () => {
      clearTimeout(first);
      clearInterval(timer);
    };
  }, []);
  const isAuthor = !!account && account === t.author,
    isCounter = !!account && account === b.counterparty,
    party = isAuthor || isCounter;
  const expired = clock >= t.accept_deadline;
  const eventClosed = t.historical || clock > t.rule.deadline;
  const sealed = r.sealed?.includes(account);
  const ownPreflightKey = JSON.stringify(
    r.evidence?.filter((e) => e.party === account) ?? [],
  );
  const claim = b.claims?.[account];
  const available =
    BigInt(b.payouts?.[account] ?? "0") > 0n &&
    (!claim || claim.status === "FAILED");
  async function preflight() {
    setChecking(true);
    try {
      const shape = evidenceShape(url, t.rule);
      const response = await fetch("/api/preflight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: t.id, url }),
      });
      const p = await response.json();
      if (!response.ok) throw Error(p.error);
      setPreview(
        shape +
          " " +
          p.message +
          " Preflight: " +
          p.status +
          (p.error ? " · " + p.error : "") +
          " Capture: " +
          datetime(p.capture) +
          " Extracted main text (" +
          p.boundedLength +
          " characters; first 2,000 shown): " +
          p.text,
      );
    } catch (e) {
      setPreview(e instanceof Error ? e.message : "Preflight failed.");
    } finally {
      setChecking(false);
    }
  }
  return (
    <div className="receipt-detail">
      <div className="receipt-banner">
        <span>{t.historical ? "HISTORICAL REPLAY" : "LIVE TAKE"}</span>
        <span>{t.id.toUpperCase()}</span>
      </div>
      <h2 className="detail-title">{t.text}</h2>
      <p className="detail-by">
        Posted by <Link href={"/profile/" + t.author}>{short(t.author)}</Link> ·{" "}
        {date(t.created_at)}
      </p>
      {t.status === "REJECTED" ? (
        <div className="notice red">
          <strong>Rejected · {t.decision}</strong>
          <p>{rejectionLabel(t.decision)}</p>
          <p>Compiler explanation, verbatim: {t.reason}</p>
        </div>
      ) : (
        <>
          <section className="frozen-rule">
            <div className="section-heading">
              <h3>
                <ShieldCheck size={19} />
                The frozen rule
              </h3>
              <span>{t.status}</span>
            </div>
            <p className="proposition">{t.rule.proposition}</p>
            <dl>
              <dt>YES requires</dt>
              <dd>{t.rule.yes}</dd>
              <dt>Doesn’t count</dt>
              <dd>{t.rule.does_not_count}</dd>
              <dt>Event window</dt>
              <dd>
                After {datetime(t.rule.as_of)} through{" "}
                {datetime(t.rule.deadline)}
              </dd>
              <dt>Default</dt>
              <dd>
                {t.rule.default}{" "}
                {t.rule.technical_failure_policy
                  ? "only if nobody submits evidence. Source failures, inconclusive evidence and consensus timeout resolve VOID."
                  : "under this legacy rule, including its original technical-failure fallbacks."}
              </dd>
              <dt>Allowed sources</dt>
              <dd className="domains">
                {t.rule.domains.join(" · ")}
                {t.rule.technical_failure_policy && (
                  <p>
                    Known blocked origins are rejected before fetch:
                    reuters.com, apnews.com, oscars.org.
                  </p>
                )}
              </dd>
              <dt>Rule SHA-256</dt>
              <dd className="hash">{t.rule_hash}</dd>
            </dl>
          </section>
          {entry.context && (
            <p className="context">
              <strong>Why this take exists</strong>
              <br />
              {entry.context.summary}{" "}
              <External href={entry.context.url}>Official context</External>
            </p>
          )}
          <section className="match-panel">
            <div className="section-heading">
              <h3>The head-to-head</h3>
              <span>{b.status ?? "UNFUNDED"}</span>
            </div>
            <div className="opponents">
              <div>
                <span>YES · AUTHOR</span>
                <strong>{amount(t.stake_wei)}</strong>
                <small>{short(t.author)}</small>
              </div>
              <b>VS</b>
              <div>
                <span>NO · OTHER SIDE</span>
                <strong>
                  {amount((BigInt(t.stake_wei) * BigInt(t.ratio)).toString())}
                </strong>
                <small>
                  {b.counterparty ? short(b.counterparty) : "Your name here"}
                </small>
              </div>
            </div>
            <p>
              Winner takes {amount(payout(t.stake_wei, t.ratio))}. Void refunds
              both stakes. No platform cut.
            </p>
            <p className="muted">
              Accept by {datetime(t.accept_deadline)}. Evidence closes{" "}
              {datetime(t.evidence_deadline)}. Finality callbacks must complete
              before the next action.
            </p>
            {!account && b.status !== "SETTLED" && (
              <button className="button" disabled={!!busy} onClick={connect}>
                <Wallet size={16} /> Connect wallet to take the other side
              </button>
            )}
            {isAuthor &&
              !b.status &&
              !expired &&
              action("Prepare author stake", "TakeEscrow", "prepare_open", [
                t.id,
              ])}
            {isAuthor && b.status === "PREPARED" && (
              <>
                {clock >= (b.intent_expires ?? 0)
                  ? action(
                      "Renew stake preflight",
                      "TakeEscrow",
                      "prepare_open",
                      [t.id],
                    )
                  : action(
                      "Stake " + amount(t.stake_wei),
                      "TakeEscrow",
                      "deposit",
                      [t.id],
                      false,
                      BigInt(t.stake_wei),
                    )}
              </>
            )}
            {!!account && !isAuthor && b.status === "OPEN" && !expired && (
              <>
                {b.intent_wallet === account && clock < (b.intent_expires ?? 0)
                  ? action(
                      "Match " + amount(b.counter_stake ?? "0"),
                      "TakeEscrow",
                      "deposit",
                      [t.id],
                      false,
                      BigInt(b.counter_stake ?? "0"),
                    )
                  : action(
                      "Take the other side · preflight",
                      "TakeEscrow",
                      "prepare_accept",
                      [t.id],
                    )}
              </>
            )}
            {b.status === "SETTLED" ? (
              <>
                <p className="green">
                  <CheckCheck size={17} />
                  Settlement finalized · {b.outcome}
                </p>
                {available &&
                  action(
                    "Claim " + amount(b.payouts?.[account] ?? "0"),
                    "TakeEscrow",
                    "claim",
                    [t.id, (claim?.attempt ?? 0) + 1],
                  )}
                <div className="public-payouts">
                  {Object.entries(b.payouts ?? {})
                    .filter(([, value]) => BigInt(value) > 0n)
                    .map(([wallet, value]) => {
                      const paid = b.claims?.[wallet];
                      return (
                        <div key={wallet}>
                          <p>
                            <Link href={"/profile/" + wallet}>
                              {short(wallet)}
                            </Link>{" "}
                            · {amount(value)}
                          </p>
                          <p
                            className={
                              paid?.status === "PAID"
                                ? "green"
                                : paid?.status === "FAILED"
                                  ? "red"
                                  : "muted"
                            }
                          >
                            {paid?.status === "PAID"
                              ? "Paid & verified"
                              : paid?.status === "FAILED"
                                ? "Transfer failed · retry available"
                                : paid
                                  ? "Payout verification pending"
                                  : "Not yet claimed"}
                          </p>
                          {paid?.parent && (
                            <External href={explorer("tx", paid.parent)}>
                              Claim receipt
                            </External>
                          )}
                          {paid?.child && (
                            <External href={explorer("tx", paid.child)}>
                              Native transfer receipt
                            </External>
                          )}
                        </div>
                      );
                    })}
                </div>
                {claim?.status === "PENDING" && (
                  <VerifyClaim
                    take={t.id}
                    account={account}
                    attempt={claim.attempt}
                    action={action}
                  />
                )}
                <div className="action-row">
                  {b.counterparty &&
                    action("Update public record", "CalledItRecord", "sync", [
                      t.id,
                    ])}
                </div>
              </>
            ) : (
              <>
                {(r.status === "FINAL" ||
                  (expired && ["OPEN", "PREPARED"].includes(b.status ?? "")) ||
                  clock >= (b.refund_deadline ?? Infinity)) &&
                  b.status &&
                  action(
                    r.status === "FINAL"
                      ? "Settle finalized result"
                      : "Settle deadline refund",
                    "TakeEscrow",
                    "settle",
                    [t.id],
                  )}
              </>
            )}
          </section>
          <section className="ruling">
            <div className="section-heading">
              <h3>The ruling</h3>
              {r.status === "FINAL" ? (
                <Stamp outcome={r.outcome ?? "VOID"} />
              ) : (
                <span>{r.status ?? "AWAITING EVIDENCE"}</span>
              )}
            </div>
            {r.resolution_case && <p className="notice">{r.resolution_case}</p>}
            {r.reason && <p>{r.reason}</p>}
            {t.rule.technical_failure_policy && (
              <p className="muted">
                Technical failure policy: {t.rule.technical_failure_policy}.
                VOID refunds each original stake in full.
              </p>
            )}
            {r.default_applied && (
              <p className="notice">
                Code applied the rule’s {t.rule.default} default. This is not a
                model-confirmed {r.outcome} verdict.
              </p>
            )}
            {r.quotes?.map((q, i) => (
              <blockquote key={i}>
                <p>“{q.text}”</p>
                <cite>
                  {r.evidence?.[q.index]?.url && (
                    <External href={r.evidence[q.index].url}>
                      Frozen evidence · source {q.index + 1}
                    </External>
                  )}
                </cite>
              </blockquote>
            ))}
            {r.evidence?.length ? (
              <div className="evidence-list">
                {r.evidence.map((e, i) => (
                  <div key={e.url}>
                    <strong>
                      Source {i + 1} · {short(e.party)}
                    </strong>
                    <External href={e.url}>Open immutable evidence</External>
                    {e.argument && <p>Party argument: {e.argument}</p>}
                    {e.preflight && (
                      <p className="notice">
                        Submission preflight: {e.preflight.status} ·{" "}
                        {e.preflight.length ?? 0} characters ·{" "}
                        {datetime(e.preflight.checked_at)}
                        {e.preflight.error ? " · " + e.preflight.error : ""}.
                        Resolution fetches the source again; technical failure
                        refunds both stakes.
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted">No evidence links submitted.</p>
            )}
            {r.status === "RESOLVING" && (
              <div className="notice">
                <p>
                  If consensus has not finalized by{" "}
                  {datetime(t.evidence_deadline + 48 * 3600)}, resolve the
                  timeout as VOID and refund both original stakes.
                </p>
                {clock >= t.evidence_deadline + 48 * 3600 &&
                  action("Resolve timeout as VOID", "TakeResolver", "resolve", [
                    t.id,
                  ])}
              </div>
            )}
            {r.status !== "FINAL" && r.status !== "RESOLVING" && (
              <>
                <p className="muted">
                  Each party can submit up to two permanent links after the
                  event deadline. Both parties may seal early; otherwise the
                  evidence window stays open.
                </p>
                {eventClosed && clock < t.evidence_deadline && (
                  <div className="evidence-form">
                    <label className="field">
                      Permanent evidence URL
                      <input
                        type="url"
                        value={url}
                        onChange={(e) => {
                          setUrl(e.target.value);
                          setPreview("");
                        }}
                        placeholder="https://web.archive.org/web/…id_/https://…"
                      />
                    </label>
                    <label className="field">
                      Your argument (optional)
                      <textarea
                        maxLength={1000}
                        value={argument}
                        onChange={(e) => setArgument(e.target.value)}
                        placeholder="Point to the official announcement and its date."
                      />
                    </label>
                    <div className="action-row">
                      <button
                        className="secondary"
                        disabled={checking || !url}
                        onClick={() => void preflight()}
                      >
                        {checking ? (
                          <LoaderCircle size={16} className="spin" />
                        ) : null}
                        Preview evidence
                      </button>
                      {action(
                        "Submit evidence",
                        "TakeResolver",
                        "submit_evidence",
                        [t.id, url, argument],
                        !party ||
                          !!sealed ||
                          !preview ||
                          !preview.includes("verified by contract"),
                      )}
                    </div>
                    {preview && (
                      <p className="notice" role="status">
                        {preview}
                      </p>
                    )}
                    {party && r.evidence?.some((e) => e.party === account) && (
                      <label className="notice">
                        <input
                          type="checkbox"
                          checked={reviewedPreflight === ownPreflightKey}
                          onChange={(e) =>
                            setReviewedPreflight(
                              e.target.checked ? ownPreflightKey : "",
                            )
                          }
                        />{" "}
                        I reviewed my submitted evidence preflight results above
                        before sealing.
                      </label>
                    )}
                    {party &&
                      !sealed &&
                      action(
                        "Seal my evidence",
                        "TakeResolver",
                        "seal_evidence",
                        [t.id],
                        !!busy ||
                          (r.evidence?.some((e) => e.party === account) ===
                            true &&
                            reviewedPreflight !== ownPreflightKey),
                      )}
                  </div>
                )}
                {eventClosed &&
                  action(
                    clock >= t.evidence_deadline + 48 * 3600
                      ? "Resolve timeout as VOID"
                      : "Request the ruling",
                    "TakeResolver",
                    "resolve",
                    [t.id],
                    !(
                      clock >= t.evidence_deadline ||
                      [
                        t.author,
                        ...(b.counterparty ? [b.counterparty] : []),
                      ].every((w) => r.sealed?.includes(w))
                    ),
                  )}
              </>
            )}
          </section>
        </>
      )}
      <details className="take-transactions">
        <summary>
          Transaction trail <ChevronDown size={16} />
        </summary>
        {Object.entries(proof.transactions)
          .filter(
            ([name]) =>
              name.includes(t.id) || name.includes(entry.label ?? "__none__"),
          )
          .map(([name, h]) => (
            <div key={name}>
              <span>{name.replaceAll("-", " ")}</span>
              <External href={explorer("tx", h)}>{short(h)}</External>
            </div>
          ))}
        <Link className="text-link" href="/proof">
          All release receipts <ArrowRight size={15} />
        </Link>
      </details>
    </div>
  );
}
function VerifyClaim({
  take,
  account,
  attempt,
  action,
}: {
  take: string;
  account: string;
  attempt: number;
  action: Action;
}) {
  const [parent, setParent] = useState(""),
    [child, setChild] = useState("");
  return (
    <div className="verify-claim">
      <p>
        The native transfer has a separate receipt. Verify the finalized parent
        and child to confirm payment or enable a failed-transfer retry.
      </p>
      <label className="field">
        Claim transaction hash
        <input
          value={parent}
          onChange={(e) => setParent(e.target.value)}
          placeholder="0x…"
        />
      </label>
      <label className="field">
        Native transfer child hash
        <input
          value={child}
          onChange={(e) => setChild(e.target.value)}
          placeholder="0x…"
        />
      </label>
      {action(
        "Verify native payout",
        "TakeEscrow",
        "verify_claim",
        [take, account, attempt, parent, child],
        !/^0x[\da-f]{64}$/i.test(parent) || !/^0x[\da-f]{64}$/i.test(child),
      )}
    </div>
  );
}
function PostForm({
  busy,
  send,
  compiled,
  select,
  entries,
  action,
  account,
}: {
  busy: string;
  send: (
    label: string,
    contract: string,
    method: string,
    args: unknown[],
    value?: bigint,
  ) => Promise<void>;
  compiled?: Entry;
  select: (id: string) => void;
  entries: Entry[];
  action: Action;
  account: string;
}) {
  const [text, setText] = useState(""),
    [category, setCategory] = useState("tech"),
    [deadline, setDeadline] = useState(""),
    [stake, setStake] = useState("2"),
    [ratio, setRatio] = useState(1),
    [fallback, setFallback] = useState("NO"),
    [issue, setIssue] = useState("");
  function submit(e: FormEvent) {
    e.preventDefault();
    setIssue("");
    try {
      const d = Math.floor(new Date(deadline).getTime() / 1000);
      if (
        !Number.isFinite(d) ||
        d < Date.now() / 1000 + 86400 ||
        d > Date.now() / 1000 + 183 * 86400
      )
        throw Error(
          "Choose a deadline between one day and six months from now.",
        );
      payout(stake, ratio);
      if (BigInt(stake) > 10n ** 24n)
        throw Error("The stake exceeds the contract limit.");
      void send("Compile my take", "Takes", "compile", [
        text,
        category,
        d,
        BigInt(stake),
        ratio,
        fallback,
        0,
      ]);
    } catch (e) {
      setIssue(e instanceof Error ? e.message : "Check your take.");
    }
  }
  return (
    <>
      <form className="post-form" onSubmit={submit}>
        <label className="field take-input">
          Your take
          <textarea
            required
            minLength={10}
            maxLength={700}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Apple officially announces a foldable iPhone before March 2027."
          />
          <span>{text.length}/700 · one claim, one outcome</span>
        </label>
        <div className="form-grid">
          <label className="field">
            Category
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {CATEGORIES.slice(1).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Deadline (your local time)
            <input
              type="datetime-local"
              required
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
              onInput={(e) => setDeadline(e.currentTarget.value)}
            />
          </label>
          <label className="field">
            Your stake in wei GEN
            <input
              inputMode="numeric"
              pattern="[1-9][0-9]*"
              required
              value={stake}
              onChange={(e) => setStake(e.target.value)}
            />
            <small>1 GEN = 10¹⁸ wei. Demo amounts can be tiny.</small>
          </label>
          <label className="field">
            Your stake : other side
            <select
              value={ratio}
              onChange={(e) => setRatio(Number(e.target.value))}
            >
              {[1, 2, 3, 4].map((n) => (
                <option key={n} value={n}>
                  1 : {n}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            If nobody submits evidence
            <select
              value={fallback}
              onChange={(e) => setFallback(e.target.value)}
            >
              <option value="NO">NO · other side wins</option>
              <option value="VOID">VOID · both refunded</option>
            </select>
          </label>
        </div>
        <div className="compile-note">
          <ShieldCheck size={23} />
          <p>
            <strong>Read the rule before you stake.</strong>
            <br />
            Compilation sends zero GEN. You’ll review a finalized rule or a
            rejection reason before a separate deposit.
          </p>
        </div>
        <p className="muted">
          Public announcements only. No politics, harm, private individuals,
          health outcomes or asset prices. Compound and subjective claims are
          rejected.
        </p>
        {issue && (
          <p className="error" role="alert">
            {issue}
          </p>
        )}
        <button
          className="button"
          disabled={!!busy || text.length < 10}
          type="submit"
        >
          {busy === "Compile my take" ? (
            <LoaderCircle size={17} className="spin" />
          ) : (
            <Scale size={18} />
          )}
          Compile my take · 0 GEN
          <ArrowRight size={17} />
        </button>
      </form>
      <div className="compiled-preview">
        <h2 className="section-title">
          {account ? "Your compiled rules" : "Compiled rules"}
        </h2>
        <p className="muted">
          After the compilation and its callback finalize, select your take
          here. Use Read live if it isn’t in this snapshot yet.
        </p>
        <label className="field">
          Select a compilation
          <select
            value={compiled?.take.id ?? ""}
            onChange={(e) => select(e.target.value)}
          >
            <option value="">Choose your take</option>
            {entries
              .filter((e) => !account || e.take.author === account)
              .map((e) => (
                <option value={e.take.id} key={e.take.id}>
                  {e.take.id} · {e.take.status} · {e.take.text.slice(0, 70)}
                </option>
              ))}
          </select>
        </label>
        {compiled && (!account || compiled.take.author === account) && (
          <>
            <p className="proposition">
              {compiled.take.status === "REJECTED"
                ? rejectionLabel(compiled.take.decision)
                : compiled.take.rule.proposition}
            </p>
            {compiled.take.status === "REJECTED" && (
              <p className="muted">
                Compiler explanation, verbatim: {compiled.take.reason}
              </p>
            )}
            <Link className="text-link" href={"/take/" + compiled.take.id}>
              {compiled.take.status === "REJECTED"
                ? "Review the rejection"
                : "Review the complete frozen rule"}{" "}
              <ArrowRight size={16} />
            </Link>
            {compiled.take.author === account &&
              compiled.take.status === "COMPILED" &&
              !compiled.bet.status &&
              action("Prepare author stake", "TakeEscrow", "prepare_open", [
                compiled.take.id,
              ])}
          </>
        )}
      </div>
    </>
  );
}

function RefundCredit({
  account,
  action,
}: {
  account: string;
  action: Action;
}) {
  const [credit, setCredit] = useState<{
      available_wei: string;
      claim?: { status: string; attempt: number };
    } | null>(null),
    [failed, setFailed] = useState(""),
    [message, setMessage] = useState("");
  return (
    <details className="refund-credit">
      <summary>
        Refund credits & failed-deposit recovery <ChevronDown size={16} />
      </summary>
      <p className="muted">
        Wrong or stale deposits become pullable credit. Runtime failures need a
        finalized failed deposit receipt proving actual native credit.
      </p>
      <button
        className="secondary"
        disabled={!account}
        onClick={async () => {
          try {
            const r = await fetch("/api/credit/" + account);
            const data = await r.json();
            if (!r.ok) throw Error(data.error);
            setCredit(data);
            setMessage("");
          } catch (e) {
            setMessage(e instanceof Error ? e.message : "Credit read failed");
          }
        }}
      >
        Read my refund credit
      </button>
      {credit && (
        <>
          <p>
            {amount(credit.available_wei)} available
            {credit.claim ? " · last transfer " + credit.claim.status : ""}
          </p>
          {BigInt(credit.available_wei) > 0n &&
            credit.claim?.status !== "PENDING" &&
            action("Claim refund credit", "TakeEscrow", "claim_credit", [
              (credit.claim?.attempt ?? 0) + 1,
            ])}
          {credit.claim?.status === "PENDING" && (
            <VerifyClaim
              take="CREDIT"
              account={account}
              attempt={credit.claim.attempt}
              action={action}
            />
          )}
        </>
      )}
      <label className="field">
        Failed deposit transaction hash
        <input
          placeholder="0x…"
          value={failed}
          onChange={(e) => setFailed(e.target.value)}
        />
      </label>
      {action(
        "Recover verified failed deposit",
        "TakeEscrow",
        "recover_failed_deposit",
        [failed],
        !/^0x[\da-f]{64}$/i.test(failed),
      )}
      {message && (
        <p role="alert" className="red">
          {message}
        </p>
      )}
    </details>
  );
}

function TransactionImport({ track }: { track: (hash: string) => void }) {
  const [hash, setHash] = useState("");
  return (
    <form
      className="transaction-import"
      onSubmit={(e) => {
        e.preventDefault();
        if (/^0x[\da-f]{64}$/i.test(hash)) {
          track(hash);
          setHash("");
        }
      }}
    >
      <label className="field">
        Track a transaction
        <input
          value={hash}
          onChange={(e) => setHash(e.target.value.trim())}
          placeholder="0x… transaction hash"
        />
      </label>
      <button className="secondary" disabled={!/^0x[\da-f]{64}$/i.test(hash)}>
        Track receipt <ArrowRight size={16} />
      </button>
    </form>
  );
}
