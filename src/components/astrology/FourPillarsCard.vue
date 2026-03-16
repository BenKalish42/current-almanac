<script setup lang="ts">
import { useAstrologyStore } from "@/stores/astrologyStore";
import type { Element } from "@/core/ganzhi";

const astrologyStore = useAstrologyStore();

const WU_XING_CLASSES: Record<Element, string> = {
  Wood: "pillar-tile-wood",
  Fire: "pillar-tile-fire",
  Earth: "pillar-tile-earth",
  Metal: "pillar-tile-metal",
  Water: "pillar-tile-water",
};

function tileClass(wuXing: Element): string {
  return WU_XING_CLASSES[wuXing] ?? "pillar-tile-earth";
}
</script>

<template>
  <div class="four-pillars-card">
    <div class="pillars-grid">
      <div
        v-for="pillar in astrologyStore.fourPillars"
        :key="pillar.label"
        class="pillar-column"
      >
        <div class="pillar-label">{{ pillar.label }}</div>
        <div
          class="pillar-tile stem-tile"
          :class="tileClass(pillar.stem.wuXing)"
        >
          <span class="hanzi">{{ pillar.stem.hanzi }}</span>
          <span v-if="pillar.stem.pinyin" class="pinyin">{{ pillar.stem.pinyin }}</span>
        </div>
        <div
          class="pillar-tile branch-tile"
          :class="tileClass(pillar.branch.wuXing)"
        >
          <span class="hanzi">{{ pillar.branch.hanzi }}</span>
          <span v-if="pillar.branch.pinyin" class="pinyin">{{ pillar.branch.pinyin }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.four-pillars-card {
  border-radius: 0.75rem;
  border: 1px solid var(--b2, #334155);
  background: var(--card-bg, rgba(15, 23, 42, 0.6));
  padding: 1rem;
  margin-bottom: 1rem;
}

.pillars-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
}

.pillar-column {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.pillar-label {
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
}

.pillar-tile {
  border-radius: 0.375rem;
  padding: 0.375rem 0.25rem;
  text-align: center;
  border-width: 1px;
  border-style: solid;
}

.stem-tile {
  min-height: 2.25rem;
}
.branch-tile {
  min-height: 2.25rem;
}

.hanzi {
  display: block;
  font-size: 1.25rem;
  font-family: "Noto Serif SC", "SimSun", serif;
  line-height: 1.2;
}
.pinyin {
  display: block;
  font-size: 0.65rem;
  opacity: 0.9;
  margin-top: 0.125rem;
}

/* Wu Xing theming */
.pillar-tile-wood {
  border-color: rgba(16, 185, 129, 0.4);
  color: rgb(167, 243, 208);
  background: rgba(6, 78, 59, 0.25);
}
.pillar-tile-fire {
  border-color: rgba(249, 115, 22, 0.5);
  color: rgb(254, 215, 170);
  background: rgba(124, 45, 18, 0.25);
}
.pillar-tile-earth {
  border-color: rgba(245, 158, 11, 0.4);
  color: rgb(253, 230, 138);
  background: rgba(120, 53, 15, 0.25);
}
.pillar-tile-metal {
  border-color: rgba(148, 163, 184, 0.4);
  color: rgb(203, 213, 225);
  background: rgba(51, 65, 85, 0.25);
}
.pillar-tile-water {
  border-color: rgba(59, 130, 246, 0.4);
  color: rgb(191, 219, 254);
  background: rgba(30, 58, 138, 0.25);
}
</style>
