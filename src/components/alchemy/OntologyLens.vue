<script setup lang="ts">
/**
 * OntologyLens — toggle between TCM and Ayurveda vocabulary.
 *
 * The toggle does not change the underlying graph data; it only swaps the
 * labels rendered on top. Mappings are seeded in `src/data/ontologyMap.json`.
 *
 * Output Contract: copy is descriptive only.
 */

import { computed } from "vue";
import ontologyMap from "@/data/ontologyMap.json";

export type OntologySystem = "TCM" | "Ayurveda";

const props = defineProps<{ system: OntologySystem }>();
const emit = defineEmits<{
  (e: "update:system", v: OntologySystem): void;
}>();

const systems: OntologySystem[] = ["TCM", "Ayurveda"];

const mappingPreview = computed<Array<{ from: string; to: string }>>(() => {
  const m =
    props.system === "TCM"
      ? ontologyMap.tcm_to_ayurveda
      : ontologyMap.ayurveda_to_tcm;
  return Object.entries(m)
    .slice(0, 8)
    .map(([k, v]) => ({ from: k, to: String(v) }));
});
</script>

<template>
  <div class="rounded-xl border border-white/10 p-4">
    <header class="mb-3 flex items-baseline justify-between gap-3">
      <div>
        <h3 class="text-xs font-medium uppercase tracking-wider text-slate-400">
          Ontology
        </h3>
        <p class="mt-1 text-xs text-slate-500">
          Vocabulary lens — graph data is unchanged.
        </p>
      </div>
      <div class="flex rounded-md border border-white/10 bg-black/20 p-0.5">
        <button
          v-for="sys in systems"
          :key="sys"
          type="button"
          class="px-3 py-1 text-xs transition-colors"
          :class="
            props.system === sys
              ? 'rounded bg-white/10 text-slate-100'
              : 'text-slate-400 hover:text-slate-200'
          "
          @click="emit('update:system', sys)"
        >
          {{ sys }}
        </button>
      </div>
    </header>

    <ul class="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-400">
      <li v-for="m in mappingPreview" :key="m.from" class="truncate">
        <span class="text-slate-300">{{ m.from }}</span>
        <span class="mx-1 text-slate-600">→</span>
        <span>{{ m.to }}</span>
      </li>
    </ul>
  </div>
</template>
