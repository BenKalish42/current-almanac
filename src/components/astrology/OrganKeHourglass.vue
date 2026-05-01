<script setup lang="ts">
/**
 * Upright hourglass: top chamber drains and bottom fills with Ke progress (15 min).
 * Full 360° flip animation when 刻 advances (not on first paint).
 */
import { computed, ref, watch } from "vue";

const props = defineProps<{
  /** 0 = Ke start, 1 = Ke end */
  progress: number;
  /** 1–8 within shichen; drives flip on change */
  keInShichen: number;
}>();

const isFlipping = ref(false);

watch(
  () => props.keInShichen,
  (_ke, prev) => {
    if (prev === undefined) return;
    isFlipping.value = true;
  }
);

function onFlipEnd() {
  isFlipping.value = false;
}

/** Top bulb: apex C(50,78), top edge y=12, corners ~(17,12)–(83,12) */
const TOP_Y0 = 12;
const TOP_Y1 = 78;
const BOTTOM_Y0 = 78;
const BOTTOM_Y1 = 142;
const CX = 50;

function widthAtYTop(y: number): number {
  const t = (y - TOP_Y0) / (TOP_Y1 - TOP_Y0);
  return Math.max(0, 66 * (1 - t));
}

function widthAtYBottom(y: number): number {
  const t = (y - BOTTOM_Y0) / (BOTTOM_Y1 - BOTTOM_Y0);
  return Math.max(0, 66 * t);
}

const topSandPoints = computed(() => {
  const p = Math.max(0, Math.min(1, props.progress));
  const ys = TOP_Y0 + p * (TOP_Y1 - TOP_Y0);
  const w = widthAtYTop(ys);
  const xl = CX - w / 2;
  const xr = CX + w / 2;
  return `${xl},${ys} ${xr},${ys} ${CX},${TOP_Y1}`;
});

const bottomSandPoints = computed(() => {
  const p = Math.max(0, Math.min(1, props.progress));
  const ys = BOTTOM_Y1 - p * (BOTTOM_Y1 - BOTTOM_Y0);
  const w = widthAtYBottom(ys);
  const xl = CX - w / 2;
  const xr = CX + w / 2;
  return `${xl},${ys} ${xr},${ys} ${CX},${BOTTOM_Y1}`;
});

const streamOpacity = computed(() => {
  const p = props.progress;
  if (p <= 0.02 || p >= 0.98) return 0;
  return 0.45;
});
</script>

<template>
  <div
    class="organ-ke-hourglass relative h-[5.5rem] w-16 shrink-0"
    :class="{ 'organ-ke-hourglass--flip': isFlipping }"
    @animationend="onFlipEnd"
  >
    <svg
      class="h-full w-full overflow-visible"
      viewBox="0 0 100 160"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="organHgSandTop" x1="50" y1="12" x2="50" y2="78" gradientUnits="userSpaceOnUse">
          <stop stop-color="#fbbf24" stop-opacity="0.95" />
          <stop offset="1" stop-color="#d97706" stop-opacity="0.9" />
        </linearGradient>
        <linearGradient id="organHgSandBottom" x1="50" y1="78" x2="50" y2="142" gradientUnits="userSpaceOnUse">
          <stop stop-color="#f59e0b" stop-opacity="0.95" />
          <stop offset="1" stop-color="#b45309" stop-opacity="0.92" />
        </linearGradient>
        <linearGradient id="organHgGlass" x1="50" y1="8" x2="50" y2="152" gradientUnits="userSpaceOnUse">
          <stop stop-color="rgba(255,255,255,0.35)" />
          <stop offset="0.5" stop-color="rgba(255,255,255,0.08)" />
          <stop offset="1" stop-color="rgba(255,255,255,0.22)" />
        </linearGradient>
      </defs>

      <!-- Glass outline: top triangle + bottom triangle, waist at (50, 78) -->
      <path
        d="M 17 12 L 83 12 L 50 78 L 83 142 L 17 142 L 50 78 Z"
        stroke="rgba(255,255,255,0.45)"
        stroke-width="2"
        stroke-linejoin="round"
        fill="url(#organHgGlass)"
      />

      <!-- Top chamber sand (drains toward neck) -->
      <polygon
        v-if="progress < 0.999"
        :points="topSandPoints"
        fill="url(#organHgSandTop)"
      />

      <!-- Bottom chamber sand (fills from bottom) -->
      <polygon
        v-if="progress > 0.001"
        :points="bottomSandPoints"
        fill="url(#organHgSandBottom)"
      />

      <!-- Neck stream -->
      <line
        x1="50"
        y1="76"
        x2="50"
        y2="82"
        stroke="url(#organHgSandTop)"
        stroke-width="3"
        stroke-linecap="round"
        :opacity="streamOpacity"
      />
    </svg>
  </div>
</template>

<style scoped>
.organ-ke-hourglass {
  transform-origin: 50% 50%;
}

@media (prefers-reduced-motion: no-preference) {
  .organ-ke-hourglass--flip {
    animation: organKeHourglassFlip 0.85s cubic-bezier(0.42, 0, 0.58, 1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .organ-ke-hourglass--flip {
    animation: organKeHourglassFlipReduced 0.35s ease-out;
  }
}

@keyframes organKeHourglassFlip {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes organKeHourglassFlipReduced {
  from {
    opacity: 0.75;
  }
  to {
    opacity: 1;
  }
}

</style>
