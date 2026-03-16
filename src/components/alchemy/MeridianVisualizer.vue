<script setup lang="ts">
import { computed } from "vue";
import { useAlchemyStore } from "@/stores/alchemyStore";

const alchemyStore = useAlchemyStore();

/** Daoist Five Elements (Wu Xing) → meridians */
const ELEMENT_MERIDIANS: Record<string, string[]> = {
  Wood: ["Liver", "Gallbladder"],
  Fire: ["Heart", "Small Intestine", "Pericardium", "San Jiao", "Triple Burner"],
  Earth: ["Spleen", "Stomach"],
  Metal: ["Lung", "Large Intestine"],
  Water: ["Kidney", "Bladder"],
};

const ELEMENT_ORDER = ["Wood", "Fire", "Earth", "Metal", "Water"] as const;

/** Element-specific fill colors for SVG circles (Tailwind fill utilities) */
const ELEMENT_FILL: Record<string, string> = {
  Wood: "fill-emerald-600",
  Fire: "fill-orange-600",
  Earth: "fill-amber-500",
  Metal: "fill-slate-500",
  Water: "fill-blue-900",
};

const ALL_KNOWN_MERIDIANS = new Set(
  Object.values(ELEMENT_MERIDIANS).flat()
);

/** Extract meridian names from herb data (handles "All 12 Meridians, principally X, Y" etc.) */
function extractMeridians(meridians: string[] | undefined): string[] {
  if (!meridians?.length) return [];
  const out: string[] = [];
  for (const entry of meridians) {
    const parts = entry.split(/[,;]/).map((s) => s.replace(/^principally\s+/i, "").trim());
    for (const part of parts) {
      if (!part || /all\s*12\s*meridians/i.test(part)) continue;
      if (ALL_KNOWN_MERIDIANS.has(part)) {
        out.push(part);
      }
    }
  }
  return out;
}

const activeMeridians = computed(() => {
  const seen = new Set<string>();
  for (const herb of alchemyStore.activeFormula) {
    const list = extractMeridians(herb.properties?.meridians);
    for (const m of list) {
      seen.add(m);
    }
  }
  return Array.from(seen);
});

/** Meridians in activeFormula that belong to each element */
const meridiansByElement = computed(() => {
  const result: Record<string, string[]> = {};
  for (const elem of ELEMENT_ORDER) {
    const meridians = ELEMENT_MERIDIANS[elem] ?? [];
    result[elem] = meridians.filter((m) => activeMeridians.value.includes(m));
  }
  return result;
});

/** Is this element "lit up" (has any active meridians)? */
function isElementActive(element: string): boolean {
  const list = meridiansByElement.value[element];
  return (list?.length ?? 0) > 0;
}

/**
 * Pentagon geometry — derived from math, not guess-and-check.
 * Regular pentagon: center (50, 50), radius 38, top vertex at angle -90°.
 * Vertices: (cx + r·cos(θ), cy + r·sin(θ)) for θ = -90°, -18°, 54°, 126°, 198°.
 */
const VIEWBOX = 100;
const CENTER = VIEWBOX / 2;
const RADIUS = VIEWBOX * 0.38;
const PENTAGON_ELEMENTS = ["Fire", "Earth", "Metal", "Water", "Wood"] as const;
const START_ANGLE = -Math.PI / 2;
const ANGLE_STEP = (2 * Math.PI) / 5;

const PENTAGON_POSITIONS = PENTAGON_ELEMENTS.map((el, i) => {
  const angle = START_ANGLE + i * ANGLE_STEP;
  const x = CENTER + RADIUS * Math.cos(angle);
  const y = CENTER + RADIUS * Math.sin(angle);
  return { el, x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10 };
});

const PENTAGON_POINTS = PENTAGON_POSITIONS.map((p) => `${p.x},${p.y}`).join(" ");
</script>

<template>
  <div class="meridian-visualizer">
    <div class="w-64 h-64 mx-auto">
      <svg viewBox="-15 -15 130 130" class="w-full h-full text-white overflow-visible">
        <!-- Scale 1.3 to restore size after viewBox expansion (130/100); center at (50,50) -->
        <g transform="translate(50,50) scale(1.3) translate(-50,-50)">
          <!-- Pentagon outline: connecting lines -->
          <polygon
          :points="PENTAGON_POINTS"
          fill="none"
          stroke="currentColor"
          stroke-opacity="0.12"
          stroke-width="0.6"
          class="text-white/90"
        />

        <!-- Element nodes: <g> at each vertex with circle + label -->
        <g
          v-for="pos in PENTAGON_POSITIONS"
          :key="pos.el"
          :transform="`translate(${pos.x}, ${pos.y})`"
          class="transition-all duration-300"
          :class="[
            isElementActive(pos.el)
              ? 'opacity-100 drop-shadow-[0_0_8px_rgba(255,255,255,0.6)]'
              : 'opacity-40',
          ]"
        >
          <circle
            r="12"
            :class="ELEMENT_FILL[pos.el] ?? 'fill-slate-500'"
            stroke="rgba(255,255,255,0.3)"
            stroke-width="0.8"
          />
          <text
            text-anchor="middle"
            dominant-baseline="central"
            font-size="4"
            fill="white"
            font-weight="600"
            class="uppercase tracking-wider"
          >
            {{ pos.el }}
          </text>
          <title>{{ (meridiansByElement[pos.el] ?? []).join(", ") || "No meridians" }}</title>
        </g>
        </g>
      </svg>
    </div>

    <p
      v-if="activeMeridians.length === 0"
      class="text-daoist-subtle text-xs italic text-center mt-2"
    >
      No meridians targeted. Add herbs to see the network.
    </p>
  </div>
</template>
