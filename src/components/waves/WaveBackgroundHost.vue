<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "@/stores/appStore";
import { getWaveVariantDefinition } from "./waveVariants";
import WaveFlashRipple from "./variants/WaveFlashRipple.vue";

const store = useAppStore();

const definition = computed(() => getWaveVariantDefinition(store.waveVariantId));
const activeComponent = computed(() => definition.value.component);
const brookAudioOn = computed(
  () => definition.value.supportsAudio && store.waveAudioEnabled
);
const showRipples = computed(() => store.waveRippleClicksEnabled);
</script>

<template>
  <div class="wave-bg-host" aria-hidden="true">
    <component :is="activeComponent" :brook-audio-on="brookAudioOn" />
    <WaveFlashRipple v-if="showRipples" />
  </div>
</template>

<style scoped>
.wave-bg-host {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}
</style>
