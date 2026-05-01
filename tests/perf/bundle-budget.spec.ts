/**
 * Bundle-budget gate. Per Gemini's "no heavy 3rd-party charting libs" rule
 * and ChatGPT's "restraint > feature expansion" rule, we cap the gz total
 * for the production bundle at the values below.
 *
 * The hard cap (`HARD_LIMIT_KB`) fails the build. The soft cap
 * (`SOFT_LIMIT_KB`) emits a console warning so the next reviewer notices
 * before the hard line is hit.
 *
 * Exception: the existing `yiJingLines` chunk (lazy-loaded; ~200 KB gz)
 * and `localizedTerms` chunk (~90 KB gz) are tracked separately and
 * not counted against the main-bundle budget — they're only fetched
 * on the Hexagrams view.
 */
import { describe, it, expect } from "vitest";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { gzipSync } from "node:zlib";

const DIST = resolve(__dirname, "../../dist");
const ASSETS = resolve(DIST, "assets");

// In gzipped kilobytes.
const SOFT_LIMIT_KB = 1100;
const HARD_LIMIT_KB = 1400;

// Patterns that count toward the *eager* bundle (loaded on first paint).
const EAGER_MATCHERS = [/^index-/];

// Patterns we know are lazy-loaded route chunks; not counted as eager.
const LAZY_MATCHERS = [
  /HexagramCenterView/,
  /AlchemyView/,
  /WorkbenchView/,
  /IntelligenceView/,
  /AIChatView/,
  /HomeView/,
  /CommunityView/,
  /yiJingLines/,
  /localizedTerms/,
  /numerals_localized/,
];

describe.skipIf(!existsSync(ASSETS))("Bundle budget", () => {
  it("eager bundle (gz) stays under the soft limit; never exceeds the hard limit", () => {
    const files = readdirSync(ASSETS);
    let eagerGzKb = 0;
    let totalGzKb = 0;
    const breakdown: { file: string; rawKb: number; gzKb: number; lane: string }[] = [];

    for (const f of files) {
      if (!f.endsWith(".js")) continue;
      const full = resolve(ASSETS, f);
      const raw = readFileSync(full);
      const rawKb = raw.length / 1024;
      const gzKb = gzipSync(raw).length / 1024;
      const isEager = EAGER_MATCHERS.some((rx) => rx.test(f));
      const isLazy = LAZY_MATCHERS.some((rx) => rx.test(f));
      const lane = isEager ? "eager" : isLazy ? "lazy" : "unclassified";
      if (lane === "eager") eagerGzKb += gzKb;
      totalGzKb += gzKb;
      breakdown.push({ file: f, rawKb, gzKb, lane });
    }

    if (process.env.PRINT_BUNDLE === "1") {
      console.log("Bundle breakdown (gz):");
      for (const b of breakdown.sort((a, b) => b.gzKb - a.gzKb)) {
        console.log(
          `  [${b.lane.padEnd(13)}] ${b.gzKb.toFixed(1).padStart(8)} KB  ${b.file}`
        );
      }
      console.log(`  total eager gz = ${eagerGzKb.toFixed(1)} KB`);
      console.log(`  total all   gz = ${totalGzKb.toFixed(1)} KB`);
    }

    expect(eagerGzKb).toBeLessThan(HARD_LIMIT_KB);
    if (eagerGzKb >= SOFT_LIMIT_KB) {
      console.warn(
        `[bundle-budget] eager bundle ${eagerGzKb.toFixed(1)} KB exceeds soft limit ${SOFT_LIMIT_KB} KB`
      );
    }
  });

  it("dist/ exists with assets/ subdirectory", () => {
    expect(existsSync(DIST)).toBe(true);
    expect(existsSync(ASSETS)).toBe(true);
    const stat = statSync(ASSETS);
    expect(stat.isDirectory()).toBe(true);
  });
});

// Tag for a CI step that runs `vite build` first then this spec.
export const __noop = true;
