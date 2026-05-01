/**
 * Sync test — the TypeScript inline pattern table in
 * `src/contracts/outputContract.ts` MUST match the canonical JSON at
 * `data/contracts/forbidden.json` (which the Python mirror loads).
 *
 * If this test fails, edit BOTH files until they agree.
 */

import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { FORBIDDEN_CATEGORIES, NON_ACTION_PHRASE } from "@/contracts/outputContract";

const json = JSON.parse(
  readFileSync(resolve(__dirname, "../../data/contracts/forbidden.json"), "utf-8")
) as {
  schema_version: string;
  description: string;
  categories: Record<string, { rationale: string; patterns: string[] }>;
  allowed_vocabulary: string[];
  non_action_phrase: string;
};

describe("Output Contract — TS / JSON sync", () => {
  it("non-action phrase matches", () => {
    expect(json.non_action_phrase).toBe(NON_ACTION_PHRASE);
  });

  it("category names match", () => {
    expect(Object.keys(json.categories).sort()).toEqual(
      Object.keys(FORBIDDEN_CATEGORIES).sort()
    );
  });

  it("each category's patterns match exactly", () => {
    for (const cat of Object.keys(json.categories)) {
      expect(FORBIDDEN_CATEGORIES[cat], `category missing in TS: ${cat}`).toBeTruthy();
      expect(FORBIDDEN_CATEGORIES[cat].patterns).toEqual(json.categories[cat].patterns);
    }
  });
});
