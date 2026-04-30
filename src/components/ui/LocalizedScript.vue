<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "@/stores/appStore";
import type { LanguageCode } from "@/lib/languages";

/**
 * Display the **native script** rendering of a CJK term in the user's
 * currently selected language. Pairs with `<PronunciationText>` (which
 * handles the romanization slot).
 *
 * Usage:
 *
 *   <LocalizedScript
 *     :hanzi="canonicalChinese"
 *     :scripts="termScriptsByLang"
 *   />
 *
 * - `hanzi` is the canonical Chinese fallback (rendered when the chosen
 *   language has no specific script entry).
 * - `scripts` maps `LanguageCode` → the term's script-slot value for that
 *   language (e.g. "건" for korean, "ཁྱན" for tibetan, "Càn" for
 *   vietnamese). Missing languages fall back to `hanzi`.
 *
 * Inherits the existing `cjkText` font stack so Hanzi fallback continues to
 * render correctly.
 */
const props = withDefaults(
  defineProps<{
    hanzi: string;
    scripts?: Partial<Record<LanguageCode, string | null | undefined>> | null;
  }>(),
  { scripts: () => ({}) }
);

const store = useAppStore();

const displayText = computed(() => {
  const lang = store.preferredLanguage as LanguageCode;
  const langScript = props.scripts?.[lang]?.toString().trim();
  if (langScript) return langScript;
  return props.hanzi?.trim() || "";
});
</script>

<template>
  <span class="localized-script cjkText">{{ displayText }}</span>
</template>

<style scoped>
.localized-script {
  /* Inherits the cjkText font-stack defined globally in App.vue / HexagramCenterView */
  transition: opacity 0.2s ease;
}
</style>
