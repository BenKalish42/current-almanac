/**
 * Heuristic formula rater: assigns Jing–Qi–Shen cultivation scores
 * based on herb properties, actions, and role-weighted contribution.
 */

/** Minimal Herb shape for rating (matches alchemyStore Herb) */
export interface HerbForRating {
  id: string;
  properties: {
    temperature: string;
    flavor: string[];
    meridians: string[];
  };
  actions: string[];
}

export interface FormulaRating {
  jingScore: number;
  qiScore: number;
  shenScore: number;
  primaryEffect: string;
}

/** Role → point multiplier. Unassigned/Courier/Envoy = default. */
const ROLE_MULTIPLIERS: Record<string, number> = {
  "King (Jun)": 2.0,
  "Minister (Chen)": 1.5,
  "Assistant (Zuo)": 1.0,
  "Envoy (Shi)": 0.5,
};

const DEFAULT_MULTIPLIER = 1.0;

function getRoleMultiplier(herbId: string, herbRoles: Record<string, string>): number {
  const role = herbRoles[herbId];
  if (!role) return DEFAULT_MULTIPLIER;
  const mult = ROLE_MULTIPLIERS[role];
  return typeof mult === "number" ? mult : DEFAULT_MULTIPLIER;
}

function collectText(herb: HerbForRating): string {
  const actions = herb.actions?.join(" ") ?? "";
  const flavor = herb.properties?.flavor?.join(" ") ?? "";
  const meridians = herb.properties?.meridians?.join(" ") ?? "";
  const temperature = herb.properties?.temperature ?? "";
  return `${actions} ${flavor} ${meridians} ${temperature}`.toLowerCase();
}

/**
 * Heuristically score a single herb's contribution to Jing, Qi, Shen.
 */
function scoreHerb(herb: HerbForRating): { jing: number; qi: number; shen: number } {
  let jing = 0;
  let qi = 0;
  let shen = 0;
  const text = collectText(herb);
  const temperature = (herb.properties?.temperature ?? "").toLowerCase();
  const flavor = herb.properties?.flavor ?? [];
  const hasSweet = flavor.some((f) => f.toLowerCase().includes("sweet"));
  const isWarm = temperature.includes("warm") || temperature.includes("hot");

  // Qi: Tonifies Qi, Primal Qi, Qi in actions; Sweet + Warm
  if (/\bqi\b/.test(text) || /tonifies?\s*(primal\s+)?qi/i.test(text)) qi += 3;
  if (/spleen|lung|stomach|wei qi|yuan qi|protective qi/i.test(text)) qi += 2;
  if (hasSweet && isWarm) qi += 1;

  // Shen: Spirit, Shen, Heart, calms
  if (/shen|spirit|heart/i.test(text)) shen += 3;
  if (/calms?\s+(the\s+)?(spirit|shen)|improves\s+mental/i.test(text)) shen += 2;
  if (/\bheart\b/.test(text)) shen += 1;

  // Jing: Essence, Blood, Kidney, Marrow, nourishes
  if (/jing|essence|marrow|kidney\s*yin|boosts?\s+jing/i.test(text)) jing += 3;
  if (/blood|nourishes|tonifies?\s+blood/i.test(text)) jing += 2;
  if (/kidney|liv(er)?\s+and\s+kidney/i.test(text)) jing += 1;

  return { jing, qi, shen };
}

/**
 * Calculate aggregate Jing–Qi–Shen cultivation rating for an active formula.
 */
export function calculateFormulaRating(
  activeFormula: HerbForRating[],
  herbRoles: Record<string, string>
): FormulaRating {
  let jingRaw = 0;
  let qiRaw = 0;
  let shenRaw = 0;

  for (const herb of activeFormula) {
    const { jing, qi, shen } = scoreHerb(herb);
    const mult = getRoleMultiplier(herb.id, herbRoles);
    jingRaw += jing * mult;
    qiRaw += qi * mult;
    shenRaw += shen * mult;
  }

  // Normalize to 0–100: scale so the max score is 100 (or leave as-is if all 0)
  const maxRaw = Math.max(jingRaw, qiRaw, shenRaw, 1);
  const scale = 100 / maxRaw;
  const jingScore = Math.round(Math.min(100, jingRaw * scale));
  const qiScore = Math.round(Math.min(100, qiRaw * scale));
  const shenScore = Math.round(Math.min(100, shenRaw * scale));

  // primaryEffect based on highest score
  const scores = [
    { key: "jingScore" as const, val: jingScore, label: "Primary Jing Tonic" },
    { key: "qiScore" as const, val: qiScore, label: "Primary Qi Tonic" },
    { key: "shenScore" as const, val: shenScore, label: "Primary Shen Tonic" },
  ];
  scores.sort((a, b) => b.val - a.val);

  const first = scores[0]!;
  const second = scores[1]!;
  const third = scores[2]!;

  let primaryEffect: string;
  if (first.val === 0 && second.val === 0 && third.val === 0) {
    primaryEffect = "No Clear Signature";
  } else if (first.val === second.val && second.val >= third.val) {
    primaryEffect = "Balanced Cultivation";
  } else {
    primaryEffect = first.label;
  }

  return {
    jingScore,
    qiScore,
    shenScore,
    primaryEffect,
  };
}
