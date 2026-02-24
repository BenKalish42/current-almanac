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
  <div v-if="chart" class="qimen">
    <div class="qimenMeta">
      <div class="metaRow">
        <span class="label">Method</span>
        <span class="value">Zhi Run (置润)</span>
      </div>
      <div class="metaRow">
        <span class="label">Scope</span>
        <span class="value">{{ chart.scope === "hour" ? "Hour chart" : "Day chart" }}</span>
      </div>
      <div class="metaRow">
        <span class="label">Local Time</span>
        <span class="value">{{ chart.solar.ymd }} {{ chart.solar.timeLabel }}</span>
      </div>
      <div class="metaRow">
        <span class="label">Qi Men Dun Jia</span>
        <span class="value">
          {{ chart.lunar.dun }} Dun • Ju {{ chart.lunar.ju }} • {{ chart.lunar.yuan }} Yuan
        </span>
      </div>
      <div class="metaRow">
        <span class="label">JieQi</span>
        <span class="value">{{ chart.lunar.jieQi }}</span>
      </div>
      <div class="metaRow">
        <span class="label">Fu Tou</span>
        <span class="value">{{ formatGanZhiDisplay(chart.zhiRun.fuTouGanZhi) }} · {{ chart.zhiRun.fuTouDay }}</span>
      </div>
      <div class="metaRow">
        <span class="label">Term Start</span>
        <span class="value">{{ chart.zhiRun.termStart }}</span>
      </div>
      <div class="metaRow">
        <span class="label">Alignment</span>
        <span class="value">{{ chart.zhiRun.termStatus }}</span>
      </div>
      <div class="metaRow">
        <span class="label">Intercalary</span>
        <span class="value">{{ chart.zhiRun.intercalary ? "Yes" : "No" }}</span>
      </div>
      <div class="metaRow">
        <span class="label">Day/Hour</span>
        <span class="value">
          {{ formatGanZhiDisplay(chart.lunar.dayGanZhi) }} • {{ formatGanZhiDisplay(chart.lunar.hourGanZhi) || "—" }}
        </span>
      </div>
    </div>

    <div class="qimenGrid">
      <div v-for="(row, rIdx) in chart.grid" :key="`row-${rIdx}`" class="qimenRow">
        <div
          v-for="palaceId in row"
          :key="`p-${palaceId}`"
          class="qimenCell"
        >
          <div class="cellHdr">
            <span class="cellId">#{{ palaceId }}</span>
            <span class="cellName">{{ palaceData(palaceId)?.name }}</span>
            <span class="cellDir">{{ palaceData(palaceId)?.direction }}</span>
          </div>
          <div class="cellBody">
            <div class="cellLine">Heaven: {{ formatStemValue(palaceData(palaceId)?.stemHeaven ?? null) }}</div>
            <div class="cellLine">Earth: {{ formatStemValue(palaceData(palaceId)?.stemEarth ?? null) }}</div>
            <div class="cellLine">Star: {{ formatStarValue(palaceData(palaceId)?.star ?? null) }}</div>
            <div class="cellLine">Door: {{ formatDoorValue(palaceData(palaceId)?.door ?? null) }}</div>
            <div class="cellLine">Spirit: {{ formatSpiritValue(palaceData(palaceId)?.spirit ?? null) }}</div>
          </div>
        </div>
      </div>
    </div>

    <details class="qimenDebug">
      <summary>Debug chart data</summary>
      <pre>{{ JSON.stringify(chart, null, 2) }}</pre>
    </details>
  </div>
</template>

<style scoped>
.qimen {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qimenMeta {
  display: grid;
  gap: 6px;
  font-size: 13px;
}

.metaRow {
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.label {
  color: #94a3b8;
  min-width: 80px;
}

.value {
  color: #e2e8f0;
}

.qimenGrid {
  display: grid;
  gap: 8px;
}

.qimenRow {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.qimenCell {
  border: 1px solid #1f2937;
  border-radius: 10px;
  padding: 8px;
  background: #0b1220;
  min-height: 120px;
}

.cellHdr {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 6px;
}

.cellId {
  color: #e2e8f0;
  font-weight: 600;
}

.cellName {
  color: #cbd5f5;
}

.cellDir {
  margin-left: auto;
  color: #64748b;
}

.cellBody {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: #e2e8f0;
}

.cellLine {
  display: flex;
  justify-content: space-between;
}

.qimenDebug {
  color: #9ca3af;
}

.qimenDebug pre {
  font-size: 11px;
  background: #0b1220;
  border-radius: 10px;
  padding: 8px;
  overflow: auto;
  max-height: 320px;
}
</style>
