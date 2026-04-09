<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "@/stores/appStore";
import { getCurrentOrganHour } from "@/data/organClock";
import { getShichenDetail } from "@/core/shichenDetail";
import type { OrganHourEntry, WuXingElement } from "@/data/organClock";

const store = useAppStore();

/** Moment for organ + Chu/Zheng/Ke (True Solar when enabled and longitude set) */
const effectivePresentDate = computed(() => {
  if (store.useTrueSolarTime && store.longitude != null) {
    return store.solarAdjustedSelectedDate;
  }
  return store.selectedDate;
});

const activeOrgan = computed<OrganHourEntry>(() =>
  getCurrentOrganHour(effectivePresentDate.value.getHours())
);

const shichenDetail = computed(() => getShichenDetail(effectivePresentDate.value));

function formatTimeBlock(entry: OrganHourEntry): string {
  const fmt = (h: number) => String(h).padStart(2, "0") + ":00";
  const e = entry.endHour < entry.startHour ? entry.endHour + 24 : entry.endHour;
  return `${fmt(entry.startHour)} – ${fmt(e === 24 ? 0 : entry.endHour)}`;
}

/** Blue-forward shell; Wu Xing read via border tint (matches home wave / daoist UI). */
const wuXingClasses: Record<WuXingElement, string> = {
  Wood: "from-slate-950/80 via-cyan-950/45 to-blue-950/55 border-cyan-500/25",
  Fire: "from-slate-950/80 via-blue-950/50 to-indigo-950/55 border-sky-400/35",
  Earth: "from-slate-950/80 via-blue-950/40 to-slate-900/50 border-amber-500/20",
  Metal: "from-slate-950/85 via-slate-900/55 to-blue-950/40 border-slate-400/28",
  Water: "from-blue-950/70 via-indigo-950/50 to-slate-950/60 border-blue-400/35",
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
        <div class="mt-2 text-xs leading-relaxed text-white/75">
          <div class="mb-0.5 text-[10px] font-medium uppercase tracking-[0.15em] text-white/45">
            Chu / Zheng / Ke (初正刻)
          </div>
          <div class="font-mono text-sm text-white/90">{{ shichenDetail.fullLabel }}</div>
          <div class="text-white/65">{{ shichenDetail.fullLabelEn }}</div>
          <div class="mt-0.5 text-white/55">{{ shichenDetail.keBoundsDisplay }} local</div>
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
