<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    yinLevel?: number;
    yangLevel?: number;
  }>(),
  { yinLevel: 50, yangLevel: 50 }
);

const yinPct = computed(() =>
  Math.max(0, Math.min(100, Number.isFinite(props.yinLevel) ? props.yinLevel : 50))
);
const yangPct = computed(() =>
  Math.max(0, Math.min(100, Number.isFinite(props.yangLevel) ? props.yangLevel : 50))
);

const yinIsCritical = computed(() => yinPct.value < 20);
const yangIsCritical = computed(() => yangPct.value < 20);

const yinBarStyle = computed(() => ({ width: `${yinPct.value}%` }));
const yangBarStyle = computed(() => ({ width: `${yangPct.value}%` }));
</script>

<template>
  <div class="jing-battery rounded-xl bg-daoist-surface/80 p-4 border border-white/5">
    <div class="flex gap-6">
      <!-- Yin Jing -->
      <div class="flex-1 min-w-0">
        <div class="flex items-baseline justify-between mb-1.5">
          <span class="text-xs font-medium text-daoist-muted tracking-wider">Yin Jing</span>
          <span class="text-sm font-mono tabular-nums text-slate-300">{{ yinPct }}%</span>
        </div>
        <div
          class="h-2.5 w-full rounded-full bg-daoist-charcoal overflow-hidden border border-slate-700/40"
        >
          <div
            class="h-full rounded-full transition-all duration-500 ease-out"
            :class="[
              yinIsCritical ? 'animate-pulse' : '',
              'bg-gradient-to-r from-teal-800 to-cyan-500',
            ]"
            :style="yinBarStyle"
          />
        </div>
      </div>

      <!-- Yang Jing -->
      <div class="flex-1 min-w-0">
        <div class="flex items-baseline justify-between mb-1.5">
          <span class="text-xs font-medium text-daoist-muted tracking-wider">Yang Jing</span>
          <span class="text-sm font-mono tabular-nums text-amber-200/90">{{ yangPct }}%</span>
        </div>
        <div
          class="h-2.5 w-full rounded-full bg-daoist-charcoal overflow-hidden border border-amber-900/30"
        >
          <div
            class="h-full rounded-full transition-all duration-500 ease-out"
            :class="[
              yangIsCritical ? 'animate-pulse' : '',
              'bg-gradient-to-r from-amber-900 to-amber-500',
            ]"
            :style="yangBarStyle"
          />
        </div>
      </div>
    </div>
  </div>
</template>
