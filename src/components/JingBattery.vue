<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "@/stores/appStore";

const store = useAppStore();

/**
 * Jing Score (0-100%): Rough estimate of "Essence" reserves.
 * - Capacity + Sleep Quality: increase Jing (restorative)
 * - Load + Cognitive Noise + Social Load: deplete Jing (drain)
 * Sliders are 0-10; we normalize to a 0-100 score.
 */
const jingScore = computed(() => {
  const cap = normalize(store.userCapacity);
  const load = normalize(store.userLoad);
  const sleep = normalize(store.userSleepQuality);
  const cognitive = normalize(store.userCognitiveNoise);
  const social = normalize(store.userSocialLoad);

  // Restorative: high capacity + sleep = +Jing
  const restorative = (cap + sleep) / 2;
  // Depletive: high load + cognitive + social = -Jing
  const depletive = (load + cognitive + social) / 3;

  // Score: restorative minus depletive, scaled to 0-100
  const raw = Math.max(0, Math.min(100, 50 + (restorative - depletive) * 10));
  return Math.round(raw);
});

function normalize(val: number | null): number {
  return Number.isFinite(val) ? Math.max(0, Math.min(10, val as number)) : 5;
}

const batteryColor = computed(() => {
  if (jingScore.value >= 70) return "bg-emerald-500";
  if (jingScore.value >= 40) return "bg-amber-500";
  return "bg-red-500";
});

const batteryLabel = computed(() => {
  if (jingScore.value >= 70) return "Full";
  if (jingScore.value >= 40) return "Depleted";
  return "Critical";
});
</script>

<template>
  <div class="jing-battery">
    <div class="flex items-center justify-between gap-2 mb-1">
      <span class="text-xs font-medium text-white/80 uppercase tracking-wider">Jing</span>
      <span class="text-xs text-white/60">{{ jingScore }}% · {{ batteryLabel }}</span>
    </div>
    <div class="h-3 w-full rounded-full bg-black/30 overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-500 ease-out"
        :class="batteryColor"
        :style="{ width: `${jingScore}%` }"
      />
    </div>
  </div>
</template>
