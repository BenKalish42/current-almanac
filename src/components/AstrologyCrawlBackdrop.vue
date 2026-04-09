<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "@/stores/appStore";
import { OPENING_CRAWL_ZH } from "@/data/openingCrawlZh";
import { romanizeCrawlChar, type CrawlDialect } from "@/lib/crawlRomanization";
import PronunciationText from "@/components/ui/PronunciationText.vue";

const store = useAppStore();

const paragraphs = computed(() => {
  const d = store.preferredDialect as CrawlDialect;
  return OPENING_CRAWL_ZH.split("\n\n").map((para) =>
    Array.from(para).map((ch) => ({
      ch,
      ro: romanizeCrawlChar(ch, d),
    }))
  );
});

/** Feed the same computed reading into the slot PronunciationText expects for each dialect. */
function rubyProps(ro: string) {
  const dialect = store.preferredDialect;
  return {
    pinyin: dialect === "pinyin" || dialect === "taigi" ? ro : "",
    jyutping: dialect === "jyutping" ? ro : null,
    zhuyin: dialect === "zhuyin" ? ro : null,
    taigi: dialect === "taigi" ? ro : null,
  };
}
</script>

<template>
  <div class="astro-crawl-layer" aria-hidden="true">
    <div class="astro-crawl-stars" />
    <div class="astro-crawl-perspective">
      <div class="astro-crawl-tilt">
        <div class="astro-crawl-track">
          <div v-for="(para, pi) in paragraphs" :key="pi" class="astro-crawl-para">
            <span v-for="(cell, ci) in para" :key="`${pi}-${ci}`" class="astro-crawl-cell">
              <template v-if="cell.ch === ' '">
                <span class="astro-crawl-space" />
              </template>
              <template v-else>
                <span class="astro-crawl-han">{{ cell.ch }}</span>
                <PronunciationText
                  v-if="cell.ro"
                  class="astro-crawl-roman"
                  v-bind="rubyProps(cell.ro)"
                />
              </template>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.astro-crawl-layer {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  opacity: 0.2;
  background: radial-gradient(ellipse 100% 80% at 50% 100%, rgba(10, 10, 34, 0.85) 0%, rgba(0, 0, 16, 0.95) 45%, #020208 100%);
}

.astro-crawl-stars {
  position: absolute;
  inset: 0;
  opacity: 0.85;
  background-image:
    radial-gradient(1px 1px at 8% 12%, rgba(255, 255, 255, 0.55) 50%, transparent 52%),
    radial-gradient(1px 1px at 22% 38%, rgba(255, 255, 255, 0.35) 50%, transparent 52%),
    radial-gradient(1.5px 1.5px at 41% 7%, rgba(200, 220, 255, 0.5) 50%, transparent 52%),
    radial-gradient(1px 1px at 63% 24%, rgba(255, 255, 255, 0.4) 50%, transparent 52%),
    radial-gradient(1px 1px at 77% 61%, rgba(255, 255, 255, 0.28) 50%, transparent 52%),
    radial-gradient(1px 1px at 91% 18%, rgba(255, 255, 255, 0.45) 50%, transparent 52%),
    radial-gradient(1px 1px at 15% 72%, rgba(255, 255, 255, 0.32) 50%, transparent 52%),
    radial-gradient(1px 1px at 52% 51%, rgba(180, 210, 255, 0.42) 50%, transparent 52%),
    radial-gradient(1px 1px at 68% 78%, rgba(255, 255, 255, 0.25) 50%, transparent 52%);
  background-size: 220px 220px;
  background-position: 0 0;
  animation: astro-star-drift 200s linear infinite;
}

@media (prefers-reduced-motion: reduce) {
  .astro-crawl-stars {
    animation: none;
  }
}

@keyframes astro-star-drift {
  from {
    transform: translate3d(0, 0, 0);
  }
  to {
    transform: translate3d(-40px, -24px, 0);
  }
}

.astro-crawl-perspective {
  position: absolute;
  inset: 0;
  perspective: 380px;
  perspective-origin: 50% 78%;
  overflow: hidden;
}

.astro-crawl-tilt {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  top: -8%;
  transform: rotateX(52deg);
  transform-origin: 50% 100%;
  transform-style: preserve-3d;
}

.astro-crawl-track {
  margin: 0 auto;
  max-width: min(40rem, 90vw);
  padding: 0 0.75rem 30vh;
  font-family: "Noto Serif SC", "Songti SC", "SimSun", serif;
  font-size: clamp(0.95rem, 2.2vw, 1.35rem);
  font-weight: 500;
  line-height: 1.65;
  letter-spacing: 0.04em;
  text-align: justify;
  color: #e8d89a;
  text-shadow: 0 0 12px rgba(232, 216, 154, 0.08);
  animation: astro-crawl-scroll 120s linear infinite;
}

.astro-crawl-para + .astro-crawl-para {
  margin-top: 1.5em;
}

.astro-crawl-cell {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  vertical-align: top;
  margin: 0 1px;
  min-width: 0.5em;
}

.astro-crawl-han {
  display: block;
  line-height: 1.15;
}

.astro-crawl-roman {
  display: block;
  margin-top: 1px;
  font-family: ui-sans-serif, system-ui, -apple-system, Tahoma, Arial, sans-serif;
  font-size: 0.38em;
  font-weight: 500;
  line-height: 1.05;
  letter-spacing: 0.02em;
  color: rgba(100, 75, 45, 0.92);
  max-width: 4.2em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.astro-crawl-space {
  display: inline-block;
  width: 0.35em;
}

@keyframes astro-crawl-scroll {
  from {
    transform: translateY(42vh);
  }
  to {
    transform: translateY(-118%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .astro-crawl-track {
    animation: none;
    transform: translateY(12vh);
    opacity: 0.42;
  }
}
</style>
