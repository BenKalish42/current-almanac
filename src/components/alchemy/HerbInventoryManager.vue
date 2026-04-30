<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { useAlchemyStore } from "@/stores/alchemyStore";
import type { Herb } from "@/stores/alchemyStore";
import LocalizedScript from "@/components/ui/LocalizedScript.vue";
import PronunciationText from "@/components/ui/PronunciationText.vue";
import { herbScripts, herbRomans } from "@/i18n/localizedTerms";

const alchemyStore = useAlchemyStore();
const searchInput = ref("");
const debouncedQuery = ref("");
const dropdownOpen = ref(false);
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

// Debounce search: 300ms delay before updating query passed to store
watch(searchInput, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    debouncedQuery.value = val;
    debounceTimer = null;
  }, 300);
});

const searchResults = computed(() =>
  alchemyStore.searchHerbs(debouncedQuery.value)
);

const activeFormula = computed(() => alchemyStore.activeFormula);

function openDropdown() {
  dropdownOpen.value = true;
}

function closeDropdown() {
  // Delay so mousedown on a result can fire before blur
  setTimeout(() => {
    dropdownOpen.value = false;
  }, 150);
}

function selectHerb(herb: Herb) {
  alchemyStore.addHerbToFormula(herb);
  searchInput.value = "";
  debouncedQuery.value = "";
  dropdownOpen.value = false;
}

function removeHerb(herbId: string) {
  alchemyStore.removeHerbFromFormula(herbId);
}

const showDropdown = computed(
  () => dropdownOpen.value && searchInput.value.trim().length > 0
);
const canAnalyzeSynergy = computed(() => activeFormula.value.length >= 2);

/** Primary pinyin display: tonal_pinyin if enriched, else raw pinyin_name */
function displayPinyin(herb: Herb): string {
  if (herb.id.toLowerCase().includes("shadow")) return "Proprietary Ingredient";
  return (herb.linguistics?.tonal_pinyin ?? herb.pinyin_name) || "";
}

function displayCommonName(herb: Herb): string {
  if (herb.id.toLowerCase().includes("shadow")) return "Proprietary Ingredient";
  return herb.common_name;
}

/** If search matched an alias, return that alias string for UI indicator */
function getMatchedAlias(herb: Herb, query: string): string | null {
  const q = query.trim().toLowerCase();
  if (!q || !herb.aliases?.length) return null;
  return (
    herb.aliases.find(
      (a) =>
        a &&
        (a.trim().toLowerCase().includes(q) ||
          q.includes(a.trim().toLowerCase()))
    ) ?? null
  );
}

async function analyzeVectors() {
  await alchemyStore.analyzeCombinedVectors();
}
</script>

<template>
  <div class="herb-inventory-manager">
    <!-- Search bar -->
    <div class="relative">
      <div
        class="flex items-center gap-2 rounded-lg bg-daoist-surface border border-white/10 px-3 py-2.5 focus-within:border-daoist-jade/50 transition-colors"
      >
        <svg
          class="w-4 h-4 text-daoist-muted shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          v-model="searchInput"
          type="search"
          placeholder="Search herbs by pinyin or name..."
          class="flex-1 min-w-0 bg-transparent text-daoist-text placeholder-daoist-subtle text-sm outline-none"
          @focus="openDropdown"
          @blur="closeDropdown"
        />
      </div>

      <!-- Results dropdown -->
      <Transition name="dropdown">
        <div
          v-if="showDropdown && searchResults.length > 0"
          class="absolute left-0 right-0 top-full mt-1 z-50 max-h-60 overflow-y-auto rounded-lg border border-white/10 bg-daoist-elevated shadow-xl"
        >
          <button
            v-for="herb in searchResults"
            :key="herb.id"
            type="button"
            class="w-full px-4 py-3 text-left hover:bg-white/5 focus:bg-white/5 focus:outline-none focus:ring-1 focus:ring-inset focus:ring-daoist-jade/50 transition-colors first:rounded-t-lg last:rounded-b-lg"
            @mousedown.prevent="selectHerb(herb)"
          >
            <span class="block font-medium text-daoist-text">
              <PronunciationText :pinyin="displayPinyin(herb)" v-bind="herbRomans(herb)" />
            </span>
            <span class="block text-sm text-daoist-muted mt-0.5">
              {{ herb.common_name }}
              <span v-if="getMatchedAlias(herb, debouncedQuery)" class="text-daoist-subtle ml-2">
                (Alias match: {{ getMatchedAlias(herb, debouncedQuery) }})
              </span>
              <span v-else-if="'hanzi_name' in herb && herb.hanzi_name" class="text-daoist-subtle ml-2">
                · {{ (herb as Herb & { hanzi_name?: string }).hanzi_name }}
              </span>
            </span>
          </button>
        </div>
      </Transition>

      <!-- No results message -->
      <Transition name="dropdown">
        <div
          v-if="showDropdown && debouncedQuery && searchResults.length === 0"
          class="absolute left-0 right-0 top-full mt-1 z-50 px-4 py-3 rounded-lg border border-white/10 bg-daoist-elevated text-daoist-muted text-sm"
        >
          No herbs found for "{{ debouncedQuery }}"
        </div>
      </Transition>
    </div>

    <!-- Active formula list -->
    <div v-if="activeFormula.length > 0" class="mt-4">
      <h3 class="text-xs font-medium text-daoist-muted uppercase tracking-wider mb-2">
        Active formula ({{ activeFormula.length }})
      </h3>
      <ul class="space-y-1.5">
        <li
          v-for="herb in activeFormula"
          :key="herb.id"
          class="flex items-center justify-between gap-2 rounded-lg bg-daoist-surface/60 border border-white/5 px-3 py-2"
        >
          <div class="min-w-0">
            <LocalizedScript
              v-if="Object.keys(herbScripts(herb)).length > 0"
              class="font-medium text-daoist-text text-sm mr-1"
              :hanzi="''"
              :scripts="herbScripts(herb)"
            />
            <span class="font-medium text-daoist-text text-sm">
              <PronunciationText :pinyin="displayPinyin(herb)" v-bind="herbRomans(herb)" />
            </span>
            <span class="text-daoist-muted text-xs ml-2">{{ displayCommonName(herb) }}</span>
            <span class="text-daoist-jade text-xs ml-2 font-mono tabular-nums">
              {{ alchemyStore.getHerbDosage(herb.id).toFixed(2) }} g
            </span>
          </div>
          <button
            type="button"
            class="shrink-0 w-6 h-6 flex items-center justify-center rounded text-daoist-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
            aria-label="Remove herb"
            @click="removeHerb(herb.id)"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </li>
      </ul>

      <div class="mt-4">
        <button
          type="button"
          class="w-full rounded-lg border px-3 py-2 text-sm font-medium transition-colors"
          :class="
            canAnalyzeSynergy && !alchemyStore.isAnalyzingSynergy
              ? 'border-daoist-jade/40 bg-daoist-jade/15 text-daoist-jade hover:bg-daoist-jade/20'
              : 'border-white/10 bg-daoist-elevated/40 text-daoist-subtle cursor-not-allowed'
          "
          :disabled="!canAnalyzeSynergy || alchemyStore.isAnalyzingSynergy"
          @click="analyzeVectors"
        >
          {{
            alchemyStore.isAnalyzingSynergy
              ? "Architecting vectors..."
              : "Analyze Combined Vectors"
          }}
        </button>
        <p v-if="!canAnalyzeSynergy" class="mt-2 text-xs text-daoist-subtle">
          Add at least two herbs to run synergy/collision analysis.
        </p>
      </div>

      <details v-if="alchemyStore.synergyReport" class="mt-4 rounded-lg border border-white/10 bg-daoist-elevated/35">
        <summary class="cursor-pointer select-none px-3 py-2 text-sm font-medium text-daoist-text">
          Synergy & Collision Report
        </summary>
        <div class="border-t border-white/10 px-3 py-3">
          <pre class="whitespace-pre-wrap text-sm text-daoist-muted leading-relaxed">{{ alchemyStore.synergyReport }}</pre>
        </div>
      </details>
    </div>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
