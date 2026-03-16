<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "@/stores/appStore";

const props = withDefaults(
  defineProps<{
    pinyin: string;
    jyutping?: string | null;
    zhuyin?: string | null;
    taigi?: string | null;
  }>(),
  { jyutping: null, zhuyin: null, taigi: null }
);

const store = useAppStore();

const displayText = computed(() => {
  const dialect = store.preferredDialect;
  if (dialect === "jyutping" && props.jyutping?.trim()) return props.jyutping.trim();
  if (dialect === "zhuyin" && props.zhuyin?.trim()) return props.zhuyin.trim();
  if (dialect === "taigi" && props.taigi?.trim()) return props.taigi.trim();
  return props.pinyin?.trim() || "";
});
</script>

<template>
  <span class="pronunciation-text">{{ displayText }}</span>
</template>

<style scoped>
.pronunciation-text {
  transition: opacity 0.2s ease;
}
</style>
