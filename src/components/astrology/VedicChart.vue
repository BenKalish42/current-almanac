<script setup lang="ts">
import { computed, ref } from "vue";
import type { VedicChartSnapshot, VedicGrahaPlacement } from "@/utils/vedicMath";
import { VEDIC_RASI_SANSKRIT, VEDIC_RASI_EN } from "@/utils/vedicMath";

const props = defineProps<{
  chart: VedicChartSnapshot;
}>();

/** South Indian 4×4: fixed rāśi 0..11, clockwise from top-left. */
const SOUTH_PERIM: Array<{
  row: 1 | 2 | 3 | 4;
  col: 1 | 2 | 3 | 4;
  rasiIndex0: number;
  label: string;
}> = [
  { row: 1, col: 1, rasiIndex0: 0, label: "Ari" },
  { row: 1, col: 2, rasiIndex0: 1, label: "Tau" },
  { row: 1, col: 3, rasiIndex0: 2, label: "Gem" },
  { row: 1, col: 4, rasiIndex0: 3, label: "Can" },
  { row: 2, col: 4, rasiIndex0: 4, label: "Leo" },
  { row: 3, col: 4, rasiIndex0: 5, label: "Vir" },
  { row: 4, col: 4, rasiIndex0: 6, label: "Lib" },
  { row: 4, col: 3, rasiIndex0: 7, label: "Sco" },
  { row: 4, col: 2, rasiIndex0: 8, label: "Sag" },
  { row: 4, col: 1, rasiIndex0: 9, label: "Cap" },
  { row: 3, col: 1, rasiIndex0: 10, label: "Aqu" },
  { row: 2, col: 1, rasiIndex0: 11, label: "Pis" },
];

/**
 * North Indian: fixed *house* positions 1…12 (whole sign from Lagṇa; counterclockwise
 * from top, standard diamond-on-rectangle pattern).
 * Row/col are 1-based; center block r2-c2 to r3-c2 is void; r5-c2 is void between 6 & 5.
 */
const NORTH_HOUSES: Array<{
  row: 1 | 2 | 3 | 4 | 5;
  col: 1 | 2 | 3;
  house1to12: number;
  spanRow?: 2;
}> = [
  { row: 1, col: 1, house1to12: 12 },
  { row: 1, col: 2, house1to12: 1 },
  { row: 1, col: 3, house1to12: 2 },
  { row: 2, col: 1, house1to12: 11 },
  { row: 2, col: 2, house1to12: 0, spanRow: 2 },
  { row: 2, col: 3, house1to12: 3 },
  { row: 3, col: 1, house1to12: 10 },
  { row: 3, col: 3, house1to12: 4 },
  { row: 4, col: 1, house1to12: 9 },
  { row: 4, col: 2, house1to12: 8 },
  { row: 4, col: 3, house1to12: 7 },
  { row: 5, col: 1, house1to12: 6 },
  { row: 5, col: 2, house1to12: 0 },
  { row: 5, col: 3, house1to12: 5 },
];

const layout = ref<"south" | "north">("south");

const lagnaRasi0 = computed(() => {
  const L = props.chart.bodies.find((b) => b.id === "Lagna");
  return L?.rasi.index0 ?? 0;
});

const grahaByRasi = computed(() => {
  const map = new Map<number, VedicGrahaPlacement[]>();
  for (const p of props.chart.bodies) {
    const r = p.rasi.index0;
    const li = map.get(r) ?? [];
    li.push(p);
    map.set(r, li);
  }
  return map;
});

function abbrsInRasi(i: number): string {
  const g = grahaByRasi.value.get(i) ?? [];
  return g.map((x) => x.abbr).join(" ");
}

/** North: whole-sign house H → rāśi = Lagṇa + H − 1. */
function abbrsInHouse(house1to12: number): string {
  const rasi = (lagnaRasi0.value + house1to12 - 1 + 120) % 12;
  return abbrsInRasi(rasi);
}

function rasiShortSanskritForHouse(house1to12: number): string {
  const rasi = (lagnaRasi0.value + house1to12 - 1 + 120) % 12;
  const sa = VEDIC_RASI_SANSKRIT[rasi] ?? "—";
  return sa.length > 3 ? sa.slice(0, 3) : sa;
}
</script>

<template>
  <section
    class="vedic-chart rounded-xl border p-3 text-slate-100/95"
    style="border-color: var(--b2, #334155); background: var(--card-bg, rgba(15, 23, 42, 0.55))"
  >
    <header
      class="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-2"
    >
      <div
        class="inline-flex rounded-md border p-0.5 text-[0.65rem] font-medium uppercase"
        style="border-color: var(--b2, #334155)"
        role="group"
        aria-label="Vedic chart layout"
      >
        <button
          type="button"
          class="rounded px-2 py-1 transition-colors"
          :class="layout === 'south' ? 'bg-slate-600/80 text-white' : 'text-slate-400 hover:text-slate-200'"
          :aria-pressed="layout === 'south'"
          @click="layout = 'south'"
        >
          South Indian
        </button>
        <button
          type="button"
          class="rounded px-2 py-1 transition-colors"
          :class="layout === 'north' ? 'bg-slate-600/80 text-white' : 'text-slate-400 hover:text-slate-200'"
          :aria-pressed="layout === 'north'"
          @click="layout = 'north'"
        >
          North Indian
        </button>
      </div>
      <span class="font-mono text-[0.7rem] text-slate-400/90"
        >Lahiri ayaṅaṁśa: {{ chart.ayanamsa.degrees.toFixed(4) }}°</span
      >
    </header>

    <!-- South Indian: fixed rāśi; empty center 2×2 -->
    <div
      v-if="layout === 'south'"
      class="mx-auto grid aspect-square w-full max-w-sm auto-rows-fr grid-cols-4 gap-0.5 font-mono text-[0.6rem] leading-tight"
    >
      <template v-for="cell in SOUTH_PERIM" :key="`s-${cell.col}-${cell.row}`">
        <div
          class="border border-slate-600/70 bg-slate-900/50 p-1.5"
          :style="{
            gridRow: cell.row,
            gridColumn: cell.col,
          }"
        >
          <div class="text-[0.5rem] font-medium uppercase text-slate-500">{{ cell.label }}</div>
          <div class="mt-0.5 min-h-[0.9rem] text-amber-100/90">{{ abbrsInRasi(cell.rasiIndex0) }}</div>
        </div>
      </template>

      <div
        class="border border-dashed border-slate-500/50 bg-slate-950/40"
        style="grid-row: 2 / span 2; grid-column: 2 / span 2; border-radius: 0.2rem"
        aria-hidden="true"
      />
    </div>

    <!-- North Indian: fixed house numbers; rāśi = whole sign from Lagṇa -->
    <div
      v-else
      class="vedic-north-wrap mx-auto w-full max-w-sm font-mono text-[0.58rem] leading-tight"
    >
      <p class="mb-1.5 text-[0.6rem] text-slate-500/90">Houses 1…12 (whole sign) — H1 = Lagṇa rāśi ({{ VEDIC_RASI_EN[lagnaRasi0] }})</p>
      <div
        class="vedic-north grid aspect-[3/4] w-full grid-cols-3 grid-rows-5 gap-0.5"
      >
        <div
          v-for="c in NORTH_HOUSES"
          :key="`n-${c.col}-${c.row}-${c.house1to12}-${c.spanRow ?? 0}`"
          class="border border-slate-600/70 bg-slate-900/50 p-1"
          :class="{ 'vedic-north-void': c.house1to12 === 0 }"
          :style="{
            gridRow: c.spanRow ? `${c.row} / span ${c.spanRow}` : c.row,
            gridColumn: c.col,
            borderStyle: c.house1to12 === 0 ? 'dashed' : undefined,
          }"
        >
          <template v-if="c.house1to12 > 0">
            <div class="text-[0.5rem] font-medium text-slate-500">H{{ c.house1to12 }}</div>
            <div class="text-[0.5rem] text-slate-600">
              {{ rasiShortSanskritForHouse(c.house1to12) }} ·
              {{ VEDIC_RASI_EN[(lagnaRasi0 + c.house1to12 - 1 + 12) % 12] }}
            </div>
            <div class="min-h-[0.8rem] text-amber-100/90">
              {{ abbrsInHouse(c.house1to12) }}
            </div>
          </template>
        </div>
      </div>
    </div>

    <ul class="mt-3 list-none space-y-2 p-0 text-left text-sm text-slate-200/90">
      <li
        v-for="b in chart.bodies"
        :key="b.id"
        class="flex flex-wrap items-baseline gap-x-3 gap-y-0.5 border-b border-slate-600/30 pb-2"
        :class="{ 'text-amber-200/90': b.id === 'Moon' }"
      >
        <span class="w-7 shrink-0 font-mono text-xs text-slate-500">{{ b.abbr }}</span>
        <span class="min-w-0 flex-1"
          >{{ b.rasi.sanskrit }} <span class="text-slate-500">·</span> {{ b.rasi.en }}
          <span class="text-slate-500"> · </span> {{ b.degreeInRasi.toFixed(2) }}°</span
        >
        <span class="shrink-0 text-xs text-slate-400">
          {{ b.nakshatra.name }} · p{{ b.nakshatra.pada }}
          <span v-if="b.isRetrograde" class="ml-0.5 text-rose-300/80">R</span>
        </span>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.vedic-chart {
  --card-bg: rgba(15, 23, 42, 0.6);
}

.vedic-north-void {
  min-height: 0;
  background: rgba(2, 6, 23, 0.4);
  border-color: rgba(71, 85, 105, 0.4) !important;
}
</style>
