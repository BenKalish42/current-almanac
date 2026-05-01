import { describe, it, expect } from "vitest";
import { createInMemoryTriplestore } from "@/services/graph/triplestore";
import {
  traverseEarth,
  traverseHeavens,
  serializeEarth,
  serializeHeavens,
} from "@/services/graph/ragTraversal";

function seedEarth() {
  const s = createInMemoryTriplestore();

  const user = s.upsertNode("SovereignNode", {});
  const bio = s.upsertNode("BiometricState", {
    timestamp: "2026-05-01T12:00:00Z",
    ba_gang: { hot_cold: 2, wet_dry: -1, deficient_excess: 1, interior_exterior: 0 },
  });
  s.upsertEdge("EXPERIENCING", user.id, bio.id);

  const heat = s.upsertNode("Pathology", { nature: "Heat", description: "Excess heat" });
  s.upsertEdge("MATCHES_SYNDROME", bio.id, heat.id);

  const huangqin = s.upsertNode("Botanical", { tcm_name: "Huang Qin" });
  s.upsertEdge("TREATS", huangqin.id, heat.id);
  const qingshu = s.upsertNode("Formula", { name: "Qing Shu Yi Qi Tang" });
  s.upsertEdge("TREATS", qingshu.id, heat.id);

  const pillarHour = s.upsertNode("TemporalPillar", { type: "Hour", ganzhi: "甲午" });
  const fire = s.upsertNode("OntologyVector", { system: "TCM", name: "Fire", vector: "Upward" });
  s.upsertEdge("MANIFESTS_AS", pillarHour.id, fire.id);

  return { s, user, bio, heat, huangqin, qingshu, pillarHour, fire };
}

describe("RAG traversal — Earth", () => {
  it("returns the 7-step subgraph", () => {
    const { s, user, bio, heat, huangqin, qingshu, pillarHour, fire } = seedEarth();
    const sub = traverseEarth(s);
    expect(sub.user?.id).toBe(user.id);
    expect(sub.biometric?.id).toBe(bio.id);
    expect(sub.pathologies.map((p) => p.id)).toEqual([heat.id]);
    expect(sub.botanicals.map((b) => b.id)).toEqual([huangqin.id]);
    expect(sub.formulas.map((f) => f.id)).toEqual([qingshu.id]);
    expect(sub.active_pillar?.id).toBe(pillarHour.id);
    expect(sub.ontology_vector?.id).toBe(fire.id);
  });

  it("serializes to JSON containing the user, biometric, and treaters", () => {
    const { s } = seedEarth();
    const json = serializeEarth(traverseEarth(s));
    expect(json).toContain("SovereignNode");
    expect(json).toContain("Heat");
    expect(json).toContain("Huang Qin");
    expect(json).toContain("Qing Shu Yi Qi Tang");
  });
});

describe("RAG traversal — Heavens", () => {
  it("collects natal/current pillars and celestial maps", () => {
    const s = createInMemoryTriplestore();
    const user = s.upsertNode("SovereignNode", {});
    const natal = s.upsertNode("TemporalPillar", { type: "Year", ganzhi: "甲辰" });
    s.upsertEdge("BORN_DURING", user.id, natal.id);
    const current = s.upsertNode("TemporalPillar", { type: "Hour", ganzhi: "壬午" });
    const palace = s.upsertNode("SpatialPalace", { number: 5, direction: "Center" });
    s.upsertEdge("FLIES_STAR_TO", current.id, palace.id);
    const sun = s.upsertNode("CelestialBody", { name: "Sun" });
    const mesha = s.upsertNode("Zodiac_Sidereal", { name: "Mesha" });
    s.upsertEdge("OCCUPIES_SIDEREAL", sun.id, mesha.id, { degree: 23.5 });

    const sub = traverseHeavens(s);
    expect(sub.user?.id).toBe(user.id);
    expect(sub.natal_pillars.map((p) => p.id)).toContain(natal.id);
    expect(sub.current_pillars.map((p) => p.id)).toContain(current.id);
    expect(sub.spatial_palaces.map((p) => p.id)).toContain(palace.id);
    expect(sub.celestial_bodies.map((c) => c.id)).toContain(sun.id);
    expect(sub.sidereal_signs.map((z) => z.id)).toContain(mesha.id);

    const json = serializeHeavens(sub);
    expect(json).toContain("Mesha");
    expect(json).toContain("壬午");
  });
});
