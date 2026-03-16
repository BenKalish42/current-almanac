<script setup lang="ts">
import { computed, ref } from "vue";
import { useAlchemyStore } from "@/stores/alchemyStore";
import { useFormulaStore } from "@/stores/formulaStore";
import type { FormulaIngredient, MarketIngredient, MarketVariant } from "@/data/schema_formulas";
import type { CauldronIngredientInput } from "@/stores/alchemyStore";

const formulaStore = useFormulaStore();
const alchemyStore = useAlchemyStore();

const searchQuery = ref("");
const pendingLoad = ref<{
  label: string;
  ingredients: CauldronIngredientInput[];
} | null>(null);

const roleOrder: Record<FormulaIngredient["role"], number> = {
  Jun: 0,
  Chen: 1,
  Zuo: 2,
  Shi: 3,
};

const filteredFormulas = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return formulaStore.classicalFormulas;
  return formulaStore.classicalFormulas.filter((formula) => {
    return (
      formula.name_hanzi.toLowerCase().includes(q) ||
      formula.name_pinyin.toLowerCase().includes(q) ||
      formula.source_text.toLowerCase().includes(q) ||
      formula.description.toLowerCase().includes(q)
    );
  });
});

function prettifyHerbId(herbId: string): string {
  return herbId
    .replace(/^herb_/, "")
    .replace(/^shadow_herb_/, "")
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function herbLabel(herbId: string): string {
  if (herbId.toLowerCase().includes("shadow")) return "Proprietary Ingredient";
  const herb = alchemyStore.getHerbById(herbId);
  if (herb) {
    const pinyin = herb.linguistics?.tonal_pinyin ?? herb.pinyin_name;
    return `${pinyin} (${herb.common_name})`;
  }
  return prettifyHerbId(herbId);
}

function ingredientsForFormula(formulaId: string): FormulaIngredient[] {
  return [...formulaStore.getIngredientsForFormula(formulaId)].sort(
    (a, b) => roleOrder[a.role] - roleOrder[b.role]
  );
}

function visibleVariantIngredients(variant: MarketVariant): MarketIngredient[] {
  return variant.actual_ingredients.filter(
    (ingredient) => !ingredient.herb_id.toLowerCase().includes("shadow")
  );
}

function classicalLoadIngredients(formulaId: string): CauldronIngredientInput[] {
  return formulaStore.getIngredientsForFormula(formulaId).map((edge) => ({
    herb_id: edge.herb_id,
    classical_dosage_ratio: edge.classical_dosage_ratio,
  }));
}

function variantLoadIngredients(variant: MarketVariant): CauldronIngredientInput[] {
  return variant.actual_ingredients.map((ingredient) => ({
    herb_id: ingredient.herb_id,
    exact_dosage_grams: ingredient.exact_dosage_grams,
  }));
}

function requestLoad(label: string, ingredients: CauldronIngredientInput[]) {
  if (alchemyStore.activeFormula.length === 0) {
    alchemyStore.loadFormulaIntoCauldron(ingredients, false);
    return;
  }
  pendingLoad.value = { label, ingredients };
}

function confirmLoad(append: boolean) {
  if (!pendingLoad.value) return;
  alchemyStore.loadFormulaIntoCauldron(pendingLoad.value.ingredients, append);
  pendingLoad.value = null;
}
</script>

<template>
  <section class="rounded-xl bg-daoist-surface border border-white/10 p-4 space-y-4">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-xs font-medium text-daoist-muted uppercase tracking-wider">
          Formula Library
        </h2>
        <p class="text-sm text-daoist-subtle mt-1">
          Compare classical blueprints against modern market variants.
        </p>
      </div>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search by Hanzi, Pinyin, source text..."
        class="w-full sm:w-80 rounded-lg border border-white/10 bg-daoist-elevated/60 px-3 py-2 text-sm text-daoist-text placeholder:text-daoist-subtle focus:outline-none focus:ring-2 focus:ring-daoist-jade/40"
      />
    </div>

    <div v-if="filteredFormulas.length" class="space-y-3">
      <details
        v-for="formula in filteredFormulas"
        :key="formula.id"
        class="rounded-lg border border-white/10 bg-daoist-elevated/30 overflow-hidden"
      >
        <summary
          class="list-none cursor-pointer px-4 py-3 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between"
        >
          <div class="min-w-0 sm:flex-1">
            <p class="text-daoist-text font-semibold">
              {{ formula.name_hanzi }}
              <span class="text-daoist-muted font-normal ml-2">{{ formula.name_pinyin }}</span>
            </p>
            <p class="text-xs text-daoist-subtle">
              {{ formula.source_text }}
            </p>
          </div>
          <span class="text-xs text-daoist-muted mt-1 sm:mt-0">
            {{ formula.linguistics.cantonese }} / {{ formula.linguistics.taiwanese }}
          </span>
          <button
            type="button"
            class="mt-2 sm:mt-0 rounded-md border border-daoist-jade/40 bg-daoist-jade/15 text-daoist-jade px-2.5 py-1 text-xs font-medium hover:bg-daoist-jade/20 transition-colors"
            @click.stop="requestLoad(`${formula.name_pinyin} (Classical)`, classicalLoadIngredients(formula.id))"
          >
            Load to Cauldron
          </button>
        </summary>

        <div class="border-t border-white/10 px-4 py-4 space-y-4">
          <p class="text-sm text-daoist-subtle">
            {{ formula.description }}
          </p>

          <div>
            <h3 class="text-xs font-medium text-daoist-muted uppercase tracking-wider mb-2">
              Classical Ingredient Ratios
            </h3>
            <ul class="space-y-2">
              <li
                v-for="edge in ingredientsForFormula(formula.id)"
                :key="`${formula.id}:${edge.herb_id}:${edge.role}`"
                class="rounded-md border border-white/10 bg-daoist-charcoal/30 px-3 py-2 flex items-center justify-between gap-3"
              >
                <div class="min-w-0">
                  <span class="text-sm text-daoist-text">{{ herbLabel(edge.herb_id) }}</span>
                  <span class="text-xs text-daoist-muted ml-2">{{ edge.role }}</span>
                </div>
                <span class="text-xs font-mono tabular-nums text-daoist-jade shrink-0">
                  {{ edge.classical_dosage_ratio }}
                </span>
              </li>
            </ul>
          </div>

          <div>
            <h3 class="text-xs font-medium text-daoist-muted uppercase tracking-wider mb-2">
              Market Variants
            </h3>
            <div class="space-y-2">
              <article
                v-for="variant in formulaStore.getVariantsForFormula(formula.id)"
                :key="variant.id"
                class="rounded-md border border-white/10 bg-daoist-charcoal/30 px-3 py-3"
              >
                <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <h4 class="text-sm font-medium text-daoist-text">{{ variant.brand_name }} Curing Pills</h4>
                  <div class="flex items-center gap-2">
                    <span
                      v-if="variant.has_shadow_nodes"
                      class="inline-flex items-center rounded-full border border-amber-500/50 bg-amber-500/10 px-2 py-0.5 text-[11px] text-amber-300"
                    >
                      Contains Proprietary/Restricted Blend.
                    </span>
                    <button
                      type="button"
                      class="rounded-md border border-daoist-jade/40 bg-daoist-jade/15 text-daoist-jade px-2.5 py-1 text-xs font-medium hover:bg-daoist-jade/20 transition-colors"
                      @click="requestLoad(`${variant.brand_name} ${formula.name_pinyin}`, variantLoadIngredients(variant))"
                    >
                      Load to Cauldron
                    </button>
                  </div>
                </div>
                <ul class="space-y-1">
                  <li
                    v-for="ingredient in visibleVariantIngredients(variant)"
                    :key="`${variant.id}:${ingredient.herb_id}`"
                    class="text-sm text-daoist-muted flex items-center justify-between gap-2"
                  >
                    <span>{{ herbLabel(ingredient.herb_id) }}</span>
                    <span class="font-mono tabular-nums">{{ ingredient.exact_dosage_grams }} g</span>
                  </li>
                </ul>
              </article>
            </div>
          </div>
        </div>
      </details>
    </div>

    <p v-else class="text-sm text-daoist-subtle italic py-6 text-center">
      No formulas match your search.
    </p>

    <div
      v-if="pendingLoad"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 px-4"
      @click.self="pendingLoad = null"
    >
      <div class="w-full max-w-md rounded-xl border border-white/10 bg-daoist-surface p-4 shadow-2xl">
        <h3 class="text-sm font-semibold text-daoist-text">Load to Cauldron</h3>
        <p class="text-sm text-daoist-muted mt-2">
          {{ pendingLoad.label }} is ready. Replace current Cauldron or combine formulas?
        </p>
        <div class="mt-4 flex flex-wrap justify-end gap-2">
          <button
            type="button"
            class="rounded-md border border-white/10 px-3 py-1.5 text-sm text-daoist-muted hover:text-daoist-text"
            @click="pendingLoad = null"
          >
            Cancel
          </button>
          <button
            type="button"
            class="rounded-md border border-white/10 px-3 py-1.5 text-sm text-daoist-muted hover:text-daoist-text"
            @click="confirmLoad(false)"
          >
            Replace Cauldron
          </button>
          <button
            type="button"
            class="rounded-md border border-daoist-jade/40 bg-daoist-jade/15 px-3 py-1.5 text-sm text-daoist-jade hover:bg-daoist-jade/20"
            @click="confirmLoad(true)"
          >
            Combine Formulas
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
