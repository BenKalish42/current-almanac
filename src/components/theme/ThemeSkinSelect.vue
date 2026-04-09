<script setup lang="ts">
import { storeToRefs } from "pinia";
import { useThemeStore, SKIN_OPTIONS, type ChosenSkin } from "@/stores/themeStore";

withDefaults(
  defineProps<{
    /** Stacked label + select for header toolbars */
    variant?: "default" | "toolbar";
  }>(),
  { variant: "default" }
);

const theme = useThemeStore();
const { chosenSkin } = storeToRefs(theme);

function onChange(e: Event) {
  const v = (e.target as HTMLSelectElement).value as ChosenSkin;
  theme.setChosenSkin(v);
}
</script>

<template>
  <label class="skinLbl" :class="{ 'skinLbl--toolbar': variant === 'toolbar' }">
    <span class="skinLblText">Chosen Skin</span>
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
.skinLbl--toolbar {
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
  margin: 0;
}
.skinLblText {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--muted);
  line-height: 1.2;
}
.skinLbl--toolbar .skinLblText {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.skinLbl--toolbar .skinSelect {
  min-width: 0;
  max-width: none;
  width: 100%;
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
