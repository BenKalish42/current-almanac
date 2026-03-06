<script setup lang="ts">
import { computed } from "vue";
import { computeDaLiuRen } from "@/core/daliuren";
import type { DaLiuRenData } from "@/types/astrology";

const props = defineProps<{
  date: Date;
}>();

const daliurenData = computed<DaLiuRenData | null>(() => {
  try {
    const result = computeDaLiuRen(props.date);
    const BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
    const siKeStrings = result.siKe.map(
      (s) => `${s.upper} / ${s.lower}`
    );
    const sanChuanStrings = [result.sanChuan.chu, result.sanChuan.zhong, result.sanChuan.mo].filter(Boolean);
    const earthBoard: DaLiuRenData["earthBoard"] = BRANCHES.map((branch, i) => ({
      branch,
      heavenPan: result.heavenPan[branch] ?? "—",
      index: i + 1,
    }));
    return {
      siKe: siKeStrings,
      sanChuan: sanChuanStrings,
      earthBoard,
    };
  } catch {
    return null;
  }
});

/** 4x4 grid indices; inner 4 (6,7,10,11) are hollow */
function isHollow(idx: number): boolean {
  return [6, 7, 10, 11].includes(idx);
}

/** Peripheral cells in clockwise order: top row, right col, bottom row, left col */
const PERIPHERAL_GRID_INDICES = [0, 1, 2, 3, 7, 11, 15, 14, 13, 12, 8, 4];

function getEarthCell(gridIdx: number): { branch: string; heavenPan: string } | null {
  if (!daliurenData.value) return null;
  const boardIdx = PERIPHERAL_GRID_INDICES.indexOf(gridIdx);
  if (boardIdx < 0) return null;
  const cell = daliurenData.value.earthBoard[boardIdx];
  return cell ? { branch: cell.branch, heavenPan: cell.heavenPan } : null;
}
</script>

<template>
  <div v-if="daliurenData" class="daliuren-board">
    <!-- Header: Si Ke (4 domino cards) + San Chuan (3 vertical badges) -->
    <div class="header-section">
      <div class="si-ke-row">
        <div
          v-for="(ke, i) in daliurenData.siKe"
          :key="`sike-${i}`"
          class="si-ke-card"
        >
          <span class="si-ke-label">{{ ["Heaven", "Earth", "Zei", "Hour"][i] ?? "—" }}</span>
          <span class="si-ke-value">{{ ke }}</span>
        </div>
      </div>
      <div class="san-chuan-row">
        <div
          v-for="(chuan, i) in daliurenData.sanChuan"
          :key="`chuan-${i}`"
          class="san-chuan-badge"
        >
          <span class="chuan-label">{{ ["初", "中", "末"][i] ?? "—" }}</span>
          <span class="chuan-value">{{ chuan }}</span>
        </div>
      </div>
    </div>

    <!-- 4x4 grid with hollow center -->
    <div class="earth-grid">
      <template v-for="idx in 16" :key="idx">
        <div
          v-if="isHollow(idx - 1)"
          class="earth-cell hollow"
        >
          <div class="yin-yang-placeholder">
            <svg viewBox="0 0 24 24" class="yin-yang-svg" aria-hidden="true">
              <circle cx="12" cy="12" r="11" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4" />
              <path d="M12 1a11 11 0 0 1 0 22 5.5 5.5 0 0 0 0-11 5.5 5.5 0 0 1 0-11z" fill="currentColor" opacity="0.3" />
              <circle cx="12" cy="6.5" r="1.5" fill="currentColor" opacity="0.5" />
              <circle cx="12" cy="17.5" r="1.5" fill="none" stroke="currentColor" stroke-width="1" opacity="0.5" />
            </svg>
          </div>
        </div>
        <div
          v-else
          class="earth-cell"
        >
          <div class="earth-cell-inner">
            <span class="heaven-pan">{{ getEarthCell(idx - 1)?.heavenPan ?? "—" }}</span>
            <span class="branch">{{ getEarthCell(idx - 1)?.branch ?? "—" }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.daliuren-board {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.si-ke-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.si-ke-card {
  padding: 10px 12px;
  border: 1px solid rgb(51 65 85 / 0.6);
  border-radius: 8px;
  background: rgb(15 23 42 / 0.8);
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: border-color 0.2s;
}

.si-ke-card:hover {
  border-color: rgb(71 85 105 / 0.8);
}

.si-ke-label {
  font-size: 10px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-daoist-muted);
}

.si-ke-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-daoist-text);
  font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif;
}

.san-chuan-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.san-chuan-badge {
  padding: 8px 14px;
  border: 1px solid rgb(51 65 85 / 0.6);
  border-radius: 8px;
  background: rgb(26 36 53 / 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 56px;
}

.chuan-label {
  font-size: 11px;
  color: var(--color-daoist-muted);
}

.chuan-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-daoist-text);
  font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif;
}

.earth-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-template-rows: repeat(4, minmax(0, 1fr));
  gap: 6px;
  aspect-ratio: 1;
  max-width: 400px;
  margin: 0 auto;
}

.earth-cell {
  border: 1px solid rgb(51 65 85 / 0.6);
  border-radius: 8px;
  background: rgb(15 23 42 / 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
  transition: border-color 0.2s, background-color 0.2s;
}

.earth-cell:hover {
  border-color: rgb(71 85 105 / 0.8);
  background: rgb(15 23 42 / 0.95);
}

.earth-cell.hollow {
  background: rgb(15 23 42 / 0.4);
  border-style: dashed;
}

.earth-cell-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
}

.heaven-pan {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-daoist-text);
  font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif;
}

.branch {
  font-size: 12px;
  color: var(--color-daoist-muted);
}

.yin-yang-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--color-daoist-muted);
  opacity: 0.5;
}

.yin-yang-svg {
  width: 32px;
  height: 32px;
}
</style>
