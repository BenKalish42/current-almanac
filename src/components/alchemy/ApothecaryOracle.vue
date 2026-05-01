<script setup lang="ts">
/**
 * ApothecaryOracle — "Synthesize the Earth" action.
 *
 * Per Chen's blueprint Pillar 2 §5: collects Ba Gang state + active meridian,
 * runs RAG traversal, fires through the contract-bound oracle, streams the
 * descriptive reply. No prescriptions; describe properties only.
 */

import { ref } from "vue";
import { synthesizeEarth, type EarthPayload } from "@/services/oracle";
import { getTriplestore } from "@/services/graph/triplestore";
import { hasLlmKey } from "@/services/llmService";

const props = defineProps<{ payload: EarthPayload }>();

const loading = ref(false);
const text = ref<string | null>(null);
const error = ref<string | null>(null);

async function fire() {
  if (!hasLlmKey()) {
    error.value =
      "No LLM key configured. Set VITE_DEEPSEEK_API_KEY in .env and restart the dev server.";
    return;
  }
  loading.value = true;
  error.value = null;
  text.value = null;
  try {
    const out = await synthesizeEarth(props.payload, { store: getTriplestore() });
    text.value = out;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="rounded-xl border border-white/10 p-4">
    <header class="mb-3">
      <h3 class="text-xs font-medium uppercase tracking-wider text-slate-400">
        Apothecary
      </h3>
      <p class="mt-1 text-xs text-slate-500">
        Describes the configuration. Does not prescribe.
      </p>
    </header>

    <button
      type="button"
      class="w-full rounded-lg border border-emerald-500/30 bg-emerald-950/40 px-4 py-3 text-sm font-medium text-emerald-200 transition hover:bg-emerald-900/40 disabled:opacity-50"
      :disabled="loading"
      @click="fire"
    >
      {{ loading ? "Synthesizing…" : "Synthesize the Earth" }}
    </button>

    <div v-if="error" class="mt-3 rounded border border-amber-500/30 bg-amber-950/30 p-3 text-xs text-amber-200">
      {{ error }}
    </div>

    <article
      v-if="text"
      class="mt-3 whitespace-pre-wrap rounded border border-white/10 bg-black/20 p-3 text-sm leading-relaxed text-slate-200"
    >
      {{ text }}
    </article>
  </section>
</template>
