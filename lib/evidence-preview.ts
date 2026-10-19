/** Non-authoritative browser preview. Contract submission repeats all checks on validators. */
import { type Rule, evidenceShape } from "./domain";
async function bounded(url: string) {
  const r = await fetch(url, {
    headers: { "User-Agent": "Mozilla/5.0 CalledIt/1.0" },
    signal: AbortSignal.timeout(25000),
    cache: "no-store",
  });
  if (!r.ok)
    throw Error(
      "Evidence source returned HTTP " +
        r.status +
        ". Try a different permanent source.",
    );
  const reader = r.body?.getReader();
  if (!reader) throw Error("Empty source response");
  const chunks: Uint8Array[] = [];
  let size = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    size += value.length;
    if (size > 2000000) {
      await reader.cancel();
      throw Error("Evidence exceeds the 2 MB contract limit.");
    }
    chunks.push(value);
  }
  const all = new Uint8Array(size);
  let at = 0;
  for (const chunk of chunks) {
    all.set(chunk, at);
    at += chunk.length;
  }
  return new TextDecoder().decode(all);
}
function text(raw: string) {
  let main = raw.replace(
    /<(script|style|nav|footer|header)\b[^>]*>[\s\S]*?<\/\1>/gi,
    " ",
  );
  const article = main.match(
    /<(?:main|article)\b[^>]*>([\s\S]*?)<\/(?:main|article)>/i,
  );
  if (article) main = article[1];
  return main
    .replace(/<[^>]+>/g, " ")
    .replace(
      /&(?:amp|lt|gt|quot|#39|nbsp);/g,
      (v) =>
        ({
          "&amp;": "&",
          "&lt;": "<",
          "&gt;": ">",
          "&quot;": '"',
          "&#39;": "'",
          "&nbsp;": " ",
        })[v] ?? v,
    )
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 24000);
}
export async function preview(
  url: string,
  rule: Rule,
  info: Record<string, string>,
) {
  evidenceShape(url, rule);
  let capture: number;
  if (info.kind === "archive") {
    const stamp = info.capture;
    const rows = JSON.parse(
      await bounded(
        "https://web.archive.org/cdx/search/cdx?url=" +
          encodeURIComponent(info.original) +
          "&output=json&fl=timestamp,original&filter=statuscode:200&from=" +
          stamp +
          "&to=" +
          stamp,
      ),
    );
    if (
      !Array.isArray(rows) ||
      !rows
        .slice(1)
        .some(
          (r: unknown) =>
            Array.isArray(r) && r[0] === stamp && r[1] === info.original,
        )
    )
      throw Error("Exact capture is absent from CDX.");
    capture =
      Date.parse(
        `${stamp.slice(0, 4)}-${stamp.slice(4, 6)}-${stamp.slice(6, 8)}T${stamp.slice(8, 10)}:${stamp.slice(10, 12)}:${stamp.slice(12, 14)}Z`,
      ) / 1000;
  } else {
    const data = JSON.parse(
      await bounded(
        "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&revids=" +
          info.revision +
          "&rvprop=ids%7Ctimestamp",
      ),
    );
    const pages = Object.values(data.query?.pages ?? {}) as {
      revisions?: { revid: number; timestamp: string }[];
    }[];
    const revisions = pages.flatMap((p) => p.revisions ?? []);
    if (revisions.length !== 1 || String(revisions[0].revid) !== info.revision)
      throw Error("Revision metadata is unavailable.");
    capture = Date.parse(revisions[0].timestamp) / 1000;
  }
  if (
    !Number.isFinite(capture) ||
    capture <= rule.as_of ||
    capture > rule.deadline + 72 * 3600
  )
    throw Error("Capture is outside the frozen evidence window.");
  const main = text(await bounded(url));
  if (main.length < 30) throw Error("No usable main text found.");
  return { capture, text: main.slice(0, 2000), boundedLength: main.length };
}
