/**
 * Phase 5: Alchemy API service.
 * Communicates with FastAPI backend for formula recommendations and safety checks.
 */

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "";

export interface FormulaArchitectureEntry {
  role: string;
  herb_id: string;
  pinyin_name: string;
  dosage_percentage: number;
  purpose: string;
}

/** Internal alchemy practice (Nei Dan) from Dual Cultivation. */
export interface NeiDanPractice {
  id: string;
  name: string;
  type: string;
  target_pattern: string[];
  instructions: string[];
  safety_note: string;
}

/** Dual Cultivation: Wei Dan (herbal) + Nei Dan (internal practice). */
export interface Prescription {
  wei_dan: FormulaArchitectureEntry[];
  nei_dan: NeiDanPractice | null;
  /** Backward compat: same as wei_dan */
  architecture: FormulaArchitectureEntry[];
  id: string;
  formula_id: string;
  pinyin_name: string;
  common_name: string;
  primary_pattern: string;
  actions: string[];
  safety_note: string;
}

/** @deprecated Use Prescription for Dual Cultivation. */
export type FormulaResponse = Prescription;

export interface AstroState {
  birthProfile?: unknown;
  temporalHex?: unknown;
  qimenChart?: unknown;
  [key: string]: unknown;
}

export interface UserState {
  capacity_0_10?: number | null;
  load_0_10?: number | null;
  sleep_quality_0_10?: number | null;
  cognitive_noise_0_10?: number | null;
  social_load_0_10?: number | null;
  emotional_tone?: string | null;
  intent?: { domain?: string; goal_constraint?: string };
  [key: string]: unknown;
}

export interface OverrideCheckResponse {
  allowed: boolean;
  message: string;
}

export interface MergeFormulasResponse {
  architecture: FormulaArchitectureEntry[];
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error (${res.status}): ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Fetches the Prescription (Dual Cultivation) based on astro state and user state.
 * Returns wei_dan (herbal formula) and nei_dan (matched internal practice).
 */
export async function fetchFormula(
  astroState: AstroState,
  userState: UserState
): Promise<Prescription> {
  const payload = {
    astro: astroState,
    user: userState,
  };
  return apiFetch<Prescription>("/api/formula", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Checks whether adding a new herb to the current formula is safe.
 * Returns synergy note (green) or blocking warning (red).
 */
export async function checkOverride(
  currentFormulaId: string,
  newHerbId: string
): Promise<OverrideCheckResponse> {
  const payload = {
    formula_id: currentFormulaId,
    herb_id: newHerbId,
  };
  return apiFetch<OverrideCheckResponse>("/api/check-override", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Merges two formulas using the He Fang algorithm.
 */
export async function mergeFormulas(
  formulaAId: string,
  formulaBId: string,
  primaryFormulaId: string
): Promise<MergeFormulasResponse> {
  const payload = {
    formula_a_id: formulaAId,
    formula_b_id: formulaBId,
    primary_formula_id: primaryFormulaId,
  };
  return apiFetch<MergeFormulasResponse>("/api/merge-formulas", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
