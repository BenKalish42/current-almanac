<script setup lang="ts">
/**
 * FishermanScene — anime-style old Southeast-Asian fisherman.
 *
 * Sitting cross-legged on a dock, eyes closed, faintly smiling. Holds a long
 * rod across his lap into the water. Idle sway loops gently; a small tug fires
 * roughly every `tugIntervalMs`. On every Ke (15-min) boundary, a "big tug"
 * plays and a fish arcs onto the dock pile behind him.
 *
 * No external assets — pure inline SVG. Respects prefers-reduced-motion.
 */

import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { usePrefersReducedMotion } from "@/utils/usePrefersReducedMotion";

const props = withDefaults(
  defineProps<{
    /** Used to drive deterministic catches when external clock changes. */
    moment?: Date;
    /** Cycle key for fish-catch trigger (Ke boundary). */
    keKey?: string | number | null;
    /** Cycle key that resets the fish pile (e.g. local midnight). */
    dayKey?: string | number | null;
    /** Idle tug interval in ms. */
    tugIntervalMs?: number;
  }>(),
  {
    moment: () => new Date(),
    keKey: null,
    dayKey: null,
    tugIntervalMs: 8000,
  }
);

const prefersReducedMotion = usePrefersReducedMotion();

/* ---------------- Idle tug ---------------------------------------------- */

const tugging = ref(false);
let tugTimer: number | null = null;

function scheduleTug() {
  if (tugTimer != null) {
    clearTimeout(tugTimer);
    tugTimer = null;
  }
  // Slight jitter (±1s) so it doesn't feel mechanical.
  const jitter = (Math.random() * 2000 - 1000);
  const delay = Math.max(2000, props.tugIntervalMs + jitter);
  tugTimer = window.setTimeout(() => {
    if (!prefersReducedMotion.value && !catching.value) {
      tugging.value = true;
      window.setTimeout(() => {
        tugging.value = false;
        scheduleTug();
      }, 480);
    } else {
      scheduleTug();
    }
  }, delay);
}

onMounted(() => {
  scheduleTug();
});

onUnmounted(() => {
  if (tugTimer != null) clearTimeout(tugTimer);
});

/* ---------------- Catch (Ke boundary) ----------------------------------- */

type FishOnDock = { id: number; offsetX: number; offsetY: number; flip: boolean; createdAt: number };
const fishPile = ref<FishOnDock[]>([]);
const catching = ref(false);
const splashes = ref<{ id: number }[]>([]);
let catchId = 0;
let splashId = 0;

const PILE_KEY = "current_fisherman_pile_v1";

function loadPile() {
  try {
    const raw = localStorage.getItem(PILE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw) as { day?: string; pile?: FishOnDock[] };
    if (!parsed?.day || parsed.day !== String(props.dayKey ?? "")) return;
    if (Array.isArray(parsed.pile)) fishPile.value = parsed.pile.slice(-8);
  } catch {
    /* ignore */
  }
}

function savePile() {
  try {
    localStorage.setItem(
      PILE_KEY,
      JSON.stringify({ day: String(props.dayKey ?? ""), pile: fishPile.value })
    );
  } catch {
    /* ignore */
  }
}

onMounted(loadPile);

function pushFish() {
  catchId += 1;
  // Stack behind the fisherman in a loose pile.
  const idx = fishPile.value.length;
  const offsetX = ((idx % 4) - 1.5) * 9; // tile 4-wide
  const offsetY = -Math.floor(idx / 4) * 6;
  const flip = idx % 2 === 0;
  fishPile.value = [...fishPile.value, { id: catchId, offsetX, offsetY, flip, createdAt: Date.now() }].slice(-8);
  savePile();
}

function spawnSplash() {
  splashId += 1;
  const id = splashId;
  splashes.value = [...splashes.value, { id }];
  window.setTimeout(() => {
    splashes.value = splashes.value.filter((s) => s.id !== id);
  }, 900);
}

watch(
  () => props.keKey,
  (next, prev) => {
    if (prev === undefined || prev === null) return;
    if (next === prev) return;
    // New Ke → catch a fish.
    if (prefersReducedMotion.value) {
      pushFish();
      return;
    }
    catching.value = true;
    spawnSplash();
    // After the rod-bend + arc finishes, drop the fish onto the pile.
    window.setTimeout(() => {
      pushFish();
      catching.value = false;
    }, 950);
  }
);

watch(
  () => props.dayKey,
  (next, prev) => {
    if (prev === undefined || prev === null) return;
    if (next === prev) return;
    // New day — clear yesterday's pile.
    fishPile.value = [];
    savePile();
  }
);

/* ---------------- Style classes ---------------------------------------- */

const rodClasses = computed(() => ({
  "fisherman-scene__rod": true,
  "fisherman-scene__rod--tug": tugging.value,
  "fisherman-scene__rod--catch": catching.value,
}));

const lineClasses = computed(() => ({
  "fisherman-scene__line": true,
  "fisherman-scene__line--tug": tugging.value,
  "fisherman-scene__line--catch": catching.value,
}));

const bobberClasses = computed(() => ({
  "fisherman-scene__bobber": true,
  "fisherman-scene__bobber--tug": tugging.value,
  "fisherman-scene__bobber--catch": catching.value,
}));
</script>

<template>
  <div class="fisherman-scene" role="img" aria-label="Old fisherman patiently fishing from a dock">
    <svg
      viewBox="0 0 200 260"
      xmlns="http://www.w3.org/2000/svg"
      class="fisherman-scene__svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="fishermanSky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(255,225,180,0.18)" />
          <stop offset="100%" stop-color="rgba(70,110,150,0.04)" />
        </linearGradient>
        <linearGradient id="fishermanWater" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#1d4a6a" />
          <stop offset="100%" stop-color="#0c2436" />
        </linearGradient>
        <linearGradient id="fishermanDock" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#7a4a26" />
          <stop offset="100%" stop-color="#3d2210" />
        </linearGradient>
        <linearGradient id="fishermanRobe" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#a08259" />
          <stop offset="100%" stop-color="#5a4126" />
        </linearGradient>
        <linearGradient id="fishermanHat" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#dcc187" />
          <stop offset="100%" stop-color="#8c6c34" />
        </linearGradient>
        <radialGradient id="fishermanSkin" cx="50%" cy="40%" r="65%">
          <stop offset="0%" stop-color="#f3d3a4" />
          <stop offset="100%" stop-color="#c79b6a" />
        </radialGradient>
        <linearGradient id="fishermanFish" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#9bd0e5" />
          <stop offset="100%" stop-color="#3f7e9c" />
        </linearGradient>

        <!-- Anime fish sprite: ovular body + triangular tail + tiny eye -->
        <symbol id="fishermanFishSprite" viewBox="-12 -6 24 12" overflow="visible">
          <ellipse cx="0" cy="0" rx="9" ry="4" fill="url(#fishermanFish)" stroke="#1f3d52" stroke-width="0.6" />
          <path d="M 8 0 L 14 -5 L 14 5 Z" fill="#3f7e9c" stroke="#1f3d52" stroke-width="0.6" stroke-linejoin="round" />
          <circle cx="-5" cy="-1" r="0.9" fill="#0a1a2a" />
          <path d="M -2 -3 Q 4 -5 6 -2" stroke="#cce4ee" stroke-width="0.5" fill="none" stroke-linecap="round" />
        </symbol>
      </defs>

      <!-- Backdrop sky/water -->
      <rect x="0" y="0" width="200" height="170" fill="url(#fishermanSky)" />
      <rect x="0" y="170" width="200" height="90" fill="url(#fishermanWater)" />

      <!-- Distant ripple lines -->
      <g class="fisherman-scene__ripple">
        <path d="M 0 188 Q 50 184 100 188 T 200 188" stroke="rgba(255,255,255,0.16)" stroke-width="0.7" fill="none" />
        <path d="M 0 200 Q 60 196 120 200 T 200 200" stroke="rgba(255,255,255,0.10)" stroke-width="0.6" fill="none" />
        <path d="M 0 214 Q 70 210 140 214 T 200 214" stroke="rgba(255,255,255,0.07)" stroke-width="0.5" fill="none" />
      </g>

      <!-- Dock (planks) -->
      <g>
        <rect x="0" y="172" width="200" height="14" fill="url(#fishermanDock)" />
        <line x1="0" y1="178" x2="200" y2="178" stroke="rgba(0,0,0,0.45)" stroke-width="0.6" />
        <line x1="0" y1="184" x2="200" y2="184" stroke="rgba(0,0,0,0.55)" stroke-width="0.6" />
        <!-- Dock posts -->
        <rect x="14" y="184" width="6" height="50" fill="#3d2210" />
        <rect x="178" y="184" width="6" height="50" fill="#3d2210" />
      </g>

      <!-- Fish pile (behind fisherman, on the dock) -->
      <g class="fisherman-scene__pile">
        <use
          v-for="fish in fishPile"
          :key="fish.id"
          href="#fishermanFishSprite"
          :x="36 + fish.offsetX"
          :y="170 + fish.offsetY"
          :transform="fish.flip ? `rotate(180 ${36 + fish.offsetX} ${170 + fish.offsetY})` : ''"
          class="fisherman-scene__fish"
        />
      </g>

      <!-- Fisherman group (sways gently). Faces right (toward the card). -->
      <g
        class="fisherman-scene__figure"
        :class="{ 'fisherman-scene__figure--catch': catching }"
      >
        <!-- Crossed legs -->
        <ellipse cx="92" cy="178" rx="22" ry="9" fill="url(#fishermanRobe)" />
        <path
          d="M 76 174 Q 82 168 96 168 Q 110 168 116 174 L 116 178 L 76 178 Z"
          fill="url(#fishermanRobe)"
        />

        <!-- Torso -->
        <path
          d="M 82 142 Q 78 158 80 174 L 110 174 Q 112 158 108 142 Q 104 130 95 128 Q 86 130 82 142 Z"
          fill="url(#fishermanRobe)"
          stroke="#3a280f"
          stroke-width="1"
          stroke-linejoin="round"
        />
        <!-- Sash detail -->
        <path d="M 82 158 Q 95 156 108 158 L 108 162 Q 95 160 82 162 Z" fill="#39230f" opacity="0.7" />

        <!-- Right arm holding rod (forward), animated on tug -->
        <g class="fisherman-scene__arm-right">
          <path
            d="M 105 142 Q 116 144 124 152 Q 128 156 126 160"
            stroke="url(#fishermanRobe)"
            stroke-width="7"
            stroke-linecap="round"
            fill="none"
          />
          <!-- Hand -->
          <circle cx="126" cy="160" r="3.4" fill="url(#fishermanSkin)" stroke="#3a280f" stroke-width="0.6" />
        </g>

        <!-- Left arm resting on lap -->
        <path
          d="M 84 142 Q 78 152 78 168"
          stroke="url(#fishermanRobe)"
          stroke-width="7"
          stroke-linecap="round"
          fill="none"
        />
        <circle cx="78" cy="168" r="3" fill="url(#fishermanSkin)" stroke="#3a280f" stroke-width="0.6" />

        <!-- Neck -->
        <rect x="91" y="124" width="8" height="8" fill="url(#fishermanSkin)" />

        <!-- Head -->
        <ellipse cx="95" cy="116" rx="13" ry="14" fill="url(#fishermanSkin)" stroke="#3a280f" stroke-width="0.8" />
        <!-- Closed smiling eyes ‿ ‿ -->
        <path d="M 87 116 q 2 -2 4 0" stroke="#1d1206" stroke-width="1.1" fill="none" stroke-linecap="round" />
        <path d="M 100 116 q 2 -2 4 0" stroke="#1d1206" stroke-width="1.1" fill="none" stroke-linecap="round" />
        <!-- Subtle blush -->
        <ellipse cx="89" cy="120" rx="2" ry="0.9" fill="rgba(220,120,90,0.4)" />
        <ellipse cx="101" cy="120" rx="2" ry="0.9" fill="rgba(220,120,90,0.4)" />
        <!-- Soft smile -->
        <path d="M 91 122 q 4 3 8 0" stroke="#1d1206" stroke-width="1" fill="none" stroke-linecap="round" />
        <!-- A few stray gray hair strands -->
        <path d="M 84 108 q 3 -2 6 0" stroke="#d8d3c5" stroke-width="0.8" fill="none" />
        <path d="M 100 108 q 3 -2 6 0" stroke="#d8d3c5" stroke-width="0.8" fill="none" />
        <!-- Wispy beard -->
        <path d="M 92 128 q 3 6 6 0" stroke="#d8d3c5" stroke-width="0.7" fill="none" stroke-linecap="round" />

        <!-- Conical hat -->
        <g>
          <path
            d="M 70 108 L 95 80 L 120 108 Z"
            fill="url(#fishermanHat)"
            stroke="#3a280f"
            stroke-width="0.8"
            stroke-linejoin="round"
          />
          <!-- Brim -->
          <ellipse cx="95" cy="108" rx="28" ry="4.5" fill="url(#fishermanHat)" stroke="#3a280f" stroke-width="0.6" />
          <!-- Weave lines -->
          <path d="M 75 105 Q 95 102 115 105" stroke="rgba(60,40,15,0.5)" stroke-width="0.5" fill="none" />
          <path d="M 80 100 Q 95 96 110 100" stroke="rgba(60,40,15,0.45)" stroke-width="0.5" fill="none" />
          <path d="M 85 95 Q 95 92 105 95" stroke="rgba(60,40,15,0.4)" stroke-width="0.5" fill="none" />
          <!-- Apex point -->
          <circle cx="95" cy="80" r="1.4" fill="#5a4022" />
        </g>
      </g>

      <!-- Fishing rod, line, bobber (overlay above figure for proper z) -->
      <g
        :class="rodClasses"
        style="transform-origin: 126px 160px"
      >
        <!-- Rod -->
        <line
          x1="126"
          y1="160"
          x2="186"
          y2="118"
          stroke="#2a1a0a"
          stroke-width="1.6"
          stroke-linecap="round"
        />
        <!-- Rod tip highlight -->
        <line
          x1="170"
          y1="129"
          x2="186"
          y2="118"
          stroke="#7a5430"
          stroke-width="1"
          stroke-linecap="round"
        />
      </g>

      <!-- Fishing line: rod tip → bobber on water -->
      <path
        :class="lineClasses"
        d="M 186 118 Q 186 170 178 220"
        stroke="rgba(220,220,220,0.6)"
        stroke-width="0.6"
        fill="none"
      />

      <!-- Bobber -->
      <g :class="bobberClasses" style="transform-origin: 178px 220px">
        <circle cx="178" cy="220" r="3" fill="#d6443a" stroke="#4a1410" stroke-width="0.6" />
        <rect x="176" y="220" width="4" height="2" fill="#f4f4f4" />
      </g>

      <!-- Splash rings spawned on catch -->
      <g>
        <circle
          v-for="splash in splashes"
          :key="splash.id"
          cx="178"
          cy="220"
          r="2"
          stroke="rgba(255,255,255,0.85)"
          stroke-width="0.6"
          fill="none"
          class="fisherman-scene__splash"
        />
      </g>

      <!-- Caught fish flying through the air on a Ke catch -->
      <g v-if="catching" class="fisherman-scene__catch-fish">
        <use href="#fishermanFishSprite" x="178" y="220">
          <animateMotion
            dur="0.9s"
            fill="freeze"
            path="M 0 0 Q -50 -100 -140 -50"
            calcMode="spline"
            keySplines="0.25 0.1 0.5 1"
            keyTimes="0;1"
          />
        </use>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.fisherman-scene {
  width: 100%;
  max-width: 220px;
  aspect-ratio: 200 / 260;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  pointer-events: none;
}

.fisherman-scene__svg {
  width: 100%;
  height: 100%;
  display: block;
}

@media (prefers-reduced-motion: no-preference) {
  .fisherman-scene__figure {
    transform-origin: 95px 175px;
    animation: fishermanSway 5.4s ease-in-out infinite alternate;
  }

  .fisherman-scene__figure--catch {
    animation: fishermanSway 5.4s ease-in-out infinite alternate, fishermanCatch 0.9s ease-out;
  }

  .fisherman-scene__rod--tug {
    animation: fishermanRodTug 0.45s ease-in-out;
  }

  .fisherman-scene__rod--catch {
    animation: fishermanRodCatch 0.9s ease-out;
  }

  .fisherman-scene__bobber--tug {
    animation: fishermanBobberDip 0.45s ease-in-out;
  }

  .fisherman-scene__bobber--catch {
    animation: fishermanBobberDip 0.45s ease-in-out;
  }

  .fisherman-scene__line--tug {
    animation: fishermanLineFlex 0.45s ease-in-out;
  }

  .fisherman-scene__ripple {
    animation: fishermanRipple 12s linear infinite;
    transform-origin: 100px 200px;
  }

  .fisherman-scene__splash {
    animation: fishermanSplash 0.9s ease-out forwards;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fisherman-scene__figure,
  .fisherman-scene__rod,
  .fisherman-scene__bobber,
  .fisherman-scene__line,
  .fisherman-scene__ripple {
    animation: none !important;
  }
}

@keyframes fishermanSway {
  from {
    transform: translateY(-1.2px) rotate(-1.6deg);
  }
  to {
    transform: translateY(1.4px) rotate(1.6deg);
  }
}

@keyframes fishermanCatch {
  0% { transform: rotate(-1.2deg) translateY(0); }
  35% { transform: rotate(1.4deg) translateY(-1.5px); }
  60% { transform: rotate(-0.9deg) translateY(0.5px); }
  100% { transform: rotate(0deg) translateY(0); }
}

@keyframes fishermanRodTug {
  0% { transform: rotate(0deg); }
  35% { transform: rotate(-9deg); }
  65% { transform: rotate(4deg); }
  100% { transform: rotate(0deg); }
}

@keyframes fishermanRodCatch {
  0% { transform: rotate(0deg); }
  20% { transform: rotate(-22deg); }
  45% { transform: rotate(8deg); }
  70% { transform: rotate(-4deg); }
  100% { transform: rotate(0deg); }
}

@keyframes fishermanBobberDip {
  0% { transform: translateY(0); }
  50% { transform: translateY(3.5px); }
  100% { transform: translateY(0); }
}

@keyframes fishermanLineFlex {
  0%,
  100% { transform: none; }
  50% { transform: translateY(-1.5px); }
}

@keyframes fishermanRipple {
  from { transform: translateX(0); }
  to { transform: translateX(-30px); }
}

@keyframes fishermanSplash {
  0% { r: 1; opacity: 0.9; }
  100% { r: 9; opacity: 0; }
}
</style>
