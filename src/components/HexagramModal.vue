<script setup lang="ts">
import { onMounted, onUnmounted, computed } from "vue";

type HexagramSummary = {
  daoist: string;
  buddhist: string;
  confucian: string;
  humanDesign: string;
  geneKeys: string;
};

const props = defineProps<{
  open: boolean;
  hexNum: number | null;
  hexName: string;
  summaries: HexagramSummary | null;
}>();

const emit = defineEmits<{ (e: "close"): void }>();

const sections = computed(() => [
  { key: "daoist", label: "Daoist (Liu Yiming / Wang Bi)", text: props.summaries?.daoist ?? "" },
  { key: "buddhist", label: "Buddhist (Chih-hsui Ou-i)", text: props.summaries?.buddhist ?? "" },
  { key: "confucian", label: "Confucian (Ten Wings)", text: props.summaries?.confucian ?? "" },
  { key: "humanDesign", label: "Human Design", text: props.summaries?.humanDesign ?? "" },
  { key: "geneKeys", label: "Gene Keys", text: props.summaries?.geneKeys ?? "" },
]);

function onKeydown(e: KeyboardEvent) {
  if (!props.open) return;
  if (e.key === "Escape") emit("close");
}

onMounted(() => window.addEventListener("keydown", onKeydown));
onUnmounted(() => window.removeEventListener("keydown", onKeydown));
</script>

<template>
  <div v-if="open" class="hexModalOverlay" @click.self="emit('close')">
    <div class="hexModal" role="dialog" aria-modal="true">
      <div class="hexModalHeader">
        <div class="hexModalTitle">Hexagram #{{ hexNum ?? "—" }} — {{ hexName }}</div>
        <button class="btn small" @click="emit('close')">Close</button>
      </div>
      <div class="hexModalBody">
        <div v-for="section in sections" :key="section.key" class="hexModalSection">
          <div class="hexModalSectionTitle">{{ section.label }}</div>
          <div class="hexModalSectionText">
            {{ section.text && section.text.trim().length ? section.text : "Summary pending." }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hexModalOverlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: grid;
  place-items: center;
  z-index: 60;
  padding: 18px;
}
.hexModal {
  width: min(900px, 100%);
  max-height: min(85vh, 900px);
  overflow: auto;
  background: rgba(0,0,0,0.9);
  border: 1px solid var(--b2);
  border-radius: 14px;
  padding: 16px;
  display: grid;
  gap: 12px;
}
.hexModalHeader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.hexModalTitle {
  font-size: 14px;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: var(--muted);
}
.hexModalBody {
  display: grid;
  gap: 12px;
}
.hexModalSection {
  border: 1px solid var(--b);
  border-radius: 12px;
  padding: 12px;
  background: rgba(0,0,0,0.2);
}
.hexModalSectionTitle {
  font-size: 12px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.hexModalSectionText {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.5;
}
</style>
