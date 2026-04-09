<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { usePrefersReducedMotion } from "@/utils/usePrefersReducedMotion";

const MAX_RIPPLES = 8;
const RIPPLE_MS = 2400;

type Ripple = { id: number; x: number; y: number; size: number };

const ripples = ref<Ripple[]>([]);
let nextId = 0;
const reduced = usePrefersReducedMotion();

function spawnRipple(clientX: number, clientY: number) {
  if (reduced.value) return;
  const size = 80 + Math.random() * 60;
  const r: Ripple = { id: nextId++, x: clientX, y: clientY, size };
  ripples.value = [...ripples.value, r].slice(-MAX_RIPPLES);
  window.setTimeout(() => {
    ripples.value = ripples.value.filter((x) => x.id !== r.id);
  }, RIPPLE_MS);
}

function onPointerDown(ev: PointerEvent) {
  if (ev.button !== 0 && ev.pointerType === "mouse") return;
  spawnRipple(ev.clientX, ev.clientY);
}

function attachRippleListener() {
  window.addEventListener("pointerdown", onPointerDown, true);
}

function detachRippleListener() {
  window.removeEventListener("pointerdown", onPointerDown, true);
}

onMounted(() => {
  if (!reduced.value) attachRippleListener();
  watch(
    reduced,
    (r) => {
      if (r) {
        detachRippleListener();
        ripples.value = [];
      } else {
        attachRippleListener();
      }
    },
    { flush: "sync" }
  );
});

onUnmounted(() => {
  detachRippleListener();
});
</script>

<template>
  <div class="wave-flash-ripple" aria-hidden="true">
    <div
      v-for="r in ripples"
      :key="r.id"
      class="wave-flash-ripple__ring"
      :style="{
        left: `${r.x}px`,
        top: `${r.y}px`,
        width: `${r.size}px`,
        height: `${r.size}px`,
        marginLeft: `-${r.size / 2}px`,
        marginTop: `-${r.size / 2}px`,
        animationDuration: `${RIPPLE_MS}ms`,
      }"
    />
  </div>
</template>

<style scoped>
.wave-flash-ripple {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.wave-flash-ripple__ring {
  position: fixed;
  border-radius: 50%;
  border: 2px solid rgba(120, 175, 235, 0.42);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08) inset;
  animation: rippleExpand ease-out forwards;
  pointer-events: none;
}

@keyframes rippleExpand {
  0% {
    transform: scale(0.2);
    opacity: 0.55;
  }
  100% {
    transform: scale(3.2);
    opacity: 0;
  }
}
</style>
