<script setup lang="ts">
import { computed, ref } from "vue";
import { YI_JING_HEXAGRAMS } from "@/data/yiJing";
import { getHexBinary } from "@/core/iching";
import HexagramLines from "@/components/HexagramLines.vue";
import HexagramModal from "@/components/HexagramModal.vue";
import LocalizedScript from "@/components/ui/LocalizedScript.vue";
import seedHexagrams from "@/data/seed_hexagrams.json";
import { localizedNumeral } from "@/i18n/numerals_localized";
import type { LanguageCode } from "@/lib/languages";

function toRoman(num: number): string {
  const roman = [
    { symbol: 'LX', value: 60 },
    { symbol: 'L', value: 50 },
    { symbol: 'XL', value: 40 },
    { symbol: 'X', value: 10 },
    { symbol: 'IX', value: 9 },
    { symbol: 'V', value: 5 },
    { symbol: 'IV', value: 4 },
    { symbol: 'I', value: 1 }
  ];
  let str = '';
  let n = num;
  for (const { symbol, value } of roman) {
    const q = Math.floor(n / value);
    n -= q * value;
    str += symbol.repeat(q);
  }
  return str;
}

function toChineseNumeral(num: number): string {
  const cnNums = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"] as const;
  if (num < 10) return cnNums[num] ?? "";
  if (num === 10) return "十";
  if (num < 20) return "十" + (cnNums[num % 10] ?? "");
  const tens = Math.floor(num / 10);
  const units = num % 10;
  return (cnNums[tens] ?? "") + "十" + (units === 0 ? "" : (cnNums[units] ?? ""));
}

type HexagramSummary = {
  daoist: string;
  buddhist: string;
  confucian: string;
  psychological: string;
  humanDesign: string;
  geneKeys: string;
};
type HexagramSummaryMap = Record<string, HexagramSummary>;

type SeedHexagram = {
  id: number;
  pinyin_name: string;
  english_name: string;
  perspectives: {
    daoist: string;
    confucian: string;
    buddhist: string;
    psychological: string;
    human_design: string;
    gene_keys: string;
  };
};

function buildHexSummaryMap(seed: SeedHexagram[]): HexagramSummaryMap {
  const map: HexagramSummaryMap = {};
  for (const h of seed) {
    map[String(h.id)] = {
      daoist: h.perspectives?.daoist ?? "",
      confucian: h.perspectives?.confucian ?? "",
      buddhist: h.perspectives?.buddhist ?? "",
      psychological: h.perspectives?.psychological ?? "",
      humanDesign: h.perspectives?.human_design ?? "",
      geneKeys: h.perspectives?.gene_keys ?? "",
    };
  }
  return map;
}

const hexSummaryMap = buildHexSummaryMap(seedHexagrams as SeedHexagram[]);

const isHexModalOpen = ref(false);
const selectedHexNum = ref<number | null>(null);

const HEX_NAME_CN_SHORT: string[] = [
  "", "乾", "坤", "屯", "蒙", "需", "讼", "师", "比", "小畜", "履", "泰", "否",
  "同人", "大有", "谦", "豫", "随", "蛊", "临", "观", "噬嗑", "贲", "剥", "复",
  "无妄", "大畜", "颐", "大过", "坎", "离", "咸", "恒", "遯", "大壮", "晋", "明夷",
  "家人", "睽", "蹇", "解", "损", "益", "夬", "姤", "萃", "升", "困", "井", "革",
  "鼎", "震", "艮", "渐", "归妹", "丰", "旅", "巽", "兑", "涣", "节", "中孚",
  "小过", "既济", "未济",
];

import { LANGUAGES } from "@/lib/languages";

/** Build a ScriptMap that contains every language's numeral form for `id`,
 *  so LocalizedScript can swap reactively without re-running this function. */
function numeralScripts(id: number): Partial<Record<LanguageCode, string>> {
  const out: Partial<Record<LanguageCode, string>> = {};
  for (const def of LANGUAGES) {
    if (def.code === "pinyin") continue; // hanzi fallback handles default
    out[def.code] = localizedNumeral(id, def.code);
  }
  return out;
}

function hexNameShort(num: number | null) {
  if (!num || num < 1 || num >= HEX_NAME_CN_SHORT.length) return "—";
  return HEX_NAME_CN_SHORT[num];
}

const selectedHexSummary = computed(() => {
  const num = selectedHexNum.value;
  if (!num) return null;
  return hexSummaryMap[String(num)] ?? null;
});

const selectedHexDisplayName = computed(
  () => hexNameShort(selectedHexNum.value) || "—"
);

function openHexModal(id: number) {
  selectedHexNum.value = id;
  isHexModalOpen.value = true;
}

function closeHexModal() {
  isHexModalOpen.value = false;
}

function onViewHexagram(id: number) {
  selectedHexNum.value = id;
}
</script>

<template>
  <div class="wrap">
    <main class="main">
      <div class="card">
        <div class="header">
          <h1 class="title">Hexagram Center</h1>
          <p class="subtitle">The 64 States of Change</p>
        </div>
        
        <div class="hex-grid">
          <div 
            v-for="hex in YI_JING_HEXAGRAMS" 
            :key="hex.id" 
            class="hex-cell"
            @click="openHexModal(hex.id)"
            role="button"
            tabindex="0"
            @keydown.enter.prevent="openHexModal(hex.id)"
            @keydown.space.prevent="openHexModal(hex.id)"
            :aria-label="`Hexagram ${hex.id}`"
          >
            <div class="hex-numerals">
              <div class="hex-arabic">{{ hex.id }}</div>
              <div class="hex-roman">{{ toRoman(hex.id) }}</div>
              <LocalizedScript
                class="hex-chinese"
                :hanzi="toChineseNumeral(hex.id)"
                :scripts="numeralScripts(hex.id)"
              />
            </div>
            <div class="hex-lines">
              <HexagramLines :binary="getHexBinary(hex.id)" size="sm" />
            </div>
          </div>
        </div>
      </div>
    </main>

    <HexagramModal
      :open="isHexModalOpen"
      :hex-num="selectedHexNum"
      :hex-name="selectedHexDisplayName"
      :summaries="selectedHexSummary"
      :moving-lines="[]"
      @close="closeHexModal"
      @view-hexagram="onViewHexagram"
    />
  </div>
</template>

<style scoped>
.wrap {
  display: flex;
  min-height: 100vh;
  padding: 18px;
  color: var(--txt);
}

.main {
  flex: 1;
  display: flex;
  justify-content: center;
}

.card {
  border: 1px solid var(--b);
  border-radius: 12px;
  padding: 24px;
  max-width: 1200px;
  width: 100%;
  background: rgba(0, 0, 0, 0.02);
}

.header {
  margin-bottom: 32px;
  text-align: center;
}

.title {
  font-size: 24px;
  font-weight: 800;
  color: var(--txt);
  margin-bottom: 6px;
}

.subtitle {
  font-size: 14px;
  color: var(--muted);
}

.hex-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (min-width: 768px) {
  .hex-grid {
    grid-template-columns: repeat(8, 1fr);
  }
}

.hex-cell {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 10px;
  background: var(--bg);
  border: 1px solid var(--b2);
  cursor: pointer;
  transition: all 0.2s ease;
}

.hex-cell:hover, .hex-cell:focus-visible {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
  outline: none;
}

.hex-numerals {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 4px;
  width: 32px;
}

.hex-arabic {
  font-size: 11px;
  font-weight: 700;
  color: var(--txt);
  line-height: 1;
}

.hex-roman {
  font-size: 10px;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0.5px;
  line-height: 1;
}

.hex-chinese {
  font-size: 11px;
  color: var(--muted);
  line-height: 1;
}

.cjkText {
  font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei",
    ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}

.hex-lines {
  display: flex;
  justify-content: center;
}
</style>
