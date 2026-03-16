<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "@/stores/appStore";
import { getCurrentOrganHour } from "@/data/organClock";
import type { OrganHourEntry, WuXingElement } from "@/data/organClock";

const store = useAppStore();

/** Current hour (0–23) from store's dateISO + timeHHMM */
const currentHour24 = computed(() => {
  const [, t] = (store.presentDatetimeLocal || "").split("T");
  if (!t) return new Date().getHours();
  const [h] = t.split(":").map(Number);
  return Number.isFinite(h) ? h : new Date().getHours();
});

const activeOrgan = computed<OrganHourEntry>(() =>
  getCurrentOrganHour(currentHour24.value ?? new Date().getHours())
);

function formatTimeBlock(entry: OrganHourEntry): string {
  const fmt = (h: number) => String(h).padStart(2, "0") + ":00";
  const e = entry.endHour < entry.startHour ? entry.endHour + 24 : entry.endHour;
  return `${fmt(entry.startHour)} – ${fmt(e === 24 ? 0 : entry.endHour)}`;
}

const wuXingClasses: Record<WuXingElement, string> = {
  Wood: "from-emerald-950/60 to-emerald-900/40 border-emerald-500/30",
  Fire: "from-orange-950/60 to-red-900/40 border-orange-500/30",
  Earth: "from-amber-950/60 to-amber-900/40 border-amber-500/30",
  Metal: "from-slate-800/60 to-slate-700/40 border-slate-400/30",
  Water: "from-blue-950/60 to-indigo-900/40 border-blue-500/30",
};
</script>

<template>
  <div
    class="organ-hour-card rounded-xl border bg-gradient-to-br p-4 shadow-lg transition-all duration-300"
    :class="wuXingClasses[activeOrgan.wuXing] ?? 'from-slate-800/60 to-slate-700/40 border-slate-400/30'"
  >
    <div class="organ-hour-header mb-4 flex flex-col gap-3">
      <div>
        <div class="mb-0.5 text-[10px] font-medium uppercase tracking-[0.15em] text-white/50">
          Earthly Branch (Time)
        </div>
        <div class="flex flex-wrap items-baseline gap-2">
          <span class="font-mono text-2xl text-white/90" aria-hidden="true">
            {{ activeOrgan.branchCn }}
          </span>
          <span class="text-sm font-medium uppercase tracking-wider text-white/70">
            {{ activeOrgan.branch }}
          </span>
          <span class="text-sm text-white/60">
            {{ formatTimeBlock(activeOrgan) }}
          </span>
        </div>
      </div>
      <div>
        <div class="mb-0.5 text-[10px] font-medium uppercase tracking-[0.15em] text-white/50">
          Active Meridian
        </div>
        <h3 class="text-lg font-semibold text-white">
          {{ activeOrgan.organ }}
          <span class="ml-1.5 font-normal text-white/80">{{ activeOrgan.organHanzi }} {{ activeOrgan.organPinyin }}</span>
        </h3>
      </div>
    </div>
    <div class="organ-hour-body grid gap-4 sm:grid-cols-2">
      <section>
        <h4 class="mb-1 text-xs font-medium uppercase tracking-wider text-white/60">
          Physiological State
        </h4>
        <p class="text-sm leading-relaxed text-white/90">
          {{ activeOrgan.physiological }}
        </p>
      </section>
      <section>
        <h4 class="mb-1 text-xs font-medium uppercase tracking-wider text-white/60">
          Neidan / {{ activeOrgan.spiritName.toUpperCase() }}
        </h4>
        <p class="text-sm leading-relaxed text-white/90">
          {{ activeOrgan.neidanSpirit }}
        </p>
      </section>
    </div>
  </div>
</template>
