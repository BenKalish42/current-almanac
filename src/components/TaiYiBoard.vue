<script setup lang="ts">
import { computed } from "vue";
import { computeTaiYi } from "@/core/taiyi";

const props = defineProps<{
  date: Date;
}>();

const taiYiResult = computed(() => {
  try {
    return computeTaiYi(props.date);
  } catch {
    return null;
  }
});
</script>

<template>
  <div class="taiyi-board">
    <div class="taiyi-placeholder">
      <div class="taiyi-card">
        <h3 class="taiyi-title">Tai Yi Shen Shu (太乙神数)</h3>
        <div v-if="taiYiResult" class="taiyi-metrics">
          <div class="metric-row primary">
            <span class="metric-label">Accumulation Year</span>
            <span class="metric-value">{{ taiYiResult.accumulationYear.toLocaleString() }}</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Configuration</span>
            <span class="metric-value">{{ taiYiResult.configurationNumber }}</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Palace</span>
            <span class="metric-value">{{ taiYiResult.palaceNumber }} ({{ taiYiResult.dun }})</span>
          </div>
        </div>
        <div v-else class="taiyi-empty">
          Unable to compute Tai Yi for this moment.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.taiyi-board {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 280px;
}

.taiyi-placeholder {
  width: 100%;
  max-width: 480px;
}

.taiyi-card {
  border: 1px solid rgb(51 65 85 / 0.6);
  border-radius: 12px;
  padding: 24px;
  background: rgb(15 23 42 / 0.6);
  backdrop-filter: blur(8px);
}

.taiyi-title {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-daoist-muted);
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid rgb(51 65 85 / 0.4);
}

.taiyi-metrics {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.metric-row.primary .metric-value {
  font-size: 24px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--color-daoist-text);
}

.metric-label {
  font-size: 12px;
  color: var(--color-daoist-muted);
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: rgb(203 213 225);
  font-variant-numeric: tabular-nums;
}

.taiyi-empty {
  font-size: 14px;
  color: var(--color-daoist-muted);
  text-align: center;
  padding: 24px 0;
}
</style>
