<script setup lang="ts">
import { formatGanZhiDisplay, getStemInfo } from "@/core/ganzhi";
import type { QimenChart, PalaceId } from "@/core/qimen";

const props = defineProps<{
  chart: QimenChart | null;
}>();

function palaceData(id: PalaceId) {
  return props.chart?.palaces[id] ?? null;
}

const STAR_MAP: Record<string, string> = {
  "蓬": "Tian Peng",
  "任": "Tian Ren",
  "冲": "Tian Chong",
  "辅": "Tian Fu",
  "英": "Tian Ying",
  "芮": "Tian Rui",
  "柱": "Tian Zhu",
  "心": "Tian Xin",
  "禽": "Tian Qin",
};

const DOOR_MAP: Record<string, string> = {
  "休": "Rest",
  "生": "Life",
  "伤": "Injury",
  "杜": "Delusion",
  "景": "View",
  "死": "Death",
  "惊": "Fear",
  "开": "Open",
};

const SPIRIT_MAP: Record<string, string> = {
  "值符": "Chief",
  "螣蛇": "Soaring Serpent",
  "太阴": "Great Yin",
  "六合": "Six Harmony",
  "勾陈": "Hooked Chen",
  "朱雀": "Vermilion Bird",
  "九地": "Nine Earth",
  "九天": "Nine Heaven",
  "白虎": "White Tiger",
  "玄武": "Black Tortoise",
};

function formatStemValue(stem: string | null) {
  if (!stem) return "—";
  const info = getStemInfo(stem);
  if (!info) return stem;
  return `${stem} ${info.element} ${info.yinYang}`;
}

function formatStarValue(star: string | null) {
  if (!star) return "—";
  const en = STAR_MAP[star];
  return en ? `${star} ${en}` : star;
}

function formatDoorValue(door: string | null) {
  if (!door) return "—";
  const en = DOOR_MAP[door];
  return en ? `${door} ${en}` : door;
}

function formatSpiritValue(spirit: string | null) {
  if (!spirit) return "—";
  const en = SPIRIT_MAP[spirit];
  return en ? `${spirit} ${en}` : spirit;
}
</script>

<template>
  <div v-if="chart" class="qmdj-board">
    <div class="qmdj-meta">
      <div class="meta-row">
        <span class="label">Method</span>
        <span class="value">Zhi Run (置润)</span>
      </div>
      <div class="meta-row">
        <span class="label">Scope</span>
        <span class="value">{{ chart.scope === "hour" ? "Hour chart" : "Day chart" }}</span>
      </div>
      <div class="meta-row">
        <span class="label">Local Time</span>
        <span class="value">{{ chart.solar.ymd }} {{ chart.solar.timeLabel }}</span>
      </div>
      <div class="meta-row">
        <span class="label">Qi Men Dun Jia</span>
        <span class="value">
          {{ chart.lunar.dun }} Dun • Ju {{ chart.lunar.ju }} • {{ chart.lunar.yuan }} Yuan
        </span>
      </div>
      <div class="meta-row">
        <span class="label">Day/Hour</span>
        <span class="value">
          {{ formatGanZhiDisplay(chart.lunar.dayGanZhi) }} • {{ formatGanZhiDisplay(chart.lunar.hourGanZhi) || "—" }}
        </span>
      </div>
    </div>

    <div class="qmdj-grid">
      <div v-for="(row, rIdx) in chart.grid" :key="`row-${rIdx}`" class="qmdj-row">
        <div
          v-for="palaceId in row"
          :key="`p-${palaceId}`"
          class="qmdj-cell"
        >
          <div class="cell-hdr">
            <span class="cell-id">#{{ palaceId }}</span>
            <span class="cell-name">{{ palaceData(palaceId)?.name }}</span>
            <span class="cell-dir">{{ palaceData(palaceId)?.direction }}</span>
          </div>
          <div class="cell-body">
            <div class="cell-line">Heaven: {{ formatStemValue(palaceData(palaceId)?.stemHeaven ?? null) }}</div>
            <div class="cell-line">Earth: {{ formatStemValue(palaceData(palaceId)?.stemEarth ?? null) }}</div>
            <div class="cell-line">Star: {{ formatStarValue(palaceData(palaceId)?.star ?? null) }}</div>
            <div class="cell-line">Door: {{ formatDoorValue(palaceData(palaceId)?.door ?? null) }}</div>
            <div class="cell-line">Spirit: {{ formatSpiritValue(palaceData(palaceId)?.spirit ?? null) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.qmdj-board {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qmdj-meta {
  display: grid;
  gap: 6px;
  font-size: 13px;
}

.meta-row {
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.label {
  color: var(--color-daoist-muted);
  min-width: 80px;
}

.value {
  color: var(--color-daoist-text);
}

.qmdj-grid {
  display: grid;
  gap: 8px;
}

.qmdj-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.qmdj-cell {
  border: 1px solid rgb(51 65 85 / 0.6);
  border-radius: 10px;
  padding: 8px;
  background: rgb(15 23 42 / 0.8);
  min-height: 120px;
  transition: border-color 0.2s, background-color 0.2s;
}

.qmdj-cell:hover {
  border-color: rgb(71 85 105 / 0.8);
  background: rgb(15 23 42 / 0.95);
}

.cell-hdr {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 12px;
  color: var(--color-daoist-muted);
  margin-bottom: 6px;
}

.cell-id {
  color: var(--color-daoist-text);
  font-weight: 600;
}

.cell-name {
  color: rgb(203 213 225);
}

.cell-dir {
  margin-left: auto;
  color: rgb(100 116 139);
}

.cell-body {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: var(--color-daoist-text);
}

.cell-line {
  display: flex;
  justify-content: space-between;
}
</style>
