import { onMounted, onUnmounted, ref } from "vue";

function initialReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

/** Tracks window.matchMedia('(prefers-reduced-motion: reduce)'). */
export function usePrefersReducedMotion() {
  const prefersReducedMotion = ref(initialReducedMotion());
  let mq: MediaQueryList | null = null;

  function update() {
    prefersReducedMotion.value = mq?.matches ?? false;
  }

  onMounted(() => {
    mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    update();
    mq.addEventListener("change", update);
  });

  onUnmounted(() => {
    mq?.removeEventListener("change", update);
    mq = null;
  });

  return prefersReducedMotion;
}
