/** The same explorer helper used by the app also generates every document/proof URL. */
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";
import { explorer } from "../lib/explorer";
const proof = JSON.parse(readFileSync("deploy/proof.json", "utf8"));
function markdownFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = directory + "/" + entry.name;
    return entry.isDirectory()
      ? markdownFiles(path)
      : entry.name.endsWith(".md") ? [path] : [];
  });
}
const documentedUrls = ["README.md", ...markdownFiles("docs")].flatMap((file) =>
  Array.from(readFileSync(file, "utf8").matchAll(/\[[^\]]*\]\(([^)\s]+)\)/g)).flatMap((match) => {
    const target = match[1];
    if (target.startsWith("#")) return [];
    if (/^https?:\/\//.test(target)) return [target];
    const local = resolve(dirname(file), target.split("#")[0]);
    const path = relative(resolve("."), local).replaceAll("\\", "/");
    if (path.startsWith("../") || !existsSync(local)) throw Error("Broken documentation link: " + file + " -> " + target);
    return proof.github ? [proof.github + "/blob/main/" + path] : [];
  }),
);
const links = {
  documentationExplorer: Array.from(new Set(documentedUrls.filter((url) => url.startsWith("https://explorer-studio.genlayer.com/")))),
  contracts: Object.fromEntries(
    Object.entries(proof.contracts as Record<string, { address: string }>).map(
      ([name, c]) => [name, explorer("address", c.address)],
    ),
  ),
  diagnosticContracts: proof.consensusDiagnostics?.address
    ? { "Unfunded candidate": explorer("address", proof.consensusDiagnostics.address) }
    : {},
  legacyContracts: Object.fromEntries(
    Object.entries(
      (proof.legacyLiveTakes?.[0]?.contracts ?? {}) as Record<
        string,
        { address: string }
      >,
    ).map(([name, c]) => [name, explorer("address", c.address)]),
  ),
  previousUnsettledContracts: Object.fromEntries(
    (proof.previousUnsettledBets ?? []).flatMap(
      (e: { attempt: number; contracts: Record<string, { address: string }> }) =>
        Object.entries(e.contracts).map(([name, c]) => [
          `r${e.attempt}-${name}`,
          explorer("address", c.address),
        ]),
    ),
  ),
  other: Array.from(
    new Set(
      [
        proof.website,
        proof.github,
        ...documentedUrls.filter((url) => !url.startsWith("https://explorer-studio.genlayer.com/")),
        ...(proof.takes ?? []).flatMap(
          (e: { resolution: { evidence?: { url: string }[] } }) =>
            (e.resolution.evidence ?? []).map((v) => v.url),
        ),
        ...(proof.github
          ? [
              "docs/RELEASE.md",
              "docs/VERIFICATION.md",
              "docs/TUTORIAL.md",
              "docs/DEMO.md",
              "docs/FAIRNESS-REVISION.md",
              "docs/MODEL-OUTPUT-REPAIR.md",
              "deploy/proof.json",
              "deploy/releases/v2-proof.json",
              "deploy/releases/v3-proof.json",
            ].map((path) => proof.github + "/blob/main/" + path)
          : []),
      ].filter(Boolean),
    ),
  ),
  transactions: Object.fromEntries(
    Object.entries(proof.transactions as Record<string, string>).map(
      ([name, h]) => [name, explorer("tx", h)],
    ),
  ),
};
writeFileSync("deploy/links.json", JSON.stringify(links, null, 2) + "\n");
console.log("Generated canonical URLs using lib/explorer.ts");
