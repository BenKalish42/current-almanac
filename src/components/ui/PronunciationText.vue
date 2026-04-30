<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "@/stores/appStore";
import type { LanguageCode } from "@/lib/languages";

/**
 * Display the pronunciation/reading of a hexagram (or other CJK term) in the
 * user's currently selected language. Each language has an optional prop;
 * when the chosen language has no value, we fall back to `pinyin`.
 *
 * Adding a new language is three steps:
 *   1. Add a `LanguageDefinition` to `src/lib/languages.ts`.
 *   2. Add a per-hex column in `src/data/seed_hexagrams.json`.
 *   3. Add an optional prop here and wire it into the lookup map below.
 */
const props = withDefaults(
  defineProps<{
    pinyin: string;
    jyutping?: string | null;
    zhuyin?: string | null;
    taigi?: string | null;
    japanese?: string | null;
    korean?: string | null;
    tibetan?: string | null;
    hindi?: string | null;
  }>(),
  {
    jyutping: null,
    zhuyin: null,
    taigi: null,
    japanese: null,
    korean: null,
    tibetan: null,
    hindi: null,
  }
);

const store = useAppStore();

const displayText = computed(() => {
  const lookup: Record<LanguageCode, string | null | undefined> = {
    pinyin: props.pinyin,
    jyutping: props.jyutping,
    zhuyin: props.zhuyin,
    taigi: props.taigi,
    japanese: props.japanese,
    korean: props.korean,
    tibetan: props.tibetan,
    hindi: props.hindi,
  };
  const chosen = lookup[store.preferredLanguage as LanguageCode]?.trim();
  if (chosen) return chosen;
  // Fall back to the canonical pinyin reading when the chosen language has
  // no entry for this term (matches existing `taigi` behaviour).
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
