/**
 * Alchemy store - Formula builder state management.
 * Centralizes herbs, formulas, and the active custom formula.
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import seedHerbs from "@/data/seed_herbs.json";
import seedFormulas from "@/data/seed_formulas.json";
import { checkNPDI, type NPDIWarning } from "@/data/npdi";
import { calculateFormulaRating } from "@/utils/heuristicRater";
import { analyzeCauldronSynergy } from "@/services/intelligenceService";

// --- Types (based on seed JSON schemas) ---

export interface HerbProperties {
  temperature: string;
  flavor: string[];
  meridians: string[];
}

export interface HerbTranslationCell {
  script: string;
  roman: string;
}

export interface HerbLinguistics {
  tonal_pinyin?: string;
  jyutping?: string;
  hokkien?: string;
  /** Per-language { script, roman } translations (Task 12.5). */
  translations?: Record<string, HerbTranslationCell>;
}

export interface Herb {
  id: string;
  pinyin_name: string;
  common_name: string;
  english_name?: string;
  safety_tier: number;
  properties: HerbProperties;
  actions: string[];
  contraindications: string;
  /** Dialectal / alternate names for search; e.g. ["Gui Zhi"] for pinyin_name "Guizi" */
  aliases?: string[];
  /** LLM linguistic enrichment (tonal pinyin, jyutping, hokkien) */
  linguistics?: HerbLinguistics;
}

export interface FormulaArchitectureItem {
  role: string;
  herb_id: string;
  pinyin_name: string;
  purpose: string;
  dosage_percentage: number;
}

export interface Formula {
  id: string;
  pinyin_name: string;
  common_name: string;
  primary_pattern: string;
  actions: string[];
  architecture: FormulaArchitectureItem[];
  safety_note: string;
}

export interface CauldronIngredientInput {
  herb_id: string;
  exact_dosage_grams?: number;
  classical_dosage_ratio?: number;
  dosage?: number;
}

export const useAlchemyStore = defineStore("alchemy", () => {
  // --- State ---
  const herbs = ref<Herb[]>(seedHerbs as Herb[]);
  const formulas = ref<Formula[]>(seedFormulas as Formula[]);
  const activeFormula = ref<Herb[]>([]);
  const herbDosages = ref<Record<string, number>>({}); // herbId -> total dosage in g or ratio units
  const herbRoles = ref<Record<string, string>>({}); // herbId -> role (e.g. "King (Jun)")
  const npdiWarnings = ref<NPDIWarning[]>([]);
  const isAnalyzingSynergy = ref(false);
  const synergyReport = ref("");

  // --- Getters ---
  const getHerbById = computed(() => (herbId: string) => {
    return activeFormula.value.find((h) => h.id === herbId) ?? herbs.value.find((h) => h.id === herbId) ?? null;
  });

  const searchHerbs = computed(
    () => (query: string): Herb[] => {
      const q = query.trim().toLowerCase();
      if (!q) return herbs.value;
      return herbs.value.filter((h) => {
        if (h.pinyin_name?.toLowerCase().includes(q)) return true;
        if (h.common_name?.toLowerCase().includes(q)) return true;
        if (h.english_name?.toLowerCase().includes(q)) return true;
        const aliasMatch = h.aliases?.some(
          (a) => a && (a.toLowerCase().includes(q) || q.includes(a.toLowerCase()))
        );
        return aliasMatch === true;
      });
    }
  );

  const formulaCultivationRating = computed(() =>
    calculateFormulaRating(activeFormula.value, herbRoles.value)
  );

  // --- Actions ---
  function runNPDICheck() {
    npdiWarnings.value = checkNPDI(activeFormula.value);
  }

  function dosageFromInput(ingredient: CauldronIngredientInput): number {
    if (typeof ingredient.exact_dosage_grams === "number") return ingredient.exact_dosage_grams;
    if (typeof ingredient.classical_dosage_ratio === "number") return ingredient.classical_dosage_ratio;
    if (typeof ingredient.dosage === "number") return ingredient.dosage;
    return 0;
  }

  function prettifyHerbId(herbId: string): string {
    return herbId
      .replace(/^herb_/, "")
      .replace(/^shadow_herb_/, "")
      .split("_")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function createFallbackHerb(herbId: string): Herb {
    const isShadow = herbId.toLowerCase().includes("shadow");
    const baseName = isShadow ? "Proprietary Ingredient" : prettifyHerbId(herbId);
    return {
      id: herbId,
      pinyin_name: baseName,
      common_name: baseName,
      safety_tier: 1,
      properties: {
        temperature: "Neutral",
        flavor: [],
        meridians: [],
      },
      actions: [],
      contraindications: "",
    };
  }

  function addHerbToFormula(herb: Herb) {
    const exists = activeFormula.value.some((h) => h.id === herb.id);
    if (!exists) {
      activeFormula.value.push(herb);
    }
    const current = herbDosages.value[herb.id] ?? 0;
    herbDosages.value = { ...herbDosages.value, [herb.id]: current + 1 };
    runNPDICheck();
  }

  function removeHerbFromFormula(herbId: string) {
    activeFormula.value = activeFormula.value.filter((h) => h.id !== herbId);
    const next = { ...herbRoles.value };
    delete next[herbId];
    herbRoles.value = next;
    const nextDosages = { ...herbDosages.value };
    delete nextDosages[herbId];
    herbDosages.value = nextDosages;
    runNPDICheck();
  }

  function setHerbRole(herbId: string, role: string | null) {
    const next = { ...herbRoles.value };
    if (role) next[herbId] = role;
    else delete next[herbId];
    herbRoles.value = next;
  }

  function clearFormula() {
    activeFormula.value = [];
    herbDosages.value = {};
    herbRoles.value = {};
    synergyReport.value = "";
    runNPDICheck();
  }

  function loadFormulaIntoCauldron(ingredientsArray: CauldronIngredientInput[], append = false) {
    if (!append) {
      clearFormula();
    }

    const herbsById = new Map(herbs.value.map((h) => [h.id, h]));
    const activeById = new Set(activeFormula.value.map((h) => h.id));
    const nextDosages = { ...herbDosages.value };

    for (const ingredient of ingredientsArray) {
      const herbId = ingredient.herb_id;
      const dosage = dosageFromInput(ingredient);
      const resolvedHerb = herbsById.get(herbId) ?? createFallbackHerb(herbId);

      if (!activeById.has(herbId)) {
        activeFormula.value.push(resolvedHerb);
        activeById.add(herbId);
      }

      const current = nextDosages[herbId] ?? 0;
      nextDosages[herbId] = current + dosage;
    }

    herbDosages.value = nextDosages;
    runNPDICheck();
  }

  const getHerbDosage = computed(() => (herbId: string) => herbDosages.value[herbId] ?? 0);

  async function analyzeCombinedVectors() {
    if (activeFormula.value.length < 2) {
      synergyReport.value = "Add at least two herbs to analyze combined vectors.";
      return;
    }
    isAnalyzingSynergy.value = true;
    try {
      const report = await analyzeCauldronSynergy(activeFormula.value, herbDosages.value);
      synergyReport.value = report;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to analyze synergy.";
      synergyReport.value = `Error: ${msg}`;
      console.error("[analyzeCombinedVectors]", err);
    } finally {
      isAnalyzingSynergy.value = false;
    }
  }

  return {
    herbs,
    formulas,
    activeFormula,
    herbDosages,
    herbRoles,
    npdiWarnings,
    isAnalyzingSynergy,
    synergyReport,
    formulaCultivationRating,
    getHerbById,
    getHerbDosage,
    searchHerbs,
    addHerbToFormula,
    removeHerbFromFormula,
    setHerbRole,
    clearFormula,
    loadFormulaIntoCauldron,
    analyzeCombinedVectors,
  };
});
