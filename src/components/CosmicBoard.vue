<script setup lang="ts">
import { ref, computed } from "vue";
import QMDJBoard from "@/components/QMDJBoard.vue";
import DaLiuRenBoard from "@/components/DaLiuRenBoard.vue";
import TaiYiBoard from "@/components/TaiYiBoard.vue";
import type { QimenChart } from "@/core/qimen";
import type { SanShiSystem, WeatherBadge } from "@/types/astrology";

const props = withDefaults(
  defineProps<{
    qimenChartHour: QimenChart | null;
    qimenChartDay: QimenChart | null;
    selectedDate: Date;
    weatherBadges?: WeatherBadge[];
    zhuangSynthesis?: string;
  }>(),
  {
    weatherBadges: () => [
      { id: "1", type: "auspicious", label: "Heavenly Nobleman Hour", description: "Auspicious timing for noble pursuits" },
      { id: "2", type: "inauspicious", label: "Void Emptiness", description: "Caution advised in this sector" },
      { id: "3", type: "neutral", label: "Six Harmony", description: "Balanced energy prevails" },
    ],
    zhuangSynthesis: () => "",
  }
);

const currentSystem = ref<SanShiSystem>("qmdj");
const qimenScope = ref<"hour" | "day">("hour");
const qimenChart = computed(() =>
  qimenScope.value === "hour" ? props.qimenChartHour : props.qimenChartDay
);

const pillOptions: { value: SanShiSystem; label: string }[] = [
  { value: "taiyi", label: "Tai Yi" },
  { value: "qmdj", label: "Qi Men" },
  { value: "daliuren", label: "Liu Ren" },
];

const BoardComponent = computed(() => {
  switch (currentSystem.value) {
    case "qmdj":
      return QMDJBoard;
    case "daliuren":
      return DaLiuRenBoard;
    case "taiyi":
      return TaiYiBoard;
    default:
      return QMDJBoard;
  }
});

const boardProps = computed(() => {
  if (currentSystem.value === "qmdj") {
    return { chart: qimenChart.value };
  }
  return { date: props.selectedDate };
});
</script>

<template>
  <div class="cosmic-board">
    <!-- Pill-shaped toggle -->
    <div class="system-toggle" role="tablist" aria-label="San Shi system selector">
      <button
        v-for="opt in pillOptions"
        :key="opt.value"
        type="button"
        role="tab"
        :aria-selected="currentSystem === opt.value"
        class="pill-btn"
        :class="{ active: currentSystem === opt.value }"
        @click="currentSystem = opt.value"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- Current Weather Banner (horizontally scrollable chips) -->
    <div class="weather-banner-wrap">
      <div class="weather-banner">
        <button
          v-for="badge in weatherBadges"
          :key="badge.id"
          type="button"
          class="weather-chip"
          :class="badge.type"
          :title="badge.description"
        >
          <span class="chip-label">{{ badge.label }}</span>
        </button>
      </div>
    </div>

    <!-- Dynamic Board Area -->
    <div class="board-area" :key="currentSystem">
      <div v-if="currentSystem === 'qmdj'" class="qimen-scope-row">
        <button
          type="button"
          class="scope-btn"
          :class="{ active: qimenScope === 'hour' }"
          @click="qimenScope = 'hour'"
        >
          Hour Chart
        </button>
        <button
          type="button"
          class="scope-btn"
          :class="{ active: qimenScope === 'day' }"
          @click="qimenScope = 'day'"
        >
          Day Chart
        </button>
      </div>
      <Transition name="board-fade" mode="out-in">
        <component
          :is="BoardComponent"
          v-bind="boardProps"
        />
      </Transition>
    </div>

    <!-- Zhuang Synthesis Card -->
    <div class="zhuang-card">
      <h3 class="zhuang-title">Zhuang&apos;s Synthesis</h3>
      <div class="zhuang-content">
        <p v-if="zhuangSynthesis" class="zhuang-text">
          {{ zhuangSynthesis }}
        </p>
        <p v-else class="zhuang-placeholder">
          Three-sentence interpretation of the active board will appear here from Zhuang.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cosmic-board {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.system-toggle {
  display: inline-flex;
  padding: 4px;
  border-radius: 9999px;
  background: rgb(15 23 42 / 0.8);
  border: 1px solid rgb(51 65 85 / 0.5);
  width: fit-content;
  transition: border-color 0.2s;
}

.system-toggle:hover {
  border-color: rgb(71 85 105 / 0.6);
}

.pill-btn {
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-daoist-muted);
  background: transparent;
  border: none;
  border-radius: 9999px;
  cursor: pointer;
  transition: color 0.2s, background-color 0.2s;
}

.pill-btn:hover {
  color: var(--color-daoist-text);
}

.pill-btn.active {
  color: var(--color-daoist-text);
  background: rgb(51 65 85 / 0.6);
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.2);
}

.weather-banner-wrap {
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
}

.weather-banner-wrap::-webkit-scrollbar {
  height: 4px;
}

.weather-banner-wrap::-webkit-scrollbar-track {
  background: rgb(15 23 42 / 0.5);
  border-radius: 2px;
}

.weather-banner-wrap::-webkit-scrollbar-thumb {
  background: rgb(71 85 105 / 0.5);
  border-radius: 2px;
}

.weather-banner {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  min-width: min-content;
}

.weather-chip {
  flex-shrink: 0;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 9999px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: transform 0.15s, border-color 0.2s;
  white-space: nowrap;
}

.weather-chip:hover {
  transform: translateY(-1px);
}

.weather-chip.auspicious {
  background: rgb(16 185 129 / 0.2);
  color: rgb(110 231 183);
  border-color: rgb(16 185 129 / 0.4);
}

.weather-chip.inauspicious {
  background: rgb(244 63 94 / 0.2);
  color: rgb(251 113 133);
  border-color: rgb(244 63 94 / 0.4);
}

.weather-chip.neutral {
  background: rgb(245 158 11 / 0.15);
  color: rgb(251 191 36);
  border-color: rgb(245 158 11 / 0.4);
}

.board-area {
  min-height: 200px;
  transition: opacity 0.2s;
}

.qimen-scope-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.scope-btn {
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-daoist-muted);
  background: transparent;
  border: 1px solid rgb(51 65 85 / 0.5);
  border-radius: 8px;
  cursor: pointer;
  transition: color 0.2s, background-color 0.2s, border-color 0.2s;
}

.scope-btn:hover {
  color: var(--color-daoist-text);
  border-color: rgb(71 85 105 / 0.6);
}

.scope-btn.active {
  color: var(--color-daoist-text);
  background: rgb(51 65 85 / 0.6);
  border-color: rgb(71 85 105 / 0.6);
}

.board-fade-enter-active,
.board-fade-leave-active {
  transition: opacity 0.2s ease;
}

.board-fade-enter-from,
.board-fade-leave-to {
  opacity: 0;
}

.zhuang-card {
  border: 1px solid rgb(51 65 85 / 0.5);
  border-radius: 12px;
  padding: 18px;
  background: rgb(15 23 42 / 0.4);
  backdrop-filter: blur(4px);
}

.zhuang-title {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--color-daoist-muted);
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid rgb(51 65 85 / 0.4);
}

.zhuang-content {
  font-size: 14px;
  line-height: 1.55;
}

.zhuang-text {
  color: var(--color-daoist-text);
  margin: 0;
}

.zhuang-placeholder {
  color: var(--color-daoist-muted);
  margin: 0;
  font-style: italic;
}
</style>
