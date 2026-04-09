<script setup lang="ts">
import { storeToRefs } from "pinia";
import { useThemeStore, SKIN_OPTIONS, type ChosenSkin } from "@/stores/themeStore";

const theme = useThemeStore();
const { chosenSkin } = storeToRefs(theme);

function onChange(e: Event) {
  const v = (e.target as HTMLSelectElement).value as ChosenSkin;
  theme.setChosenSkin(v);
}
</script>

<template>
  <label class="skinLbl">
    Chosen Skin
    <select class="skinSelect" :value="chosenSkin" @change="onChange">
      <option v-for="opt in SKIN_OPTIONS" :key="opt.id" :value="opt.id">
        {{ opt.label }}
      </option>
    </select>
  </label>
</template>

<style scoped>
.skinLbl {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
}
.skinSelect {
  padding: 8px 12px;
  min-height: 38px;
  border: 1px solid var(--b2);
  border-radius: 8px;
  background: var(--color-daoist-surface);
  color: var(--color-daoist-text);
  font-size: 13px;
  min-width: min(200px, 70vw);
  max-width: min(280px, 92vw);
}
</style>
