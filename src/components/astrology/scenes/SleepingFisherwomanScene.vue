<script setup lang="ts">
/**
 * SleepingFisherwomanScene — woman asleep on a small wooden boat.
 *
 * Reference cue: red blanket, head pillowed at the bow, blue water, distant
 * wisp-tree silhouette. Anime-flat illustration.
 *
 * Rhythm:
 *   - Ribcage scales subtly (`breath`) on a phase-locked integer-second cycle.
 *   - Boat rocks slowly (`boat-bob`).
 *   - "Z-Z-z" letters drift up from her mouth, staggered.
 *
 * Inputs:
 *   - moment: Date  → used to phase-lock the breath cycle to wall time.
 *   - breathPeriodSec: integer seconds (default 4).
 */

import { computed, onMounted, onUnmounted, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    moment?: Date;
    /** Full inhale + exhale cycle, in whole seconds. */
    breathPeriodSec?: number;
  }>(),
  {
    moment: () => new Date(),
    breathPeriodSec: 4,
  }
);

const period = computed(() => {
  const p = Math.round(props.breathPeriodSec ?? 4);
  return Math.max(2, Math.min(8, p));
});

/** Negative animation-delay phase-locks the breath cycle to wall-clock seconds. */
const breathDelay = ref<number>(0);

function recomputePhase() {
  const m = props.moment ?? new Date();
  const ms = m.getTime();
  const p = period.value * 1000;
  const phase = ms % p;
  breathDelay.value = -(phase / 1000);
}

onMounted(recomputePhase);
watch(() => [props.moment, period.value], recomputePhase, { deep: false });

/** Re-sync every minute to compensate for any animation drift. */
let resyncId: number | null = null;
onMounted(() => {
  resyncId = window.setInterval(recomputePhase, 60_000);
});
onUnmounted(() => {
  if (resyncId != null) window.clearInterval(resyncId);
});

const breathStyle = computed(() => ({
  "--sf-breath-period": `${period.value}s`,
  "--sf-breath-delay": `${breathDelay.value}s`,
}));
</script>

<template>
  <div class="sleeping-fisherwoman-scene" role="img" aria-label="Woman sleeping peacefully on a small boat">
    <svg
      viewBox="0 0 240 200"
      xmlns="http://www.w3.org/2000/svg"
      class="sleeping-fisherwoman-scene__svg"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="sfSky" cx="50%" cy="50%" r="55%">
          <stop offset="0%" stop-color="rgba(218,180,200,0.55)" />
          <stop offset="80%" stop-color="rgba(120,140,180,0.18)" />
          <stop offset="100%" stop-color="rgba(60,80,110,0)" />
        </radialGradient>
        <radialGradient id="sfWater" cx="50%" cy="60%" r="60%">
          <stop offset="0%" stop-color="rgba(40,90,140,0.7)" />
          <stop offset="80%" stop-color="rgba(20,55,90,0.4)" />
          <stop offset="100%" stop-color="rgba(8,18,30,0)" />
        </radialGradient>
        <linearGradient id="sfHull" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#3a2010" />
          <stop offset="100%" stop-color="#0e0700" />
        </linearGradient>
        <linearGradient id="sfHullDeck" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#7a4d2a" />
          <stop offset="100%" stop-color="#3a2010" />
        </linearGradient>
        <linearGradient id="sfBlanket" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#d24e3c" />
          <stop offset="100%" stop-color="#7a2018" />
        </linearGradient>
        <linearGradient id="sfBlanketShine" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(255,200,180,0.45)" />
          <stop offset="100%" stop-color="rgba(255,200,180,0)" />
        </linearGradient>
        <radialGradient id="sfSkin" cx="50%" cy="40%" r="65%">
          <stop offset="0%" stop-color="#f5d6b1" />
          <stop offset="100%" stop-color="#c79b6f" />
        </radialGradient>
      </defs>

      <!-- Sky vignette (radial; fades to transparent) -->
      <ellipse cx="120" cy="60" rx="160" ry="60" fill="url(#sfSky)" />
      <!-- Soft cloud wisps -->
      <ellipse cx="70" cy="45" rx="38" ry="5" fill="rgba(255,255,255,0.22)" />
      <ellipse cx="180" cy="38" rx="28" ry="4" fill="rgba(255,255,255,0.16)" />

      <!-- Distant tree silhouette (right bank) -->
      <g opacity="0.7">
        <path
          d="M 200 120 Q 196 100 200 85 Q 196 80 198 70 Q 202 65 206 70 Q 210 60 214 70 Q 220 65 222 75 Q 226 80 224 90 Q 228 100 220 110 L 218 120 Z"
          fill="#0c2a18"
        />
        <line x1="210" y1="105" x2="210" y2="120" stroke="#0c1a08" stroke-width="0.9" />
      </g>

      <!-- Water vignette (oval; no hard edges) -->
      <ellipse cx="120" cy="160" rx="135" ry="42" fill="url(#sfWater)" />

      <!-- Distant ripple lines -->
      <g opacity="0.55">
        <path d="M 28 142 Q 70 140 110 142 T 210 142" stroke="rgba(255,255,255,0.18)" stroke-width="0.6" fill="none" stroke-linecap="round" />
        <path d="M 36 178 Q 80 176 124 178 T 204 178" stroke="rgba(255,255,255,0.12)" stroke-width="0.5" fill="none" stroke-linecap="round" />
      </g>

      <!-- Boat group -->
      <g class="sleeping-fisherwoman-scene__boat">
        <!-- Hull (water-line behind hull) -->
        <path
          d="M 18 158 Q 50 150 120 150 Q 200 150 222 158 L 210 178 Q 180 184 120 184 Q 60 184 30 178 Z"
          fill="url(#sfHull)"
          stroke="#000"
          stroke-width="0.6"
        />
        <!-- Deck -->
        <path
          d="M 24 158 Q 60 152 120 152 Q 180 152 216 158 L 200 168 Q 170 162 120 162 Q 70 162 40 168 Z"
          fill="url(#sfHullDeck)"
        />
        <!-- Plank seams -->
        <line x1="36" y1="166" x2="200" y2="166" stroke="#1a0d04" stroke-width="0.5" />
        <line x1="32" y1="172" x2="206" y2="172" stroke="#1a0d04" stroke-width="0.5" />

        <!-- Pillow -->
        <ellipse cx="56" cy="146" rx="14" ry="6" fill="#f3ece0" stroke="#a89a82" stroke-width="0.5" />
        <ellipse cx="56" cy="144" rx="10" ry="3" fill="#fff7ea" />

        <!-- Feet end (peeking out at right, far end of boat) -->
        <ellipse cx="178" cy="148" rx="6" ry="3" fill="url(#sfSkin)" stroke="#3a280f" stroke-width="0.4" />

        <!-- Body covered by blanket. Ribcage group breathes (scaleY pulse). -->
        <g
          class="sleeping-fisherwoman-scene__ribcage"
          :style="breathStyle"
        >
          <!-- Blanket main shape: from chest to feet -->
          <path
            d="M 70 144 Q 80 136 100 136 Q 130 136 160 140 Q 180 144 178 152 Q 170 160 130 160 Q 88 160 76 156 Q 64 150 70 144 Z"
            fill="url(#sfBlanket)"
            stroke="#52120c"
            stroke-width="0.7"
          />
          <!-- Chest hump (ribcage mound) — emphasized by breath -->
          <path
            d="M 80 144 Q 100 132 122 144 Q 122 152 100 154 Q 80 152 80 144 Z"
            fill="url(#sfBlanket)"
            opacity="0.55"
          />
          <!-- Blanket folds -->
          <path d="M 90 144 Q 100 142 110 144" stroke="rgba(0,0,0,0.35)" stroke-width="0.5" fill="none" />
          <path d="M 120 145 Q 132 143 144 146" stroke="rgba(0,0,0,0.35)" stroke-width="0.5" fill="none" />
          <path d="M 150 148 Q 160 147 168 150" stroke="rgba(0,0,0,0.3)" stroke-width="0.5" fill="none" />

          <!-- Highlight ribcage glow — pulses with breath -->
          <ellipse
            cx="100"
            cy="142"
            rx="24"
            ry="7"
            fill="url(#sfBlanketShine)"
          />
        </g>

        <!-- Head -->
        <g>
          <!-- Hair (back) -->
          <path
            d="M 50 142 Q 38 134 44 122 Q 52 114 64 116 Q 76 116 78 126 Q 80 138 70 144 Z"
            fill="#1a0e08"
            stroke="#000"
            stroke-width="0.4"
          />
          <!-- Face -->
          <ellipse cx="62" cy="134" rx="10.5" ry="9" fill="url(#sfSkin)" stroke="#3a280f" stroke-width="0.6" />
          <!-- Closed eye (only one visible from this angle) -->
          <path d="M 64 134 q 2 -2 4 0" stroke="#1d1206" stroke-width="0.9" fill="none" stroke-linecap="round" />
          <!-- Eyelashes -->
          <path d="M 64 134 q 0 -1.5 -0.6 -2" stroke="#1d1206" stroke-width="0.5" fill="none" stroke-linecap="round" />
          <path d="M 67 134 q 0.4 -1.5 1 -2" stroke="#1d1206" stroke-width="0.5" fill="none" stroke-linecap="round" />
          <!-- Soft cheek blush -->
          <ellipse cx="68" cy="138" rx="2" ry="1" fill="rgba(220,120,90,0.35)" />
          <!-- Slightly parted mouth -->
          <ellipse cx="71" cy="140" rx="1.2" ry="0.6" fill="#7a3024" />
          <!-- Small nose hint -->
          <path d="M 70 137 q 1 -0.3 0 -1.5" stroke="#7a4f31" stroke-width="0.4" fill="none" />
          <!-- Hair (front strand falling forward) -->
          <path d="M 53 126 Q 60 124 66 128" stroke="#1a0e08" stroke-width="1.2" fill="none" stroke-linecap="round" />
          <!-- Hair bun back -->
          <circle cx="44" cy="124" r="3" fill="#1a0e08" />
        </g>
      </g>

      <!-- Z-z-Z drifting from her mouth -->
      <g class="sleeping-fisherwoman-scene__zzz">
        <text x="74" y="138" class="sleeping-fisherwoman-scene__z sleeping-fisherwoman-scene__z--1">Z</text>
        <text x="74" y="138" class="sleeping-fisherwoman-scene__z sleeping-fisherwoman-scene__z--2">z</text>
        <text x="74" y="138" class="sleeping-fisherwoman-scene__z sleeping-fisherwoman-scene__z--3">Z</text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.sleeping-fisherwoman-scene {
  width: 100%;
  max-width: 240px;
  aspect-ratio: 240 / 200;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.sleeping-fisherwoman-scene__svg {
  width: 100%;
  height: 100%;
  display: block;
}

@media (prefers-reduced-motion: no-preference) {
  .sleeping-fisherwoman-scene__boat {
    transform-origin: 120px 168px;
    animation: sfBoatBob 5.8s ease-in-out infinite alternate;
  }
  .sleeping-fisherwoman-scene__ribcage {
    transform-origin: 100px 156px;
    animation: sfBreath var(--sf-breath-period, 4s) ease-in-out infinite;
    animation-delay: var(--sf-breath-delay, 0s);
  }
  .sleeping-fisherwoman-scene__z {
    animation: sfZzz 3s ease-out infinite;
    transform-box: fill-box;
    transform-origin: center;
  }
  .sleeping-fisherwoman-scene__z--1 { animation-delay: 0s; }
  .sleeping-fisherwoman-scene__z--2 { animation-delay: 1s; }
  .sleeping-fisherwoman-scene__z--3 { animation-delay: 2s; }
}

@media (prefers-reduced-motion: reduce) {
  .sleeping-fisherwoman-scene__boat,
  .sleeping-fisherwoman-scene__z {
    animation: none !important;
  }
  .sleeping-fisherwoman-scene__ribcage {
    transform-origin: 100px 156px;
    animation-duration: var(--sf-breath-period, 4s);
    animation-name: sfBreathReduced;
    animation-iteration-count: infinite;
    animation-timing-function: ease-in-out;
  }
}

.sleeping-fisherwoman-scene__z {
  font-family: "Merriweather", Georgia, serif;
  font-style: italic;
  font-weight: 700;
  font-size: 14px;
  fill: rgba(255, 255, 255, 0.85);
  paint-order: stroke;
  stroke: rgba(0, 0, 0, 0.4);
  stroke-width: 0.5px;
  opacity: 0;
}

.sleeping-fisherwoman-scene__z--2 { font-size: 16px; }
.sleeping-fisherwoman-scene__z--3 { font-size: 18px; }

@keyframes sfBreath {
  0%,
  100% {
    transform: scaleY(1);
  }
  45%,
  55% {
    transform: scaleY(1.1);
  }
}

@keyframes sfBreathReduced {
  0%,
  100% { transform: scaleY(1); }
  50% { transform: scaleY(1.02); }
}

@keyframes sfBoatBob {
  from {
    transform: translateY(-1.4px) rotate(-1.4deg);
  }
  to {
    transform: translateY(1.6px) rotate(1.4deg);
  }
}

@keyframes sfZzz {
  0% {
    transform: translate(0, 0) scale(0.6);
    opacity: 0;
  }
  20% {
    opacity: 0.95;
  }
  100% {
    transform: translate(22px, -28px) scale(1.15);
    opacity: 0;
  }
}
</style>
