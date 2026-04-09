<script setup lang="ts">
/**
 * Retro “GIF river veil”: repeating bands drift + background-position shear (visible current).
 */
import { computed } from "vue";
import { usePrefersReducedMotion } from "@/utils/usePrefersReducedMotion";

withDefaults(
  defineProps<{
    brookAudioOn?: boolean;
  }>(),
  { brookAudioOn: false }
);

const reduced = usePrefersReducedMotion();
const animClass = computed(() => (reduced.value ? "wave-gif-veil--static" : "wave-gif-veil--anim"));
</script>

<template>
  <div class="wave-gif-veil" :class="animClass">
    <div class="wave-gif-veil__layer wave-gif-veil__layer--a" />
    <div class="wave-gif-veil__layer wave-gif-veil__layer--b" />
  </div>
</template>

<style scoped>
.wave-gif-veil {
  position: absolute;
  inset: 0;
  opacity: 0.14;
}

.wave-gif-veil__layer {
  position: absolute;
  inset: -12%;
  background-repeat: repeat;
  background-size: 240px 200px;
  mix-blend-mode: soft-light;
}

.wave-gif-veil__layer--a {
  background-image: repeating-linear-gradient(
    105deg,
    rgba(52, 112, 188, 0.34) 0px,
    rgba(48, 105, 175, 0.14) 14px,
    transparent 28px,
    rgba(34, 78, 148, 0.2) 42px,
    transparent 56px
  );
}

.wave-gif-veil__layer--b {
  background-image: repeating-linear-gradient(
    -98deg,
    rgba(88, 148, 218, 0.2) 0px,
    transparent 18px,
    rgba(36, 92, 155, 0.26) 36px,
    transparent 52px
  );
  opacity: 0.85;
}

.wave-gif-veil--anim .wave-gif-veil__layer--a {
  animation:
    waveGifDriftA 28s linear infinite,
    waveGifShearA 14s linear infinite;
}

.wave-gif-veil--anim .wave-gif-veil__layer--b {
  animation:
    waveGifDriftB 36s linear infinite reverse,
    waveGifShearB 18s linear infinite reverse;
}

.wave-gif-veil--static .wave-gif-veil__layer--a,
.wave-gif-veil--static .wave-gif-veil__layer--b {
  animation: none;
}

@keyframes waveGifDriftA {
  0% {
    transform: translate3d(0, 0, 0);
  }
  100% {
    transform: translate3d(-220px, 36px, 0);
  }
}

@keyframes waveGifDriftB {
  0% {
    transform: translate3d(0, 0, 0) scale(1.03);
  }
  100% {
    transform: translate3d(180px, -28px, 0) scale(1.03);
  }
}

@keyframes waveGifShearA {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 240px 80px;
  }
}

@keyframes waveGifShearB {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: -200px -60px;
  }
}
</style>
