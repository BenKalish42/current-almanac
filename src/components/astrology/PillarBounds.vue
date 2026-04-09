<script setup lang="ts">
import { computed } from "vue";
import {
  getHourPillarBounds,
  getKeBounds,
  getYearPillarBounds,
  getMonthPillarBounds,
  getDayPillarBounds,
  getBaZiYear,
  type PillarBoundsResult,
} from "@/utils/pillarBounds";
import type { TemporalXkdgPillar } from "@/core/hexagramsXKDG";

const props = defineProps<{
  pillarType: "year" | "month" | "day" | "hour";
  pillar: TemporalXkdgPillar;
  referenceDate: Date;
  useTrueSolarTime: boolean;
  dateFormat?: "US" | "EU" | "ASIAN";
}>();

const bounds = computed<PillarBoundsResult | null>(() => {
  const { pillarType, pillar, referenceDate, useTrueSolarTime, dateFormat = "US" } = props;
  const branchChar = pillar.ganzhi?.[1] ?? "";

  switch (pillarType) {
    case "year":
      return getYearPillarBounds(getBaZiYear(referenceDate), dateFormat);
    case "month":
      return getMonthPillarBounds(referenceDate, dateFormat);
    case "day":
      return getDayPillarBounds(referenceDate, dateFormat);
    case "hour":
      return getHourPillarBounds(branchChar, referenceDate, useTrueSolarTime);
    default:
      return null;
  }
});

const keBounds = computed<PillarBoundsResult | null>(() => {
  if (props.pillarType !== "hour") return null;
  return getKeBounds(props.referenceDate, props.useTrueSolarTime);
});
</script>

<template>
  <div v-if="bounds" class="pillar-bounds">
    <span class="pillar-bounds-label">Bounds:</span>
    <span class="pillar-bounds-range">{{ bounds.start }} – {{ bounds.end }}</span>
    <span v-if="bounds.label" class="pillar-bounds-hint">({{ bounds.label }})</span>
  </div>
  <div v-if="keBounds" class="pillar-bounds pillar-bounds-ke">
    <span class="pillar-bounds-label">Ke:</span>
    <span class="pillar-bounds-range">{{ keBounds.start }} – {{ keBounds.end }}</span>
    <span v-if="keBounds.label" class="pillar-bounds-hint">({{ keBounds.label }})</span>
  </div>
</template>

<style scoped>
.pillar-bounds {
  font-size: 10px;
  color: var(--muted, rgba(255, 255, 255, 0.55));
  margin-top: 4px;
  line-height: 1.3;
}
.pillar-bounds-label {
  font-weight: 500;
}
.pillar-bounds-range {
  margin-left: 4px;
}
.pillar-bounds-hint {
  margin-left: 4px;
  font-style: italic;
}
</style>
