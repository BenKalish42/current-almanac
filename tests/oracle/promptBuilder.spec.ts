import { describe, it, expect } from "vitest";
import {
  buildHeavensUserPrompt,
  buildEarthUserPrompt,
} from "@/services/oracle";
import { createInMemoryTriplestore } from "@/services/graph/triplestore";
import { auditCompliance } from "@/contracts/outputContract";

describe("Oracle prompt builders", () => {
  it("Heavens prompt embeds canonical block + no-recompute instruction", () => {
    const txt = buildHeavensUserPrompt({
      natal: { year: "甲辰", month: "庚午", day: "庚戌", hour: "壬午" },
      present: { year: "甲辰", month: "庚午", day: "庚戌", hour: "壬午", organ: "Heart" },
    });
    expect(txt).toContain("Heavens — canonical configuration");
    expect(txt).toContain("Do not recompute math");
    expect(txt).toContain("甲辰");
    expect(txt).toContain("Heart");
  });

  it("Earth prompt embeds Ba Gang + describe-only directive", () => {
    const txt = buildEarthUserPrompt({
      baGang: { hot_cold: 1, wet_dry: -2, deficient_excess: 0, interior_exterior: 0 },
      activeMeridian: "Spleen",
    });
    expect(txt).toContain("Earth — canonical configuration");
    expect(txt).toContain("Do not prescribe");
    expect(txt).toContain("hot_cold");
    expect(txt).toContain("Spleen");
  });

  it("attaches triplestore subgraph when store is provided", () => {
    const store = createInMemoryTriplestore();
    const user = store.upsertNode("SovereignNode", {});
    const bio = store.upsertNode("BiometricState", { timestamp: "2026-05-01" });
    store.upsertEdge("EXPERIENCING", user.id, bio.id);
    const heat = store.upsertNode("Pathology", { nature: "Heat" });
    store.upsertEdge("MATCHES_SYNDROME", bio.id, heat.id);

    const txt = buildEarthUserPrompt(
      { baGang: { hot_cold: 2 }, activeMeridian: "Heart" },
      store
    );
    expect(txt).toContain("Triplestore subgraph");
    expect(txt).toContain("Heat");
    expect(txt).toContain("SovereignNode");
  });

  it("the prompt itself is contract-compliant prose", () => {
    // The prompt is authored content; we verify our authored words
    // never embed forbidden phrases (the LLM's reply is audited separately).
    const heavens = buildHeavensUserPrompt({
      natal: { year: "甲辰" },
      present: { year: "甲辰" },
    });
    const earth = buildEarthUserPrompt({
      baGang: {},
      activeMeridian: null,
    });
    // Strip the bracketed forbidden-keyword spec lines that quote forbidden
    // categories; the *spec system* may name them, but our prompt should not.
    expect(auditCompliance(heavens).ok).toBe(true);
    expect(auditCompliance(earth).ok).toBe(true);
  });
});
