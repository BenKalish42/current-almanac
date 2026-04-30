<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppSettingsFields from "@/components/settings/AppSettingsFields.vue";

/** Gap between trigger bottom and panel top (px). */
const DROPDOWN_GAP_PX = 6;

withDefaults(
  defineProps<{
    /** Classes for the trigger (same as adjacent nav links, e.g. nav-link, fw-tab, aol-keyword) */
    triggerClass?: string;
  }>(),
  { triggerClass: "" }
);

const route = useRoute();
const open = ref(false);
const rootRef = ref<HTMLElement | null>(null);
const triggerRef = ref<HTMLElement | null>(null);
const dropdownTop = ref("0px");

function updateDropdownPosition() {
  if (!open.value) return;
  const el = triggerRef.value;
  if (!el) return;
  const r = el.getBoundingClientRect();
  dropdownTop.value = `${Math.round(r.bottom + DROPDOWN_GAP_PX)}px`;
}

function toggle(e: Event) {
  e.stopPropagation();
  open.value = !open.value;
}

function onDocPointerDown(e: PointerEvent) {
  if (!open.value || !rootRef.value) return;
  const t = e.target;
  if (t instanceof Node && !rootRef.value.contains(t)) {
    open.value = false;
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") open.value = false;
}

watch(
  () => route.fullPath,
  () => {
    open.value = false;
  }
);

watch(open, async (v) => {
  if (v) {
    await nextTick();
    updateDropdownPosition();
    window.addEventListener("scroll", updateDropdownPosition, true);
    window.addEventListener("resize", updateDropdownPosition);
    document.addEventListener("pointerdown", onDocPointerDown, true);
  } else {
    window.removeEventListener("scroll", updateDropdownPosition, true);
    window.removeEventListener("resize", updateDropdownPosition);
    document.removeEventListener("pointerdown", onDocPointerDown, true);
  }
});

onMounted(() => document.addEventListener("keydown", onKeydown));
onUnmounted(() => {
  document.removeEventListener("keydown", onKeydown);
  document.removeEventListener("pointerdown", onDocPointerDown, true);
  window.removeEventListener("scroll", updateDropdownPosition, true);
  window.removeEventListener("resize", updateDropdownPosition);
});
</script>

<template>
  <div ref="rootRef" class="toolbar-settings-root">
    <a
      ref="triggerRef"
      href="#"
      class="toolbar-settings-trigger"
      :class="triggerClass"
      aria-haspopup="true"
      :aria-expanded="open"
      aria-controls="toolbar-settings-panel"
      @click.prevent="toggle"
      @keydown.space.prevent="toggle"
    >
      Settings
    </a>
    <div
      v-show="open"
      id="toolbar-settings-panel"
      class="toolbar-settings-dropdown"
      role="region"
      aria-label="App settings"
      :style="{ top: dropdownTop }"
      @click.stop
    >
      <div class="toolbar-settings-panelInner">
        <div class="toolbar-settings-fieldsGrid">
          <AppSettingsFields skin-select-variant="default" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolbar-settings-root {
  position: relative;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}

.toolbar-settings-dropdown {
  position: fixed;
  z-index: 4000;
  /* Viewport-right aligned; micro inset so it doesn’t hug the edge. `top` is set inline from the trigger. */
  right: max(10px, env(safe-area-inset-right, 0px));
  left: auto;
  box-sizing: border-box;
  /* Cap width so a 10px gutter remains on the left when the panel is wide (fixed = no document scroll). */
  width: min(440px, calc(100vw - 20px));
  max-width: min(440px, calc(100vw - 20px));
  min-width: 0;
  max-height: min(78vh, 680px);
  overflow-x: hidden;
  overflow-y: auto;
  padding: 0;
  border-radius: 12px;
  border: 1px solid var(--b2, rgba(255, 255, 255, 0.12));
  background: var(--color-daoist-surface, #1a1d24);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
}

.toolbar-settings-panelInner {
  padding: 14px 14px 16px;
}

.toolbar-settings-fieldsGrid {
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: stretch;
}

.toolbar-settings-fieldsGrid :deep(.skinLbl) {
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
}

.toolbar-settings-fieldsGrid :deep(.skinLblText) {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.toolbar-settings-fieldsGrid :deep(.skinSelect) {
  width: 100%;
  max-width: 100%;
  min-width: 0 !important;
  box-sizing: border-box;
}

.toolbar-settings-fieldsGrid :deep(.headerFieldSelect) {
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.toolbar-settings-trigger {
  display: inline-flex;
  align-items: center;
}
</style>
