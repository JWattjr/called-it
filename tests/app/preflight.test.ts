import test from "node:test";
import assert from "node:assert/strict";
import { preview } from "../../lib/evidence-preview";
import type { Rule } from "../../lib/domain";

test("article access failure is visible only after immutable metadata verifies", async () => {
  const originalFetch = globalThis.fetch;
  const original = "https://www.apple.com/newsroom/article";
  const url = "https://web.archive.org/web/20230605190503id_/" + original;
  const info = { kind: "archive", original, capture: "20230605190503" };
  const rule = {
    domains: ["apple.com"],
    as_of: Date.parse("2023-06-03T00:00:00Z") / 1000,
    deadline: Date.parse("2023-06-06T23:59:59Z") / 1000,
  } as Rule;
  try {
    for (const status of [401, 403]) {
      globalThis.fetch = async (input) =>
        String(input).includes("/cdx/")
          ? new Response(
              JSON.stringify([
                ["timestamp", "original"],
                [info.capture, original],
              ]),
            )
          : new Response("Blocked", { status });
      const result = await preview(url, rule, info);
      assert.equal(result.status, "UNAVAILABLE");
      assert.equal(result.boundedLength, 0);
      assert.match(result.error, new RegExp("HTTP " + status));
    }
    let articleFetched = false;
    globalThis.fetch = async (input) => {
      if (String(input).includes("/cdx/")) return new Response("[]");
      articleFetched = true;
      return new Response("Blocked", { status: 403 });
    };
    await assert.rejects(preview(url, rule, info), /absent from CDX/);
    assert.equal(articleFetched, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
