<script setup lang="ts">
/**
 * MicrocosmicHourglass — Daoist Microcosmic-Orbit hourglass.
 *
 * Top chamber: Qi rising as warm vapor (Governing Vessel ascent).
 * Neck:        condensation point — vapor cools into "Sweet Dew" droplets.
 * Bottom pool: luminous liquid (Conception Vessel descent into Lower Dantian).
 *
 * Driven entirely by props: `progress` (0→1) shrinks the top chamber and grows
 * the bottom pool; `cycleKey` flips the glass 360° on change. Caller decides
 * what duration / what time domain — this component is geometry + paint.
 */

import { computed, onUnmounted, ref, watch } from "vue";
import { usePrefersReducedMotion } from "@/utils/usePrefersReducedMotion";

type Size = "sm" | "md" | "lg";

const props = withDefaults(
  defineProps<{
    /** Current cycle position (clamped 0..1). */
    progress: number;
    /** Total cycle length in ms. Used to scale droplet cadence. */
    durationMs: number;
    /** Stable identifier for the current cycle; new value triggers a flip. */
    cycleKey?: string | number | null;
    /** Visual size token. */
    size?: Size;
    /** Optional caption rendered beneath the glass. */
    label?: string;
    /** Optional sublabel (e.g. countdown). */
    sublabel?: string;
  }>(),
  {
    cycleKey: null,
    size: "md",
    label: "",
    sublabel: "",
  }
);

const emit = defineEmits<{
  (e: "cycle-end"): void;
}>();

const prefersReducedMotion = usePrefersReducedMotion();

const dims = computed(() => {
  switch (props.size) {
    case "sm":
      return { w: "2.4rem", h: "4.2rem" };
    case "lg":
      return { w: "4.4rem", h: "7.2rem" };
    case "md":
    default:
      return { w: "3.2rem", h: "5.6rem" };
  }
});

const clamped = computed(() => Math.max(0, Math.min(1, props.progress)));

/** Glass geometry — viewBox 100×160; waist at (50, 78). */
const TOP_Y0 = 12;
const TOP_Y1 = 78;
const BOTTOM_Y0 = 78;
const BOTTOM_Y1 = 142;
const CX = 50;
const HALF_WIDTH_AT_TOP = 33; // (83 - 17) / 2

function widthAtTop(y: number) {
  const t = (y - TOP_Y0) / (TOP_Y1 - TOP_Y0);
  return Math.max(0, 2 * HALF_WIDTH_AT_TOP * (1 - t));
}
function widthAtBottom(y: number) {
  const t = (y - BOTTOM_Y0) / (BOTTOM_Y1 - BOTTOM_Y0);
  return Math.max(0, 2 * HALF_WIDTH_AT_TOP * t);
}

/** Top chamber mist mask: triangle from (vapor surface y) to neck. */
const topVaporPoints = computed(() => {
  const ys = TOP_Y0 + clamped.value * (TOP_Y1 - TOP_Y0);
  const w = widthAtTop(ys);
  const xl = CX - w / 2;
  const xr = CX + w / 2;
  return `${xl},${ys} ${xr},${ys} ${CX},${TOP_Y1}`;
});

/** Bottom dew pool polygon. */
const bottomPoolPoints = computed(() => {
  const ys = BOTTOM_Y1 - clamped.value * (BOTTOM_Y1 - BOTTOM_Y0);
  const w = widthAtBottom(ys);
  const xl = CX - w / 2;
  const xr = CX + w / 2;
  return `${xl},${ys} ${xr},${ys} ${CX},${BOTTOM_Y1}`;
});

/** Stream visible only mid-cycle. */
const streamOpacity = computed(() => {
  const p = clamped.value;
  if (p <= 0.02 || p >= 0.98) return 0;
  return 0.55;
});

/** Surface y of the bottom pool (used to position the splash). */
const poolSurfaceY = computed(
  () => BOTTOM_Y1 - clamped.value * (BOTTOM_Y1 - BOTTOM_Y0)
);

/* ---------------- Vapor puffs (top chamber) ----------------------------- */

type Puff = {
  id: number;
  x: number;
  startY: number;
  delay: number;
  duration: number;
  scale: number;
};

const VAPOR_COUNT = 9;
const vaporPuffs: Puff[] = Array.from({ length: VAPOR_COUNT }, (_, i) => {
  const x = 30 + ((i * 37) % 41);
  const startY = 64 + ((i * 7) % 12);
  const duration = 4 + ((i * 1.3) % 3.2);
  const delay = (i * 0.7) % 4;
  const scale = 0.8 + ((i * 0.21) % 0.7);
  return { id: i, x, startY, delay, duration, scale };
});

/* ---------------- Droplet emitter (Sweet Dew) --------------------------- */

type Drop = {
  id: number;
  x: number;
  size: number;
  duration: number;
  spawnedAt: number;
};

const drops = ref<Drop[]>([]);
const MAX_DROPS = 14;
let dropletTimer: number | null = null;
let dropId = 0;

const dropletIntervalMs = computed(() => {
  if (prefersReducedMotion.value) return 0;
  // Want ~250 droplets per cycle in the smallest scale; scale up gracefully.
  // 15 min cycle  → ~3.6 s gap, 2 h → ~28 s, 24 h → ~5.7 min.
  // Cap at 4 s so the user always sees something fall during a long view.
  const target = props.durationMs / 250;
  return Math.max(280, Math.min(4000, target));
});

function emitDrop() {
  if (drops.value.length >= MAX_DROPS) return;
  // No droplets at the very start or end (top chamber empty / pool full).
  const p = clamped.value;
  if (p <= 0.01 || p >= 0.99) return;
  dropId += 1;
  const x = CX + (Math.random() * 4 - 2);
  const size = 1.6 + Math.random() * 0.9;
  const duration = 0.85 + Math.random() * 0.55;
  drops.value.push({
    id: dropId,
    x,
    size,
    duration,
    spawnedAt: Date.now(),
  });
  // Self-clean after animation length + slack.
  window.setTimeout(() => {
    drops.value = drops.value.filter((d) => d.id !== dropId);
  }, duration * 1000 + 250);
}

function startEmitter() {
  stopEmitter();
  if (prefersReducedMotion.value) return;
  const ms = dropletIntervalMs.value;
  if (ms <= 0) return;
  // Initial puff so the first cycle isn't empty for many seconds.
  emitDrop();
  dropletTimer = window.setInterval(emitDrop, ms);
}

function stopEmitter() {
  if (dropletTimer != null) {
    window.clearInterval(dropletTimer);
    dropletTimer = null;
  }
}

watch(
  [() => props.durationMs, prefersReducedMotion],
  () => {
    startEmitter();
  },
  { immediate: true }
);

onUnmounted(() => {
  stopEmitter();
});

/* ---------------- Cycle flip ------------------------------------------- */

const isFlipping = ref(false);

watch(
  () => props.cycleKey,
  (next, prev) => {
    if (prev === undefined || prev === null) return;
    if (next === prev) return;
    isFlipping.value = true;
    drops.value = [];
  }
);

function onFlipEnd() {
  if (!isFlipping.value) return;
  isFlipping.value = false;
  emit("cycle-end");
}
</script>

<template>
  <figure
    class="microcosmic-hourglass"
    :class="[`microcosmic-hourglass--${size}`]"
    :style="{ '--mh-w': dims.w, '--mh-h': dims.h }"
  >
    <div
      class="microcosmic-hourglass__glass"
      :class="{ 'microcosmic-hourglass__glass--flip': isFlipping }"
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
          <linearGradient id="mhGlass" x1="50" y1="8" x2="50" y2="152" gradientUnits="userSpaceOnUse">
            <stop stop-color="rgba(255,255,255,0.34)" />
            <stop offset="0.5" stop-color="rgba(255,255,255,0.07)" />
            <stop offset="1" stop-color="rgba(255,255,255,0.22)" />
          </linearGradient>

          <radialGradient id="mhVapor" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#bee9ff" stop-opacity="0.85" />
            <stop offset="60%" stop-color="#7fb6e8" stop-opacity="0.32" />
            <stop offset="100%" stop-color="#5a89c8" stop-opacity="0" />
          </radialGradient>

          <linearGradient id="mhVaporColumn" x1="50" y1="12" x2="50" y2="78" gradientUnits="userSpaceOnUse">
            <stop stop-color="#cfe9ff" stop-opacity="0.18" />
            <stop offset="1" stop-color="#cfe9ff" stop-opacity="0.05" />
          </linearGradient>

          <linearGradient id="mhDew" x1="50" y1="78" x2="50" y2="142" gradientUnits="userSpaceOnUse">
            <stop stop-color="#fff7c8" stop-opacity="0.95" />
            <stop offset="0.55" stop-color="#f5c773" stop-opacity="0.92" />
            <stop offset="1" stop-color="#a06b1a" stop-opacity="0.95" />
          </linearGradient>

          <radialGradient id="mhDewGlow" cx="50%" cy="0%" r="60%">
            <stop offset="0%" stop-color="#fff5b0" stop-opacity="0.9" />
            <stop offset="100%" stop-color="#fff5b0" stop-opacity="0" />
          </radialGradient>

          <radialGradient id="mhCondense" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#fff3a8" stop-opacity="0.95" />
            <stop offset="100%" stop-color="#fff3a8" stop-opacity="0" />
          </radialGradient>

          <clipPath id="mhTopClip">
            <polygon points="17,12 83,12 50,78" />
          </clipPath>
          <clipPath id="mhBottomClip">
            <polygon points="50,78 83,142 17,142" />
          </clipPath>
        </defs>

        <!-- Glass outline -->
        <path
          d="M 17 12 L 83 12 L 50 78 L 83 142 L 17 142 L 50 78 Z"
          stroke="rgba(255,255,255,0.45)"
          stroke-width="2"
          stroke-linejoin="round"
          fill="url(#mhGlass)"
        />

        <!-- Top chamber: vapor column polygon (mass shrinks as progress→1) -->
        <polygon
          v-if="clamped < 0.999"
          :points="topVaporPoints"
          fill="url(#mhVaporColumn)"
        />

        <!-- Top chamber: drifting vapor puffs (clipped to top triangle) -->
        <g clip-path="url(#mhTopClip)" class="microcosmic-hourglass__vapor">
          <circle
            v-for="puff in vaporPuffs"
            :key="puff.id"
            class="microcosmic-hourglass__puff"
            :cx="puff.x"
            :cy="puff.startY"
            r="6"
            fill="url(#mhVapor)"
            :style="{
              animationDelay: `${puff.delay}s`,
              animationDuration: `${puff.duration}s`,
              transformBox: 'fill-box',
              transformOrigin: 'center',
              '--mh-puff-scale': puff.scale,
            }"
          />
        </g>

        <!-- Condensation point at the waist -->
        <circle
          v-if="streamOpacity > 0"
          cx="50"
          cy="78"
          r="4"
          fill="url(#mhCondense)"
          class="microcosmic-hourglass__condense"
        />

        <!-- Falling stream (visual continuity between droplets) -->
        <line
          x1="50"
          y1="76"
          x2="50"
          y2="86"
          stroke="url(#mhDew)"
          stroke-width="1.6"
          stroke-linecap="round"
          :opacity="streamOpacity"
        />

        <!-- Sweet-dew droplets falling through the neck -->
        <g clip-path="url(#mhBottomClip)">
          <circle
            v-for="drop in drops"
            :key="drop.id"
            class="microcosmic-hourglass__drop"
            :cx="drop.x"
            cy="80"
            :r="drop.size"
            fill="url(#mhDew)"
            :style="{
              animationDuration: `${drop.duration}s`,
            }"
          />
          <!-- Splash ring on impact at the pool surface -->
          <circle
            v-for="drop in drops"
            :key="`splash-${drop.id}`"
            class="microcosmic-hourglass__splash"
            :cx="drop.x"
            :cy="poolSurfaceY"
            r="0"
            stroke="rgba(255, 230, 150, 0.7)"
            stroke-width="0.6"
            fill="none"
            :style="{
              animationDuration: `${drop.duration}s`,
            }"
          />
        </g>

        <!-- Bottom pool: glowing liquid with subtle surface swell -->
        <polygon
          v-if="clamped > 0.001"
          :points="bottomPoolPoints"
          fill="url(#mhDew)"
          class="microcosmic-hourglass__pool"
        />
        <ellipse
          v-if="clamped > 0.04"
          :cx="CX"
          :cy="poolSurfaceY"
          :rx="widthAtBottom(poolSurfaceY) / 2"
          ry="1.4"
          fill="url(#mhDewGlow)"
          class="microcosmic-hourglass__sheen"
        />
      </svg>
    </div>

    <figcaption v-if="label || sublabel" class="microcosmic-hourglass__caption">
      <span v-if="label" class="microcosmic-hourglass__label">{{ label }}</span>
      <span v-if="sublabel" class="microcosmic-hourglass__sublabel">{{ sublabel }}</span>
    </figcaption>
  </figure>
</template>

<style scoped>
.microcosmic-hourglass {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin: 0;
}

.microcosmic-hourglass__glass {
  width: var(--mh-w);
  height: var(--mh-h);
  transform-origin: 50% 50%;
  filter: drop-shadow(0 0 6px rgba(255, 232, 180, 0.18));
}

.microcosmic-hourglass__caption {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-variant-numeric: tabular-nums;
  line-height: 1.05;
  gap: 1px;
}

.microcosmic-hourglass__label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.7);
}

.microcosmic-hourglass__sublabel {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.45);
}

@media (prefers-reduced-motion: no-preference) {
  .microcosmic-hourglass__glass--flip {
    animation: mhFlip 0.85s cubic-bezier(0.42, 0, 0.58, 1);
  }
  .microcosmic-hourglass__puff {
    animation-name: mhVaporRise;
    animation-iteration-count: infinite;
    animation-timing-function: ease-in-out;
    opacity: 0;
  }
  .microcosmic-hourglass__condense {
    animation: mhCondensePulse 1.6s ease-in-out infinite;
    transform-box: fill-box;
    transform-origin: center;
  }
  .microcosmic-hourglass__drop {
    animation-name: mhDropFall;
    animation-timing-function: cubic-bezier(0.55, 0, 0.7, 1);
    animation-fill-mode: forwards;
  }
  .microcosmic-hourglass__splash {
    animation-name: mhSplash;
    animation-timing-function: ease-out;
    animation-fill-mode: forwards;
    opacity: 0;
  }
  .microcosmic-hourglass__sheen {
    animation: mhSheen 2.6s ease-in-out infinite;
    transform-box: fill-box;
    transform-origin: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .microcosmic-hourglass__glass--flip {
    animation: mhFlipReduced 0.35s ease-out;
  }
  .microcosmic-hourglass__puff {
    opacity: 0.45;
  }
}

@keyframes mhFlip {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes mhFlipReduced {
  from {
    opacity: 0.7;
  }
  to {
    opacity: 1;
  }
}

@keyframes mhVaporRise {
  0% {
    transform: translate(0, 6px) scale(calc(var(--mh-puff-scale) * 0.6));
    opacity: 0;
  }
  20% {
    opacity: 0.85;
  }
  100% {
    transform: translate(0, -56px) scale(calc(var(--mh-puff-scale) * 1.3));
    opacity: 0;
  }
}

@keyframes mhCondensePulse {
  0%,
  100% {
    transform: scale(0.8);
    opacity: 0.55;
  }
  50% {
    transform: scale(1.4);
    opacity: 1;
  }
}

@keyframes mhDropFall {
  0% {
    transform: translateY(0);
    opacity: 0.0;
  }
  10% {
    opacity: 1;
  }
  85% {
    opacity: 1;
  }
  100% {
    transform: translateY(58px);
    opacity: 0;
  }
}

@keyframes mhSplash {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  85% {
    transform: scale(0);
    opacity: 0;
  }
  90% {
    transform: scale(1);
    opacity: 0.8;
  }
  100% {
    transform: scale(2.6);
    opacity: 0;
  }
}

@keyframes mhSheen {
  0%,
  100% {
    transform: scaleX(1);
    opacity: 0.6;
  }
  50% {
    transform: scaleX(1.08);
    opacity: 0.85;
  }
}
</style>
