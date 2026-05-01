<script setup lang="ts">
/**
 * Eight Principles (Ba Gang 八綱) symptom matrix.
 *
 * Per Chen's Master Architectural Blueprint — Pillar 2 §1:
 * an interactive bidirectional slider system across the four classical vectors.
 *
 *   Hot ↔ Cold        (寒熱)
 *   Wet ↔ Dry         (濕燥)
 *   Deficient ↔ Excess (虛實)
 *   Interior ↔ Exterior (表裡)
 *
 * The component is presentational. Two-way binds via `v-model:state`.
 * Output Contract: all visible labels are descriptive only.
 */

import { computed } from "vue";

export type BaGang = {
  hot_cold: number;          // -5 (cold) .. +5 (hot)
  wet_dry: number;           // -5 (wet)  .. +5 (dry)
  deficient_excess: number;  // -5 (deficient) .. +5 (excess)
  interior_exterior: number; // -5 (interior) .. +5 (exterior)
};

const props = defineProps<{ state: BaGang }>();
const emit = defineEmits<{
  (e: "update:state", v: BaGang): void;
}>();

const RANGE = 5;

function setAxis<K extends keyof BaGang>(key: K, value: number) {
  emit("update:state", { ...props.state, [key]: clamp(value) });
}

function clamp(n: number) {
  return Math.max(-RANGE, Math.min(RANGE, Math.round(n)));
}

const axes = [
  { key: "hot_cold" as const, leftLabel: "Cold", rightLabel: "Hot" },
  { key: "wet_dry" as const, leftLabel: "Wet", rightLabel: "Dry" },
  { key: "deficient_excess" as const, leftLabel: "Deficient", rightLabel: "Excess" },
  { key: "interior_exterior" as const, leftLabel: "Interior", rightLabel: "Exterior" },
];

const tone = computed(() => {
  // Subtle background-warmth tint based on net hot/cold.
  const hc = props.state.hot_cold;
  const intensity = Math.abs(hc) / RANGE; // 0..1
  if (hc > 0) return `rgba(220, 80, 60, ${0.06 * intensity})`; // warm
  if (hc < 0) return `rgba(80, 140, 220, ${0.06 * intensity})`; // cool
  return "transparent";
});
</script>

<template>
  <div
    class="rounded-xl border border-white/10 p-4 transition-colors"
    :style="{ backgroundColor: tone }"
  >
    <header class="mb-3">
      <h3 class="text-xs font-medium uppercase tracking-wider text-slate-400">
        Eight Principles
      </h3>
      <p class="mt-1 text-xs text-slate-500">
        Configuration along four classical vectors. Descriptive only.
      </p>
    </header>

    <div class="space-y-4">
      <div v-for="ax in axes" :key="ax.key" class="grid grid-cols-[5rem_1fr_5rem] items-center gap-3">
        <span class="text-right text-xs text-slate-400">{{ ax.leftLabel }}</span>
        <div class="flex items-center gap-2">
          <input
            type="range"
            :min="-RANGE"
            :max="RANGE"
            step="1"
            :value="props.state[ax.key]"
            class="w-full"
            :aria-label="`${ax.leftLabel} to ${ax.rightLabel}`"
            @input="(ev) => setAxis(ax.key, Number((ev.target as HTMLInputElement).value))"
          />
          <span class="w-6 text-center text-xs tabular-nums text-slate-300">
            {{ props.state[ax.key] > 0 ? "+" : "" }}{{ props.state[ax.key] }}
          </span>
        </div>
        <span class="text-left text-xs text-slate-400">{{ ax.rightLabel }}</span>
      </div>
    </div>
  </div>
</template>
