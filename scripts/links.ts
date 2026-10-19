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
  transactions: Object.fromEntries(
    Object.entries(proof.transactions as Record<string, string>).map(
      ([name, h]) => [name, explorer("tx", h)],
    ),
  ),
};
writeFileSync("deploy/links.json", JSON.stringify(links, null, 2) + "\n");
console.log("Generated canonical URLs using lib/explorer.ts");
