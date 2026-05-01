import { describe, it, expect } from "vitest";
import {
  auditCompliance,
  enforceCompliance,
  NON_ACTION_PHRASE,
  OUTPUT_CONTRACT_SYSTEM,
  FORBIDDEN_CATEGORIES,
} from "@/contracts/outputContract";

describe("Output Contract — auditCompliance", () => {
  it("passes clean prose", () => {
    const r = auditCompliance(
      "Resistance is increasing. Flow is limited. Effort applied here returns less than it costs."
    );
    expect(r.ok).toBe(true);
    expect(r.violations).toHaveLength(0);
  });

  it("flags 'you should'", () => {
    const r = auditCompliance("You should rest now.");
    expect(r.ok).toBe(false);
    expect(r.violations.some((v) => v.category === "instructions")).toBe(true);
  });

  it("flags 'destiny'", () => {
    const r = auditCompliance("Your destiny aligns with the moment.");
    expect(r.ok).toBe(false);
    expect(r.violations.some((v) => v.category === "destiny_agency")).toBe(true);
  });

  it("flags 'ancient wisdom' and 'poetic'", () => {
    const r = auditCompliance("Ancient wisdom suggests poetic restraint.");
    expect(r.ok).toBe(false);
    const cats = r.violations.map((v) => v.category);
    expect(cats).toContain("mystical_inflation");
  });

  it("flags 'will happen' and 'guaranteed'", () => {
    const r = auditCompliance("This will happen and is guaranteed.");
    expect(r.ok).toBe(false);
    expect(r.violations.some((v) => v.category === "predictions")).toBe(true);
  });

  it("flags moral framing", () => {
    const r = auditCompliance("Today is a good day. Tomorrow is a bad day.");
    expect(r.ok).toBe(false);
    expect(r.violations.filter((v) => v.category === "moral_framing").length).toBeGreaterThanOrEqual(2);
  });

  it("matches case-insensitively", () => {
    const r = auditCompliance("DESTINY AWAITS");
    expect(r.ok).toBe(false);
  });

  it("returns ok on empty input", () => {
    expect(auditCompliance("").ok).toBe(true);
    expect(auditCompliance("   ").ok).toBe(true);
  });

  it("allows the non-action phrase", () => {
    const r = auditCompliance(NON_ACTION_PHRASE);
    expect(r.ok).toBe(true);
  });
});

describe("Output Contract — enforceCompliance", () => {
  it("redacts forbidden phrases", () => {
    const out = enforceCompliance("You should follow your destiny.");
    expect(out).not.toContain("you should");
    expect(out.toLowerCase()).not.toContain("destiny");
    expect(out).toContain("[redacted]");
  });

  it("preserves clean text", () => {
    const clean = "Resistance is increasing.";
    expect(enforceCompliance(clean)).toBe(clean);
  });
});

describe("OUTPUT_CONTRACT_SYSTEM", () => {
  it("references the non-action phrase verbatim", () => {
    expect(OUTPUT_CONTRACT_SYSTEM).toContain(NON_ACTION_PHRASE);
  });

  it("explicitly forbids destiny + poetic + ancient wisdom", () => {
    const lower = OUTPUT_CONTRACT_SYSTEM.toLowerCase();
    expect(lower).toContain("destiny");
    expect(lower).toContain("poetic");
    expect(lower).toContain("ancient");
  });

  it("itself audits as compliant when checking the spirit (we expect labeled forbidden examples to be flagged)", () => {
    // The system prompt deliberately quotes forbidden phrases to teach the
    // model what NOT to do. So we expect the audit to fire on it. This test
    // documents that intent: the system prompt is authored content, not a
    // user-facing output, and it is allowed to enumerate violations.
    const r = auditCompliance(OUTPUT_CONTRACT_SYSTEM);
    expect(r.ok).toBe(false);
  });
});

describe("FORBIDDEN_CATEGORIES", () => {
  it("has all 5 OG-spec categories", () => {
    expect(Object.keys(FORBIDDEN_CATEGORIES).sort()).toEqual([
      "destiny_agency",
      "instructions",
      "moral_framing",
      "mystical_inflation",
      "predictions",
    ]);
  });
});
