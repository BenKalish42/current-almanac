/**
 * useSceneClock — shared, throttled wall-clock for ambient animations.
 *
 * Drives the daoist-theme scenes (MicrocosmicHourglass, FishermanScene,
 * SleepingFisherwomanScene) so they all sync to the same Ke (15-min) boundary
 * without each scene polling its own setInterval.
 *
 * - Pauses when document is hidden (battery friendly on mobile / Capacitor).
 * - Honors prefers-reduced-motion (caller decides what that means; we just
 *   surface a ref).
 * - Updates `now` ~4x per second; that's enough for breath cadence and
 *   countdown sublabels without flooding reactivity.
 */

import { computed, onMounted, onUnmounted, ref } from "vue";
import { useDocumentVisibility, useIntervalFn } from "@vueuse/core";
import { getShichenDetail } from "@/core/shichenDetail";
import { usePrefersReducedMotion } from "@/utils/usePrefersReducedMotion";

const SCENE_TICK_MS = 250;

export function useSceneClock() {
  const now = ref<number>(Date.now());
  const visibility = useDocumentVisibility();
  const prefersReducedMotion = usePrefersReducedMotion();

  const documentVisible = computed(() => visibility.value !== "hidden");

  const { pause, resume } = useIntervalFn(
    () => {
      now.value = Date.now();
    },
    SCENE_TICK_MS,
    { immediate: false, immediateCallback: false }
  );

  onMounted(() => {
    now.value = Date.now();
    if (documentVisible.value) resume();
  });

  // Pause/resume when tab visibility flips.
  // We can't use a watcher inside a regular function the same way as in setup,
  // but useIntervalFn returns reactive controls; instead we listen here.
  if (typeof document !== "undefined") {
    const onVis = () => {
      if (document.visibilityState === "hidden") {
        pause();
      } else {
        now.value = Date.now();
        resume();
      }
    };
    onMounted(() => document.addEventListener("visibilitychange", onVis));
    onUnmounted(() => document.removeEventListener("visibilitychange", onVis));
  }

  onUnmounted(() => {
    pause();
  });

  /**
   * Stable identifier for the current Ke (15-min slot). Changes precisely on a
   * Ke boundary, so scenes can `watch()` it to fire one-shot effects (fish
   * catch, hourglass flip, etc.).
   */
  const keKey = computed(() => {
    const d = new Date(now.value);
    const detail = getShichenDetail(d);
    return `${detail.organEntry.branch}-${detail.keInShichen}-${detail.keStartDate.getTime()}`;
  });

  /** Stable per-shichen key — flips at every 2-hour branch swap. */
  const shichenKey = computed(() => {
    const d = new Date(now.value);
    const detail = getShichenDetail(d);
    return `${detail.organEntry.branch}-${detail.organEntry.startHour}-${d.toDateString()}`;
  });

  /** Stable per-day key — flips at local midnight. */
  const dayKey = computed(() => {
    const d = new Date(now.value);
    return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
  });

  return {
    now,
    documentVisible,
    prefersReducedMotion,
    keKey,
    shichenKey,
    dayKey,
  };
}
