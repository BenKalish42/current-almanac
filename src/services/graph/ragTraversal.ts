/**
 * RAG traversal — assemble compact subgraphs for Oracle prompts.
 *
 * Per Chen's blueprint (Master Architectural Blueprint § "RAG Synthesis Pipeline"):
 *
 * "Synthesize the Earth" — 7-step traversal:
 *   1. Latest BiometricState for current SovereignNode.
 *   2. MATCHES_SYNDROME → Pathology.
 *   3. reverse TREATS → Botanical / Formula.
 *   4. Current TemporalPillar.
 *   5. MANIFESTS_AS → OntologyVector.
 *   6. Stringify subgraph as JSON.
 *   7. (caller) inject into Oracle prompt with strict no-recompute rule.
 *
 * "Synthesize the Heavens" — 5-step traversal:
 *   1. Sovereign's natal pillars (BORN_DURING).
 *   2. Current TemporalPillars (year/month/day/hour).
 *   3. SpatialPalace map (FLIES_STAR_TO).
 *   4. Vedic Lagna + Nakshatra (CelestialBody → Zodiac_Sidereal,
 *      CelestialBody → LunarMansion).
 *   5. Active meridian (Physiology) at current hour.
 *
 * The traversal NEVER recomputes math — it only reads what callers
 * have already populated.
 */

import type { GraphEdge, GraphNode } from "./types";
import type { Triplestore } from "./triplestore";

export type EarthSubgraph = {
  user: GraphNode | null;
  biometric: GraphNode | null;
  pathologies: GraphNode[];
  botanicals: GraphNode[];
  formulas: GraphNode[];
  active_pillar: GraphNode | null;
  ontology_vector: GraphNode | null;
};

export type HeavensSubgraph = {
  user: GraphNode | null;
  natal_pillars: GraphNode[];
  current_pillars: GraphNode[];
  spatial_palaces: GraphNode[];
  celestial_bodies: GraphNode[];
  sidereal_signs: GraphNode[];
  lunar_mansions: GraphNode[];
  active_meridian: GraphNode | null;
};

// -----------------------------------------------------------------------------
// Earth traversal
// -----------------------------------------------------------------------------

export function traverseEarth(
  store: Triplestore,
  options: { userId?: string } = {}
): EarthSubgraph {
  const user = options.userId
    ? store.getNode(options.userId) ?? null
    : firstSovereign(store);

  const biometric = user ? latestBiometric(store, user.id) : null;

  const pathologies = biometric
    ? store.follow(biometric.id, "MATCHES_SYNDROME")
    : [];

  // Reverse TREATS — find Botanicals / Formulas pointing AT each pathology.
  const treaters: GraphNode[] = [];
  for (const p of pathologies) {
    treaters.push(...store.inverseFollow(p.id, "TREATS"));
  }
  const botanicals = treaters.filter((n) => n.label === "Botanical");
  const formulas = treaters.filter((n) => n.label === "Formula");

  const active_pillar = currentTemporalPillar(store);
  const ontology_vector = active_pillar
    ? (store.follow(active_pillar.id, "MANIFESTS_AS")[0] ?? null)
    : null;

  return {
    user,
    biometric,
    pathologies: dedupeById(pathologies),
    botanicals: dedupeById(botanicals),
    formulas: dedupeById(formulas),
    active_pillar,
    ontology_vector,
  };
}

// -----------------------------------------------------------------------------
// Heavens traversal
// -----------------------------------------------------------------------------

export function traverseHeavens(
  store: Triplestore,
  options: { userId?: string } = {}
): HeavensSubgraph {
  const user = options.userId
    ? store.getNode(options.userId) ?? null
    : firstSovereign(store);

  const natal_pillars = user ? store.follow(user.id, "BORN_DURING") : [];
  const all_pillars = store.nodesWithLabel("TemporalPillar");
  const current_pillars = all_pillars.filter(
    (p) => !natal_pillars.find((np) => np.id === p.id)
  );

  // Spatial palaces flown into by any current pillar.
  const spatial_palaces: GraphNode[] = [];
  for (const p of current_pillars) {
    spatial_palaces.push(...store.follow(p.id, "FLIES_STAR_TO"));
  }

  const celestial_bodies = store.nodesWithLabel("CelestialBody");
  const sidereal_signs: GraphNode[] = [];
  const lunar_mansions: GraphNode[] = [];
  for (const cb of celestial_bodies) {
    sidereal_signs.push(...store.follow(cb.id, "OCCUPIES_SIDEREAL"));
    lunar_mansions.push(...store.follow(cb.id, "RESIDES_IN_MANSION"));
  }

  const active_meridian = activeMeridian(store);

  return {
    user,
    natal_pillars: dedupeById(natal_pillars),
    current_pillars: dedupeById(current_pillars),
    spatial_palaces: dedupeById(spatial_palaces),
    celestial_bodies: dedupeById(celestial_bodies),
    sidereal_signs: dedupeById(sidereal_signs),
    lunar_mansions: dedupeById(lunar_mansions),
    active_meridian,
  };
}

// -----------------------------------------------------------------------------
// Serialization for the Oracle prompt
// -----------------------------------------------------------------------------

/** Compact node form for the LLM context block. */
export function compactNode(n: GraphNode): Record<string, unknown> {
  return { id: n.id, label: n.label, ...n.properties };
}

export function serializeEarth(s: EarthSubgraph): string {
  return JSON.stringify(
    {
      user: s.user ? compactNode(s.user) : null,
      biometric: s.biometric ? compactNode(s.biometric) : null,
      pathologies: s.pathologies.map(compactNode),
      botanicals: s.botanicals.map(compactNode),
      formulas: s.formulas.map(compactNode),
      active_pillar: s.active_pillar ? compactNode(s.active_pillar) : null,
      ontology_vector: s.ontology_vector ? compactNode(s.ontology_vector) : null,
    },
    null,
    2
  );
}

export function serializeHeavens(s: HeavensSubgraph): string {
  return JSON.stringify(
    {
      user: s.user ? compactNode(s.user) : null,
      natal_pillars: s.natal_pillars.map(compactNode),
      current_pillars: s.current_pillars.map(compactNode),
      spatial_palaces: s.spatial_palaces.map(compactNode),
      celestial_bodies: s.celestial_bodies.map(compactNode),
      sidereal_signs: s.sidereal_signs.map(compactNode),
      lunar_mansions: s.lunar_mansions.map(compactNode),
      active_meridian: s.active_meridian ? compactNode(s.active_meridian) : null,
    },
    null,
    2
  );
}

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function firstSovereign(store: Triplestore): GraphNode | null {
  const all = store.nodesWithLabel("SovereignNode");
  return all[0] ?? null;
}

function latestBiometric(store: Triplestore, userId: string): GraphNode | null {
  const edges = store.outgoing(userId, "EXPERIENCING");
  if (edges.length === 0) return null;
  // Sort biometric states by timestamp descending.
  const targets = edges
    .map((e: GraphEdge) => store.getNode(e.targetId))
    .filter((n): n is GraphNode => Boolean(n))
    .filter((n) => n.label === "BiometricState");
  targets.sort((a, b) => {
    const ta = String(a.properties.timestamp ?? "");
    const tb = String(b.properties.timestamp ?? "");
    return tb.localeCompare(ta);
  });
  return targets[0] ?? null;
}

function currentTemporalPillar(store: Triplestore): GraphNode | null {
  // Return the Hour pillar if available, else Day.
  const pillars = store.nodesWithLabel("TemporalPillar");
  const hour = pillars.find((p) => p.properties.type === "Hour");
  if (hour) return hour;
  return pillars.find((p) => p.properties.type === "Day") ?? null;
}

function activeMeridian(store: Triplestore): GraphNode | null {
  return (
    store
      .nodesWithLabel("Physiology")
      .find((p) => p.properties.type === "Meridian" && p.properties.active === true) ?? null
  );
}

function dedupeById<T extends { id: string }>(items: T[]): T[] {
  const seen = new Set<string>();
  const out: T[] = [];
  for (const it of items) {
    if (seen.has(it.id)) continue;
    seen.add(it.id);
    out.push(it);
  }
  return out;
}
