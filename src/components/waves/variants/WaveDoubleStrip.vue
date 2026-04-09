<script setup lang="ts">
import { computed } from "vue";
import { usePrefersReducedMotion } from "@/utils/usePrefersReducedMotion";

withDefaults(
  defineProps<{
    brookAudioOn?: boolean;
  }>(),
  { brookAudioOn: false }
);

const reduced = usePrefersReducedMotion();
const animClass = computed(() => (reduced.value ? "wave-double-strip--static" : ""));
</script>

<template>
  <div class="wave-double-strip" :class="animClass">
    <div class="wave-double-strip__band wave-double-strip__band--back" />
    <div class="wave-double-strip__band wave-double-strip__band--front" />
  </div>
</template>

<style scoped>
.wave-double-strip {
  position: absolute;
  inset: 0;
  opacity: 0.18;
  pointer-events: none;
}

.wave-double-strip__band {
  position: absolute;
  left: -15%;
  width: 130%;
  height: 22%;
  border-radius: 50% / 45%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(58, 128, 198, 0.42) 25%,
    rgba(38, 88, 158, 0.34) 50%,
    rgba(78, 142, 212, 0.38) 75%,
    transparent 100%
  );
  filter: blur(1px);
  mix-blend-mode: soft-light;
}

.wave-double-strip__band--back {
  bottom: 18%;
  animation: stripScrollSlow 20s ease-in-out infinite alternate;
}

.wave-double-strip__band--front {
  bottom: 8%;
  height: 18%;
  opacity: 0.85;
  animation: stripScrollFast 14s ease-in-out infinite alternate;
}

.wave-double-strip--static .wave-double-strip__band--back,
.wave-double-strip--static .wave-double-strip__band--front {
  animation: none;
}

@keyframes stripScrollSlow {
  0% {
    transform: translate3d(-11%, 0, 0) rotate(-2.2deg);
  }
  100% {
    transform: translate3d(11%, -14px, 0) rotate(1.6deg);
  }
}

@keyframes stripScrollFast {
  0% {
    transform: translate3d(9%, 4px, 0) rotate(1.8deg);
  }
  100% {
    transform: translate3d(-12%, -10px, 0) rotate(-1.4deg);
  }
}
</style>
