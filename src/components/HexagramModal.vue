<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref, watch } from "vue";
import { getHexBinary, getRelatingHexagram } from "@/core/iching";
import { YI_JING_BY_ID, type YiJingHexagram } from "@/data/yiJing";
import PhilosophyIcon from "@/components/astrology/PhilosophyIcon.vue";
import LocalizedScript from "@/components/ui/LocalizedScript.vue";
import PronunciationText from "@/components/ui/PronunciationText.vue";
import { hexagramScripts, hexagramRomans } from "@/i18n/localizedTerms";

type HexagramSummary = {
  daoist: string;
  buddhist: string;
  confucian: string;
  psychological: string;
  humanDesign: string;
  geneKeys: string;
};

type PhilosophyKey = "daoism" | "confucianism" | "buddhism" | "psychology" | "humandesign" | "genekeys";

const HEX_NAME_TRAD: string[] = [
  "",
  "乾", "坤", "屯", "蒙", "需", "訟", "師", "比", "小畜", "履", "泰", "否", "同人", "大有", "謙", "豫",
  "隨", "蠱", "臨", "觀", "噬嗑", "賁", "剝", "復", "無妄", "大畜", "頤", "大過", "坎", "離", "咸", "恆",
  "遯", "大壯", "晉", "明夷", "家人", "睽", "蹇", "解", "損", "益", "夬", "姤", "萃", "升", "困", "井",
  "革", "鼎", "震", "艮", "漸", "歸妹", "豐", "旅", "巽", "兌", "渙", "節", "中孚", "小過", "既濟", "未濟",
];

const props = withDefaults(
  defineProps<{
    open: boolean;
    hexNum: number | null;
    hexName: string;
    summaries: HexagramSummary | null;
    movingLines?: number[];
  }>(),
  { movingLines: () => [] }
);

const PHILOSOPHY_DISPLAY: Record<PhilosophyKey, string> = {
  daoism: "Daoism",
  confucianism: "Confucianism",
  buddhism: "Buddhism",
  psychology: "Psychology",
  humandesign: "Human Design",
  genekeys: "Gene Keys",
};

const emit = defineEmits<{ (e: "close"): void; (e: "viewHexagram", id: number): void }>();
const activePhilosophy = ref<PhilosophyKey>("daoism");
const isExploded = ref(false);
const activeLine = ref<number | null>(null);
const lineData = ref<Record<string, Record<string, Record<string, string>>> | null>(null);

async function loadLineData() {
  if (lineData.value) return;
  try {
    const data = await import("@/data/yiJingLines.json");
    lineData.value = data.default as Record<string, Record<string, Record<string, string>>>;
  } catch {
    lineData.value = null;
  }
}

function onLineClick(lineNumber: number) {
  activeLine.value = lineNumber;
  void loadLineData();
}

watch(isExploded, (val) => {
  if (val) void loadLineData();
});

const activeLineText = computed(() => {
  const hexId = props.hexNum;
  const line = activeLine.value;
  const philosophy = activePhilosophy.value;
  if (!hexId || !line || !lineData.value) return null;
  const byLine = lineData.value[String(hexId)];
  if (!byLine) return null;
  const entry = byLine[String(line)];
  if (!entry) return null;
  return entry[philosophy] ?? null;
});

const selectedHexagram = computed<YiJingHexagram | null>(() => {
  if (!props.hexNum) return null;
  return YI_JING_BY_ID.get(props.hexNum) ?? null;
});

const hexTraditionalName = computed(() => {
  const num = props.hexNum;
  if (!num || num < 1 || num >= HEX_NAME_TRAD.length) return props.hexName || "Unknown";
  return HEX_NAME_TRAD[num] ?? props.hexName ?? "Unknown";
});

const hexagramLines = computed(() => {
  const binaryTopToBottom = getHexBinary(props.hexNum);
  if (!binaryTopToBottom) return [];
  const bitsBottomToTop = binaryTopToBottom.split("").reverse();
  return bitsBottomToTop.map((bit, indexFromBottom) => ({
    id: `${indexFromBottom}-${bit}`,
    isYang: bit === "1",
    y: 106 - indexFromBottom * 16,
    lineNumber: indexFromBottom + 1,
    label: indexFromBottom === 0 ? "Line 1 (Bottom)" : indexFromBottom === 5 ? "Line 6 (Top)" : `Line ${indexFromBottom + 1}`,
  }));
});

const upperTrigramLines = computed(() =>
  hexagramLines.value.filter((line) => line.lineNumber >= 4).sort((a, b) => b.lineNumber - a.lineNumber)
);

const lowerTrigramLines = computed(() =>
  hexagramLines.value.filter((line) => line.lineNumber <= 3).sort((a, b) => b.lineNumber - a.lineNumber)
);

const LINE_HEIGHT = 8;
const upperBracketBounds = computed(() => {
  const lines = upperTrigramLines.value;
  if (!lines.length) return { top: 26, bottom: 66 };
  const topY = Math.min(...lines.map((l) => l.y));
  const bottomY = Math.max(...lines.map((l) => l.y)) + LINE_HEIGHT;
  return { top: topY, bottom: bottomY };
});
const lowerBracketBounds = computed(() => {
  const lines = lowerTrigramLines.value;
  if (!lines.length) return { top: 74, bottom: 114 };
  const topY = Math.min(...lines.map((l) => l.y));
  const bottomY = Math.max(...lines.map((l) => l.y)) + LINE_HEIGHT;
  return { top: topY, bottom: bottomY };
});

/** Bracket path d strings. When exploded, upper moves -16px, lower +16px; brackets use transformed coords to align. */
const BRACKET_X = 38;
const SERIF_WIDTH = 4;
const EXPLODE_OFFSET = 16;

const upperBracketPath = computed(() => {
  const { top, bottom } = upperBracketBounds.value;
  const t = top - EXPLODE_OFFSET;
  const b = bottom - EXPLODE_OFFSET;
  const h = b - t;
  return `M ${BRACKET_X} ${t} v ${h} M ${BRACKET_X} ${t} h ${SERIF_WIDTH} M ${BRACKET_X} ${b} h ${SERIF_WIDTH}`;
});

const lowerBracketPath = computed(() => {
  const { top, bottom } = lowerBracketBounds.value;
  const t = top + EXPLODE_OFFSET;
  const b = bottom + EXPLODE_OFFSET;
  const h = b - t;
  return `M ${BRACKET_X} ${t} v ${h} M ${BRACKET_X} ${t} h ${SERIF_WIDTH} M ${BRACKET_X} ${b} h ${SERIF_WIDTH}`;
});

function trigramElementColor(name: string) {
  if (name === "Li") return "text-red-500";
  if (name === "Sun" || name === "Zhen") return "text-emerald-500";
  if (name === "Kan") return "text-blue-500";
  if (name === "Kun" || name === "Gen") return "text-amber-500";
  if (name === "Qian" || name === "Dui") return "text-slate-300";
  return "text-gray-400";
}

function trigramBorderColor(name: string) {
  if (name === "Li") return "border-l-red-500/70";
  if (name === "Sun" || name === "Zhen") return "border-l-emerald-500/70";
  if (name === "Kan") return "border-l-blue-500/70";
  if (name === "Kun" || name === "Gen") return "border-l-amber-500/70";
  if (name === "Qian" || name === "Dui") return "border-l-slate-400/70";
  return "border-l-gray-500/70";
}

const trigramBreakdown = computed(() => {
  const text = selectedHexagram.value?.trigrams ?? "";
  const match = text.match(
    /^Upper:\s*([A-Za-z]+)\s*\(([^)]+)\)\s*\/\s*Lower:\s*([A-Za-z]+)\s*\(([^)]+)\)$/
  );
  if (!match) {
    return {
      upper: { name: "Upper", element: "Unknown", colorClass: "text-gray-400" },
      lower: { name: "Lower", element: "Unknown", colorClass: "text-gray-400" },
    };
  }
  const [, upperName, upperElement, lowerName, lowerElement] = match;
  const safeUpperName = upperName ?? "Upper";
  const safeUpperElement = upperElement ?? "Unknown";
  const safeLowerName = lowerName ?? "Lower";
  const safeLowerElement = lowerElement ?? "Unknown";
  return {
    upper: {
      name: safeUpperName,
      element: safeUpperElement,
      colorClass: trigramElementColor(safeUpperName),
    },
    lower: {
      name: safeLowerName,
      element: safeLowerElement,
      colorClass: trigramElementColor(safeLowerName),
    },
  };
});

const PHILOSOPHY_TO_SUMMARY_KEY: Record<PhilosophyKey, keyof HexagramSummary> = {
  daoism: "daoist",
  confucianism: "confucian",
  buddhism: "buddhist",
  psychology: "psychological",
  humandesign: "humanDesign",
  genekeys: "geneKeys",
};

const lensOptions: Array<{ key: PhilosophyKey; label: string }> = [
  { key: "daoism", label: "Daoism" },
  { key: "confucianism", label: "Confucianism" },
  { key: "buddhism", label: "Buddhism" },
  { key: "psychology", label: "Psychology" },
  { key: "humandesign", label: "Human Design" },
  { key: "genekeys", label: "Gene Keys" },
];

const activePhilosophyDisplay = computed(
  () => PHILOSOPHY_DISPLAY[activePhilosophy.value] ?? "Daoism"
);

const activeSection = computed(() => {
  const summaryKey = PHILOSOPHY_TO_SUMMARY_KEY[activePhilosophy.value];
  const titles: Record<keyof HexagramSummary, string> = {
    daoist: "Daoist (Liu Yiming / Wang Bi)",
    confucian: "Confucian (Ten Wings)",
    buddhist: "Buddhist (Chih-hsui Ou-i)",
    psychological: "Psychological",
    humanDesign: "Human Design",
    geneKeys: "Gene Keys",
  };
  return {
    title: titles[summaryKey] ?? "Daoist",
    text: props.summaries?.[summaryKey] ?? "",
  };
});

const lineBlockBorderClass = computed(() => {
  const line = activeLine.value;
  if (!line) return "border-l-gray-500/70";
  const trigrams = trigramBreakdown.value;
  return line >= 4 ? trigramBorderColor(trigrams.upper.name) : trigramBorderColor(trigrams.lower.name);
});

/** Relating (transformed) hexagram after flipping bits at moving lines. */
const relatingHexagramId = computed(() =>
  getRelatingHexagram(props.hexNum, props.movingLines ?? [])
);

const isActiveLineMoving = computed(
  () => activeLine.value !== null && (props.movingLines ?? []).includes(activeLine.value)
);

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
        <div>
          <div class="hexModalTitle">
            HEXAGRAM #{{ hexNum ?? "?" }} <span class="text-gray-400">•</span>
            <LocalizedScript
              class="hexNameCn"
              :hanzi="hexTraditionalName"
              :scripts="hexagramScripts(hexNum ?? null)"
            />
            <span v-if="selectedHexagram?.englishName" class="hexEnglishName">
              • <span class="text-xl font-bold">{{ selectedHexagram.englishName }}</span>
            </span>
          </div>
          <div class="hexModalLinguistics">
            Pronunciation: <PronunciationText
              :pinyin="selectedHexagram?.pinyinName ?? ''"
              v-bind="hexagramRomans(hexNum ?? null)"
            />
            <span v-if="selectedHexagram?.trigrams"> | {{ selectedHexagram.trigrams }}</span>
          </div>
        </div>
        <button class="btn small" @click="emit('close')">Close</button>
      </div>
      <div class="hexModalBody">
        <button type="button" class="btn small md:hidden" @click="isExploded = !isExploded">
          {{ isExploded ? "Hide Architecture" : "Analyze Architecture" }}
        </button>
        <div
          class="hexDiagramWrap"
          @mouseenter="isExploded = true"
          @mouseleave="isExploded = false"
        >
          <svg
            v-if="hexagramLines.length"
            viewBox="-50 0 290 140"
            class="w-72 h-44 mx-auto text-slate-800 dark:text-slate-200"
            role="img"
            :aria-label="`Hexagram ${hexNum ?? ''} line structure`"
          >
            <g class="transition-opacity duration-500" :class="isExploded ? 'opacity-100' : 'opacity-0'">
              <!-- Inward-facing bracket [ for upper trigram: aligned to line rects (exploded coords) -->
              <path :d="upperBracketPath" fill="none" stroke="currentColor" stroke-width="1.5" />
              <text
                x="34"
                :y="(upperBracketBounds.top - EXPLODE_OFFSET + upperBracketBounds.bottom - EXPLODE_OFFSET) / 2"
                text-anchor="end"
                alignment-baseline="middle"
                font-size="8"
                class="fill-current"
                :class="trigramBreakdown.upper.colorClass"
              >
                {{ trigramBreakdown.upper.name }} ({{ trigramBreakdown.upper.element }})
              </text>
              <!-- Inward-facing bracket [ for lower trigram: aligned to line rects (exploded coords) -->
              <path :d="lowerBracketPath" fill="none" stroke="currentColor" stroke-width="1.5" />
              <text
                x="34"
                :y="(lowerBracketBounds.top + EXPLODE_OFFSET + lowerBracketBounds.bottom + EXPLODE_OFFSET) / 2"
                text-anchor="end"
                alignment-baseline="middle"
                font-size="8"
                class="fill-current"
                :class="trigramBreakdown.lower.colorClass"
              >
                {{ trigramBreakdown.lower.name }} ({{ trigramBreakdown.lower.element }})
              </text>
            </g>

            <g
              class="transition-transform duration-500 ease-out"
              :class="isExploded ? 'translate-y-[-16px]' : ''"
            >
              <g
                v-for="line in upperTrigramLines"
                :key="`upper-${line.id}`"
                class="cursor-pointer hover:opacity-75 transition-opacity"
                :class="(props.movingLines ?? []).includes(line.lineNumber) ? 'lineMutating' : ''"
                @click="onLineClick(line.lineNumber)"
              >
                <rect
                  v-if="line.isYang"
                  x="72"
                  :y="line.y"
                  width="84"
                  height="8"
                  rx="1.5"
                  class="fill-current"
                />
                <template v-else>
                  <rect x="72" :y="line.y" width="34" height="8" rx="1.5" class="fill-current" />
                  <rect x="122" :y="line.y" width="34" height="8" rx="1.5" class="fill-current" />
                </template>
                <text
                  x="182"
                  :y="line.y + 6"
                  text-anchor="start"
                  font-size="8"
                  class="fill-current transition-opacity duration-500"
                  :class="isExploded ? 'opacity-100' : 'opacity-0'"
                >
                  {{ line.label }}
                </text>
              </g>
            </g>

            <g
              class="transition-transform duration-500 ease-out"
              :class="isExploded ? 'translate-y-[16px]' : ''"
            >
              <g
                v-for="line in lowerTrigramLines"
                :key="`lower-${line.id}`"
                class="cursor-pointer hover:opacity-75 transition-opacity"
                :class="(props.movingLines ?? []).includes(line.lineNumber) ? 'lineMutating' : ''"
                @click="onLineClick(line.lineNumber)"
              >
                <rect
                  v-if="line.isYang"
                  x="72"
                  :y="line.y"
                  width="84"
                  height="8"
                  rx="1.5"
                  class="fill-current"
                />
                <template v-else>
                  <rect x="72" :y="line.y" width="34" height="8" rx="1.5" class="fill-current" />
                  <rect x="122" :y="line.y" width="34" height="8" rx="1.5" class="fill-current" />
                </template>
                <text
                  x="182"
                  :y="line.y + 6"
                  text-anchor="start"
                  font-size="8"
                  class="fill-current transition-opacity duration-500"
                  :class="isExploded ? 'opacity-100' : 'opacity-0'"
                >
                  {{ line.label }}
                </text>
              </g>
            </g>
          </svg>
        </div>

        <div class="lensToggleWrap">
          <button
            v-for="lens in lensOptions"
            :key="lens.key"
            type="button"
            class="lensToggle transition-all duration-300"
            :class="activePhilosophy === lens.key ? 'lensToggleActive scale-110' : 'hover:scale-105'"
            @click="activePhilosophy = lens.key"
          >
            <PhilosophyIcon :system="lens.key" />
            <span>{{ lens.label }}</span>
          </button>
        </div>

        <div class="hexModalSection">
          <div class="hexModalSectionTitle">{{ activeSection.title }}</div>
          <div class="hexModalSectionText">
            {{
              activeSection.text && activeSection.text.trim().length
                ? activeSection.text
                : "Summary pending."
            }}
          </div>
        </div>

        <div
          v-if="activeLine"
          class="lineAnalysisBlock border-l-4"
          :class="lineBlockBorderClass"
        >
          <div class="lineAnalysisBlockHeader">
            Line {{ activeLine }} • {{ activePhilosophyDisplay }} Analysis
          </div>
          <div class="lineAnalysisBlockText">
            {{ activeLineText ?? `Line ${activeLine} ${activePhilosophyDisplay} analysis is coming soon.` }}
          </div>
          <button
            v-if="isActiveLineMoving && relatingHexagramId"
            type="button"
            class="btn mt-4 w-full font-semibold py-3 mutationBridgeBtn"
            @click="emit('viewHexagram', relatingHexagramId)"
          >
            View Transformed Hexagram
          </button>
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
  background: rgba(0, 0, 0, 0.9);
  border: 1px solid var(--b2);
  border-radius: 14px;
  padding: 16px;
  display: grid;
  gap: 12px;
}
.hexModalHeader {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.hexModalTitle {
  font-size: 14px;
  letter-spacing: 0.4px;
  color: var(--muted);
}
.hexNameCn {
  font-size: 18px;
  text-transform: none;
}
.hexEnglishName {
  margin-left: 4px;
  text-transform: none;
}
.hexModalLinguistics {
  margin-top: 4px;
  font-size: 12px;
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
  background: rgba(0, 0, 0, 0.2);
}
.hexDiagramWrap {
  display: grid;
  place-items: center;
}
.lensToggleWrap {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.lensToggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid var(--b);
  border-radius: 10px;
  padding: 8px 6px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.02);
  color: var(--muted);
}
.lineAnalysisBlock {
  border-radius: 12px;
  padding: 12px 14px;
  background: rgba(0, 0, 0, 0.35);
  box-shadow: 0 0 0.5rem rgba(148, 163, 184, 0.12);
}
.lineAnalysisBlockHeader {
  font-size: 12px;
  font-weight: 600;
  color: var(--tx);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.lineAnalysisBlockText {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--muted);
}
.lensToggleActive {
  color: var(--tx);
  border-color: var(--b2);
  box-shadow: 0 0 0.75rem rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.08);
}
.lensToggleActive :deep(svg) {
  filter: drop-shadow(0 0 0.3rem rgba(148, 163, 184, 0.55));
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
.lineMutating :deep(rect),
:deep(rect.lineMutating) {
  stroke: rgb(251 191 36);
  stroke-width: 2;
  filter: drop-shadow(0 0 6px rgba(251, 191, 36, 0.7));
}
.mutationBridgeBtn {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(251, 191, 36, 0.05));
  border-color: rgba(251, 191, 36, 0.5);
  color: rgb(251 191 36);
}
.mutationBridgeBtn:hover {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.25), rgba(251, 191, 36, 0.1));
  border-color: rgba(251, 191, 36, 0.8);
}
</style>
