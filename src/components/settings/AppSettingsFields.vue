<script setup lang="ts">
import { computed } from "vue";
import AccountSubscriptionPanel from "@/components/settings/AccountSubscriptionPanel.vue";
import ThemeSkinSelect from "@/components/theme/ThemeSkinSelect.vue";
import { WAVE_VARIANTS, getWaveVariantDefinition } from "@/components/waves/waveVariants";
import { getGroupedLanguages } from "@/lib/languages";
import { useAppStore } from "@/stores/appStore";
import { useThemeStore } from "@/stores/themeStore";

withDefaults(
  defineProps<{
    skinSelectVariant?: "default" | "toolbar";
    skinSelectClass?: string;
  }>(),
  { skinSelectVariant: "default", skinSelectClass: "" }
);

const store = useAppStore();
const themeStore = useThemeStore();

const waveSupportsAudio = computed(() => getWaveVariantDefinition(store.waveVariantId).supportsAudio);

/** Registry-driven options for the language `<select>`. Adding a new language
 *  in `src/lib/languages.ts` automatically appears here. */
const languageGroups = computed(() => getGroupedLanguages());
</script>

<template>
  <AccountSubscriptionPanel />
  <div class="headerField">
    <span class="headerFieldLabel">Preferred language</span>
    <select class="headerFieldSelect" v-model="store.preferredLanguage">
      <optgroup v-for="grp in languageGroups" :key="grp.label" :label="grp.label">
        <option v-for="lang in grp.items" :key="lang.code" :value="lang.code">
          {{ lang.label }}
        </option>
      </optgroup>
    </select>
  </div>
  <ThemeSkinSelect :variant="skinSelectVariant" :class="skinSelectClass" />
  <template v-if="themeStore.skinFeatures.homeWaveLayer">
    <div class="headerField">
      <span class="headerFieldLabel">Water style</span>
      <select class="headerFieldSelect" v-model="store.waveVariantId">
        <option v-for="v in WAVE_VARIANTS" :key="v.id" :value="v.id">{{ v.label }}</option>
      </select>
    </div>
    <div class="headerField headerField--motion">
      <span class="headerFieldLabel">Motion</span>
      <div class="headerToggleRow">
        <label class="headerToggle">
          <input
            type="checkbox"
            class="homeAmbientChk"
            :checked="store.waveRippleClicksEnabled"
            @change="store.setWaveRippleClicksEnabled(($event.target as HTMLInputElement).checked)"
          />
          <span>Ripple clicks</span>
        </label>
        <label v-if="waveSupportsAudio" class="headerToggle">
          <input
            type="checkbox"
            class="homeAmbientChk"
            :checked="store.waveAudioEnabled"
            @change="store.setWaveAudioEnabled(($event.target as HTMLInputElement).checked)"
          />
          <span>Ambient brook</span>
        </label>
      </div>
    </div>
  </template>
</template>

<style scoped>
.headerField {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.headerFieldLabel {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--muted);
  line-height: 1.25;
}

.headerFieldSelect {
  width: 100%;
  margin: 0;
  padding: 8px 12px;
  min-height: 38px;
  border: 1px solid var(--b2);
  border-radius: 8px;
  background: var(--color-daoist-surface);
  color: var(--color-daoist-text);
  font-size: 13px;
  box-sizing: border-box;
}

.headerField--motion {
  grid-column: 1 / -1;
}

.headerToggleRow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 18px;
  min-height: 38px;
  padding: 4px 2px;
}

.headerToggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--txt);
  cursor: pointer;
  user-select: none;
}

.homeAmbientChk {
  margin: 0;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  cursor: pointer;
  accent-color: var(--color-daoist-jade, #4a9b7a);
}

:deep(.skinLbl--toolbar) {
  width: 100%;
}

:deep(.header-skin-select) {
  min-width: 0;
}
</style>
