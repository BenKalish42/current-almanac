import { computed, ref } from "vue";
import { defineStore } from "pinia";
import formulasData from "@/data/formulas.json";
import type {
  ClassicalFormula,
  FormulaGraphPayload,
  FormulaIngredient,
  MarketVariant,
} from "@/data/schema_formulas";

export const useFormulaStore = defineStore("formula", () => {
  const graph = ref<FormulaGraphPayload>(formulasData as FormulaGraphPayload);

  const classicalFormulas = computed<ClassicalFormula[]>(() => graph.value.classical_formulas);
  const marketVariants = computed<MarketVariant[]>(() => graph.value.market_variants);
  const formulaIngredients = computed<FormulaIngredient[]>(() => graph.value.formula_ingredients);

  function getVariantsForFormula(formulaId: string): MarketVariant[] {
    return marketVariants.value.filter((variant) => variant.formula_id === formulaId);
  }

  function getIngredientsForFormula(formulaId: string): FormulaIngredient[] {
    return formulaIngredients.value.filter((ingredient) => ingredient.formula_id === formulaId);
  }

  return {
    graph,
    classicalFormulas,
    marketVariants,
    formulaIngredients,
    getVariantsForFormula,
    getIngredientsForFormula,
  };
});
