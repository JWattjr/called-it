/** The same explorer helper used by the app also generates every document/proof URL. */
import { readFileSync, writeFileSync } from "node:fs";
import { explorer } from "../lib/explorer";
const proof = JSON.parse(readFileSync("deploy/proof.json", "utf8"));
const links = {
  contracts: Object.fromEntries(
    Object.entries(proof.contracts as Record<string, { address: string }>).map(
      ([name, c]) => [name, explorer("address", c.address)],
    ),
  ),
  legacyContracts: Object.fromEntries(
    Object.entries(
      (proof.legacyLiveTakes?.[0]?.contracts ?? {}) as Record<
        string,
        { address: string }
      >,
    ).map(([name, c]) => [name, explorer("address", c.address)]),
  ),
  other: Array.from(
    new Set(
      [
        proof.website,
        proof.github,
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
              "deploy/proof.json",
              "deploy/releases/v2-proof.json",
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
