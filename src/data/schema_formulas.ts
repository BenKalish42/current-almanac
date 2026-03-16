/**
 * Formula graph schema for Phase 1.5 Task 11.0.
 * Models classical formula blueprints, ingredient edges, and market variants.
 */

export type FormulaRole = "Jun" | "Chen" | "Zuo" | "Shi";

export interface FormulaLinguistics {
  cantonese: string;
  taiwanese: string;
}

export interface ClassicalFormula {
  id: string;
  name_hanzi: string;
  name_pinyin: string;
  linguistics: FormulaLinguistics;
  source_text: string;
  description: string;
}

export interface FormulaIngredient {
  formula_id: string;
  herb_id: string;
  role: FormulaRole;
  classical_dosage_ratio: number;
}

export interface MarketIngredient {
  herb_id: string;
  exact_dosage_grams: number;
}

export interface MarketVariant {
  id: string;
  brand_name: string;
  formula_id: string;
  actual_ingredients: MarketIngredient[];
  has_shadow_nodes: boolean;
}

export interface FormulaGraphPayload {
  classical_formulas: ClassicalFormula[];
  formula_ingredients: FormulaIngredient[];
  market_variants: MarketVariant[];
}
