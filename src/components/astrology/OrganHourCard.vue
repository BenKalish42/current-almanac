<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { useAppStore } from "@/stores/appStore";
import { getCurrentOrganHour } from "@/data/organClock";
import { getShichenDetail } from "@/core/shichenDetail";
import type { OrganHourEntry, WuXingElement } from "@/data/organClock";
import { getTrueSolarTime } from "@/utils/solarTime";
import OrganKeHourglass from "@/components/astrology/OrganKeHourglass.vue";

const store = useAppStore();

/** Live clock for Ke progress when viewing “present”; frozen when user sets a fixed moment. */
const tickNow = ref(Date.now());
let tickId: number | null = null;

function startPresentTick() {
  tickNow.value = Date.now();
  if (tickId != null) return;
  tickId = window.setInterval(() => {
    tickNow.value = Date.now();
  }, 500);
}

function stopPresentTick() {
  if (tickId != null) {
    clearInterval(tickId);
    tickId = null;
  }
}

watch(
  () => store.presentAuto,
  (auto) => {
    if (auto) startPresentTick();
    else stopPresentTick();
  },
  { immediate: true }
);

onUnmounted(() => stopPresentTick());

/** Moment for organ + Chu/Zheng/Ke (True Solar when enabled and longitude set) */
const effectivePresentDate = computed(() => {
  if (store.useTrueSolarTime && store.longitude != null) {
    return store.solarAdjustedSelectedDate;
  }
  return store.selectedDate;
});

/** Moment for the card: live when presentAuto (with TST when enabled), else the selected/solar moment. */
const displayMoment = computed(() => {
  if (!store.presentAuto) return effectivePresentDate.value;
  const live = new Date(tickNow.value);
  if (store.useTrueSolarTime && store.longitude != null) {
    return getTrueSolarTime(live, store.longitude);
  }
  return live;
});

const activeOrgan = computed<OrganHourEntry>(() =>
  getCurrentOrganHour(displayMoment.value.getHours())
);

const shichenDetail = computed(() => getShichenDetail(displayMoment.value));

/** 0 → start of current Ke, 1 → end (15-minute segment). */
const keProgress = computed(() => {
  const d = shichenDetail.value;
  const start = d.keStartDate.getTime();
  const end = d.keEndDate.getTime();
  const now = displayMoment.value.getTime();
  if (end <= start) return 0;
  return Math.max(0, Math.min(1, (now - start) / (end - start)));
});

function formatTimeBlock(entry: OrganHourEntry): string {
  const fmt = (h: number) => String(h).padStart(2, "0") + ":00";
  const e = entry.endHour < entry.startHour ? entry.endHour + 24 : entry.endHour;
  return `${fmt(entry.startHour)} – ${fmt(e === 24 ? 0 : entry.endHour)}`;
}

/** Blue-forward shell; Wu Xing read via border tint (matches home wave / daoist UI). */
const wuXingClasses: Record<WuXingElement, string> = {
  Wood: "from-slate-950/80 via-cyan-950/45 to-blue-950/55 border-cyan-200/30",
  Fire: "from-slate-950/80 via-blue-950/50 to-indigo-950/55 border-sky-200/35",
  Earth: "from-slate-950/80 via-blue-950/40 to-slate-900/50 border-[#ebe4d6]/60",
  Metal: "from-slate-950/85 via-slate-900/55 to-blue-950/40 border-[#e8e4de]/55",
  Water: "from-blue-950/70 via-indigo-950/50 to-slate-950/60 border-slate-200/35",
};
</script>

<template>
  <div
    class="organ-hour-card rounded-xl border bg-gradient-to-br p-4 shadow-lg transition-all duration-300"
    :class="wuXingClasses[activeOrgan.wuXing] ?? 'from-slate-800/60 to-slate-700/40 border-[#e2ddd4]/45'"
  >
    <div class="organ-hour-header mb-4 flex flex-col gap-4">
      <!-- Meridian (left) / Earthly branch (right); labels share one line -->
      <div class="flex flex-col gap-3 border-b border-white/10 pb-4">
        <div
          class="flex min-h-[1rem] items-baseline justify-between gap-3 text-[10px] font-medium uppercase tracking-[0.15em] text-white/50"
        >
          <span class="min-w-0 shrink">Active meridian</span>
          <span class="min-w-0 shrink text-right">Earthly branch · shichen</span>
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:items-start sm:gap-6">
          <div class="min-w-0">
            <div class="text-xl font-semibold leading-tight text-white">{{ activeOrgan.organ }}</div>
            <div class="mt-0.5 text-sm text-white/75">
              <span class="font-mono text-white/90">{{ activeOrgan.organHanzi }}</span>
              <span class="text-white/50"> · </span>
              <span class="text-white/80">{{ activeOrgan.organPinyin }}</span>
            </div>
          </div>
          <div class="min-w-0 sm:text-right">
            <div class="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 sm:justify-end">
              <span class="font-mono text-3xl leading-none text-white/95">{{ activeOrgan.branchCn }}</span>
              <span class="text-base font-semibold tracking-wide text-white/85">{{ activeOrgan.branch }}</span>
            </div>
            <div class="mt-1 font-mono text-sm text-white/55 sm:text-right">{{ formatTimeBlock(activeOrgan) }}</div>
          </div>
        </div>
      </div>

      <!-- Chu / Zheng / Ke + Lottie hourglass (15-minute Ke progress) -->
      <div class="flex flex-col gap-3 sm:flex-row sm:items-stretch sm:gap-4">
        <div class="flex shrink-0 items-center justify-center sm:justify-start">
          <OrganKeHourglass
            :progress="keProgress"
            :ke-in-shichen="shichenDetail.keInShichen"
          />
        </div>

        <div class="min-w-0 flex-1">
          <div class="mb-1 text-[10px] font-medium uppercase tracking-[0.15em] text-white/45">
            Chu / zheng / ke (初正刻)
          </div>
          <div class="font-mono text-base text-white/95">{{ shichenDetail.fullLabel }}</div>
          <div class="mt-0.5 text-sm text-white/70">{{ shichenDetail.fullLabelEn }}</div>
          <div class="mt-1 font-mono text-xs text-white/50">
            {{ shichenDetail.keBoundsDisplay }}
            <span class="text-white/40">· local</span>
          </div>
        </div>
      </div>
    </div>

    <div class="organ-hour-body grid gap-5 sm:grid-cols-2">
      <section>
        <h4 class="mb-1.5 text-xs font-medium uppercase tracking-wider text-white/60">
          Physical body
        </h4>
        <p class="text-sm leading-relaxed text-white/90">
          {{ activeOrgan.physiological }}
        </p>
      </section>
      <section>
        <h4 class="mb-1.5 text-xs font-medium uppercase tracking-wider text-white/60">
          Energetic spirit
          <span class="font-normal normal-case tracking-normal text-white/45">
            ({{ activeOrgan.spiritName }})
          </span>
        </h4>
        <p class="text-sm leading-relaxed text-white/90">
          {{ activeOrgan.neidanSpirit }}
        </p>
      </section>
    </div>
  </div>
</template>
