<script setup lang="ts">
import { computed } from "vue";
import { parseGanZhi } from "@/core/ganzhi";

const props = defineProps<{
  ganzhi: string | null;
  size?: number; // px
}>();

const size = computed(() => props.size ?? 64);
const info = computed(() => parseGanZhi(props.ganzhi ?? ""));
</script>

<template>
  <div v-if="ganzhi" :style="{ width: size+'px', height: size+'px' }">
    <svg :width="size" :height="size" viewBox="0 0 64 64">
      <rect x="4" y="4" width="56" height="56" rx="6" fill="none" stroke="rgba(200,40,40,0.9)" stroke-width="3"/>
      <rect x="8" y="8" width="48" height="48" rx="4" fill="rgba(200,40,40,0.06)" stroke="rgba(200,40,40,0.35)" stroke-width="1"/>
      <text x="32" y="38" text-anchor="middle" font-size="28" fill="rgba(200,40,40,0.9)" font-family="serif">
        {{ info.branch?.char ?? "" }}
      </text>
      <text x="18" y="22" text-anchor="middle" font-size="14" fill="rgba(200,40,40,0.8)" font-family="serif">
        {{ info.stem?.char ?? "" }}
      </text>
    </svg>
  </div>
  <div v-else style="opacity:0.6;">—</div>
</template>