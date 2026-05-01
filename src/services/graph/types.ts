/**
 * Master Knowledge Graph — node + edge type definitions.
 *
 * Per Chen's blueprint (Master Architectural Blueprint & Schema):
 * a triplestore projection of the Neo4j philosophy onto local storage.
 *
 * The store holds two flat tables (`nodes`, `edges`); domain types here
 * are an authoring-time view onto those tables.
 */

// -----------------------------------------------------------------------------
// Node labels
// -----------------------------------------------------------------------------

export const NODE_LABELS = [
  "CelestialBody",
  "Zodiac_Tropical",
  "Zodiac_Sidereal",
  "LunarMansion",
  "TemporalPillar",
  "SpatialPalace",
  "OntologyVector",
  "Physiology",
  "Pathology",
  "Botanical",
  "Formula",
  "SovereignNode",
  "BiometricState",
] as const;
export type NodeLabel = (typeof NODE_LABELS)[number];

// -----------------------------------------------------------------------------
// Edge types
// -----------------------------------------------------------------------------

export const EDGE_TYPES = [
  "OCCUPIES_TROPICAL",
  "OCCUPIES_SIDEREAL",
  "RESIDES_IN_MANSION",
  "MANIFESTS_AS",
  "FLIES_STAR_TO",
  "TRANSLATES_VECTOR",
  "ALCHEMICAL_EQUIVALENT",
  "AFFECTS",
  "TREATS",
  "CONTAINS_HERB",
  "BORN_DURING",
  "EXPERIENCING",
  "MATCHES_SYNDROME",
  "ESTABLISHED_E2EE",
] as const;
export type EdgeType = (typeof EDGE_TYPES)[number];

// -----------------------------------------------------------------------------
// Generic record shapes
// -----------------------------------------------------------------------------

export type NodeProperties = Record<string, unknown>;
export type EdgeProperties = Record<string, unknown>;

export type GraphNode = {
  id: string;
  label: NodeLabel;
  properties: NodeProperties;
};

export type GraphEdge = {
  id: string;
  type: EdgeType;
  sourceId: string;
  targetId: string;
  properties: EdgeProperties;
};

// -----------------------------------------------------------------------------
// Domain-typed property shapes (author-time hints; persisted as `properties`)
// -----------------------------------------------------------------------------

export type CelestialBodyProps = {
  name: string;
  tropical_longitude?: number;
  declination?: number;
};

export type ZodiacTropicalProps = {
  name: string;
  element?: "Fire" | "Earth" | "Air" | "Water";
  modality?: "Cardinal" | "Fixed" | "Mutable";
};

export type ZodiacSiderealProps = {
  name: string;
  ruling_planet?: string;
};

export type LunarMansionProps = {
  name: string;
  ruling_deity?: string;
  element?: string;
};

export type TemporalPillarProps = {
  type: "Year" | "Month" | "Day" | "Hour";
  ganzhi?: string;
  start_time?: string;
  end_time?: string;
};

export type SpatialPalaceProps = {
  number: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
  direction: "N" | "NE" | "E" | "SE" | "S" | "SW" | "W" | "NW" | "Center";
};

export type OntologyVectorProps = {
  system: "TCM" | "Ayurveda";
  name: string;
  vector?: string;
};

export type PhysiologyProps = {
  system: "TCM" | "Ayurveda";
  type: "Zang_Organ" | "Fu_Organ" | "Meridian" | "Nadi" | "Dhatu";
  name: string;
};

export type PathologyProps = {
  nature: "Heat" | "Damp" | "Wind" | "Dryness" | "Cold" | "Phlegm" | "Stasis";
  description?: string;
};

export type BotanicalProps = {
  latin_name?: string;
  tcm_name: string;
  pinyin_name?: string;
  thermal_nature?: string;
  flavor?: string[];
  meridians?: string[];
  safety_tier?: number;
};

export type FormulaProps = {
  name: string;
  pinyin?: string;
  action?: string;
  primary_pattern?: string;
};

export type SovereignNodeProps = {
  matrix_pub_key?: string;
  latitude?: number;
  longitude?: number;
  birth_timestamp?: string;
};

export type BiometricStateProps = {
  timestamp: string;
  symptom_array?: Record<string, number>;
  ba_gang?: {
    hot_cold?: number;
    wet_dry?: number;
    deficient_excess?: number;
    interior_exterior?: number;
  };
};
