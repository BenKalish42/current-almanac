<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import CosmicBoard from "@/components/CosmicBoard.vue";
import HexagramLines from "@/components/HexagramLines.vue";
import HexagramModal from "@/components/HexagramModal.vue";
import OrganHourCard from "@/components/astrology/OrganHourCard.vue";
import PillarBounds from "@/components/astrology/PillarBounds.vue";
import LocationAutocomplete from "@/components/ui/LocationAutocomplete.vue";
import PronunciationText from "@/components/ui/PronunciationText.vue";
import { parseGanZhi } from "@/core/ganzhi";
import { hasLlmKey } from "@/services/llmService";
import { useAppStore } from "@/stores/appStore";
import { getTrueSolarTime } from "@/utils/solarTime";
import seedHexagrams from "@/data/seed_hexagrams.json";

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
      daoist: h.perspectives.daoist ?? "",
      confucian: h.perspectives.confucian ?? "",
      buddhist: h.perspectives.buddhist ?? "",
      psychological: h.perspectives.psychological ?? "",
      humanDesign: h.perspectives.human_design ?? "",
      geneKeys: h.perspectives.gene_keys ?? "",
    };
  }
  return map;
}

const store = useAppStore();
const hexSummaryMap = buildHexSummaryMap(seedHexagrams as SeedHexagram[]);

/** Hex num → { english_name, pinyin_name, jyutping_name, zhuyin_name, taigi_name } for BaZi hexagram labels (Task 12.3/12.3b) */
type HexLabel = { english_name: string; pinyin_name: string; jyutping_name?: string; zhuyin_name?: string; taigi_name?: string };
const hexLabelMap: Record<number, HexLabel> = {};
for (const h of seedHexagrams as SeedHexagram[]) {
  const sh = h as SeedHexagram & { jyutping_name?: string; zhuyin_name?: string; taigi_name?: string };
  hexLabelMap[h.id] = {
    english_name: h.english_name ?? "",
    pinyin_name: h.pinyin_name ?? "",
    jyutping_name: sh.jyutping_name,
    zhuyin_name: sh.zhuyin_name,
    taigi_name: sh.taigi_name,
  };
}

function hexLabel(num: number | null) {
  return num ? hexLabelMap[num] ?? null : null;
}

/** Show Current Flow block only when we have real analysis — never API key hints. */
const advancedExpanded = ref(false);
/** Birth reference date for PillarBounds. Solar-adjusted when useTrueSolarTime && birthLongitude. */
const birthReferenceDate = computed(() => {
  const raw = store.birthDatetimeLocal;
  if (!raw || !raw.includes("T")) return new Date();
  try {
    const d = new Date(raw.replace(/:\d{2}$/, ":00"));
    if (Number.isNaN(d.getTime())) return new Date();
    if (store.useTrueSolarTime && store.birthLongitude != null) {
      return getTrueSolarTime(d, store.birthLongitude);
    }
    return d;
  } catch {
    return new Date();
  }
});

const displayableCurrentFlow = computed(() => {
  const t = store.currentFlowAnalysis;
  if (!t?.trim()) return null;
  if (t.includes("VITE_DEEPSEEK") || t.includes("VITE_LLM") || t.includes("API_KEY") || t.includes(".env"))
    return null;
  return t;
});

const isHexModalOpen = ref(false);
const selectedHexNum = ref<number | null>(null);
const selectedHexNameCn = ref<string | null>(null);
const selectedMovingLines = ref<number[]>([]);
const selectedHexSummary = computed(() => {
  const num = selectedHexNum.value;
  if (!num) return null;
  return hexSummaryMap[String(num)] ?? null;
});
const selectedHexDisplayName = computed(
  () => hexNameShort(selectedHexNum.value, selectedHexNameCn.value) || "—"
);

const HEX_NAME_CN_SHORT: string[] = [
  "", "乾", "坤", "屯", "蒙", "需", "讼", "师", "比", "小畜", "履", "泰", "否",
  "同人", "大有", "谦", "豫", "随", "蛊", "临", "观", "噬嗑", "贲", "剥", "复",
  "无妄", "大畜", "颐", "大过", "坎", "离", "咸", "恒", "遯", "大壮", "晋", "明夷",
  "家人", "睽", "蹇", "解", "损", "益", "夬", "姤", "萃", "升", "困", "井", "革",
  "鼎", "震", "艮", "渐", "归妹", "丰", "旅", "巽", "兑", "涣", "节", "中孚",
  "小过", "既济", "未济",
];

function hexNameShort(num: number | null, fallback: string | null) {
  if (!num || num < 1 || num >= HEX_NAME_CN_SHORT.length) return fallback ?? "—";
  return HEX_NAME_CN_SHORT[num];
}

function openHexModal(hex: { num: number | null; nameCn: string | null; movingLines?: number[] }) {
  if (!hex?.num) return;
  selectedHexNum.value = hex.num;
  selectedHexNameCn.value = hex.nameCn ?? null;
  selectedMovingLines.value = hex.movingLines ?? [];
  isHexModalOpen.value = true;
}

function onViewHexagram(id: number) {
  selectedHexNum.value = id;
  selectedMovingLines.value = []; // Transformed hex has no moving lines in this view
}

function closeHexModal() {
  isHexModalOpen.value = false;
}

function formatGanZhiLines(gz: string | null) {
  const parsed = parseGanZhi(gz ?? "");
  if (!parsed.stem || !parsed.branch) return gz ?? "—";
  const chars = `${parsed.stem.char}${parsed.branch.char}`;
  const english = `${parsed.stem.element} ${parsed.stem.yinYang} ${parsed.branch.animal}`;
  const emojis = `${parsed.stem.elementEmoji}${parsed.stem.yinYangEmoji}${parsed.branch.animalEmoji}`;
  return `${chars}\n${english}\n${emojis}`;
}

function getLocalTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "unknown";
}

async function copyCurrentFlow() {
  const text = store.currentFlowAnalysis;
  if (!text) return;
  await navigator.clipboard.writeText(text);
}

let localSyncTimer: number | null = null;

onMounted(() => {
  store.loadFromStorage();
  store.syncLocalTimeNow(true);
  store.timezoneLabel = getLocalTimezone();
  void store.hydrateFromGeolocation();
  localSyncTimer = window.setInterval(() => {
    store.syncLocalTimeNow();
    store.timezoneLabel = getLocalTimezone();
  }, 60_000);
  // Initial run after load (watchers may have run before loadFromStorage)
  queueMicrotask(() => {
    void store.requestPastSummary();
    void store.requestPresentSummary();
  });
});

// Task 12.2: Auto-generate baseline summaries when BaZi changes (debounced)
let pastDebounce: ReturnType<typeof setTimeout> | null = null;
let presentDebounce: ReturnType<typeof setTimeout> | null = null;
const DEBOUNCE_MS = 1200;

// Past: re-run when birth BaZi pillars change (birth datetime edit)
watch(
  () => store.pastBaziSignature,
  () => {
    if (pastDebounce) clearTimeout(pastDebounce);
    pastDebounce = setTimeout(() => {
      void store.requestPastSummary();
      pastDebounce = null;
    }, DEBOUNCE_MS);
  },
  { immediate: true }
);

// Present: re-run only when present BaZi pillars change (e.g. new 2h organ block), not every minute
watch(
  () => store.presentBaziSignature,
  () => {
    if (presentDebounce) clearTimeout(presentDebounce);
    presentDebounce = setTimeout(() => {
      void store.requestPresentSummary();
      presentDebounce = null;
    }, DEBOUNCE_MS);
  },
  { immediate: true }
);

onUnmounted(() => {
  if (localSyncTimer) window.clearInterval(localSyncTimer);
  if (pastDebounce) clearTimeout(pastDebounce);
  if (presentDebounce) clearTimeout(presentDebounce);
});
</script>

<template>
  <div class="appRoot">
    <div class="appHeader">
      <div class="headerLeft">
        <div class="title">Current (v0)</div>
        <div class="subtitle">You're in the Present... Would you like to get in the Current?</div>
        <div class="sub">Stored locally. No accounts. Descriptive only.</div>
      </div>
      <div class="headerRight">
        <label class="dialectLbl">
          Preferred Dialect
          <select class="dialectSelect" v-model="store.preferredDialect">
            <option value="pinyin">Mandarin (Pinyin)</option>
            <option value="jyutping">Cantonese (Jyutping)</option>
            <option value="zhuyin">Taiwanese (Zhuyin)</option>
            <option value="taigi">Taiwanese (Taigi)</option>
          </select>
        </label>
      </div>
    </div>

    <!-- Active Meridian: extracted to top for mobile, visible without scrolling -->
    <div class="activeMeridianSection">
      <OrganHourCard />
    </div>

    <div class="wrap">
      <main class="main">
        <div class="card">
          <div class="topSections">
            <section class="panel">
              <div class="panelHeader">
                <div class="secTitle">Past (Birth)</div>
                <div class="panelControls">
                  <label class="inlineLbl">
                    Birth datetime
                    <input class="input inlineInput" type="datetime-local" v-model="store.birthDatetimeLocal" />
                  </label>
                  <label class="inlineLbl">
                    Birth location
                    <LocationAutocomplete v-model:locationName="store.birthLocationName" v-model:longitude="store.birthLongitude" />
                  </label>
                  <label class="inlineLbl">
                    BaZi sect
                    <select class="input inlineInput inlineSelect" v-model.number="store.birthSect">
                      <option :value="1">sect 1</option>
                      <option :value="2">sect 2</option>
                    </select>
                  </label>
                </div>
              </div>
              <div v-if="store.birthTemporalHex" class="pillarGrid">
                <div class="pillarBox">
                  <div class="pillarLabel">Year</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.birthTemporalHex.year.ganzhi) }}</div>
                  <PillarBounds pillar-type="year" :pillar="store.birthTemporalHex.year" :reference-date="birthReferenceDate" :use-true-solar-time="!!(store.useTrueSolarTime && store.birthLongitude != null)" :date-format="store.dateFormat" />
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.birthTemporalHex.year.hex.num }"
                    role="button"
                    :tabindex="store.birthTemporalHex.year.hex.num ? 0 : -1"
                    :aria-disabled="!store.birthTemporalHex.year.hex.num"
                    @click="openHexModal(store.birthTemporalHex.year.hex)"
                    @keydown.enter.prevent="openHexModal(store.birthTemporalHex.year.hex)"
                    @keydown.space.prevent="openHexModal(store.birthTemporalHex.year.hex)"
                  >
                    <div class="hexTop">{{ hexLabel(store.birthTemporalHex.year.hex.num)?.english_name || "—" }}</div>
                    <div class="hexRow">
                      <div class="hexNum">#{{ store.birthTemporalHex.year.hex.num ?? "—" }}</div>
                      <HexagramLines :binary="store.birthTemporalHex.year.hex.binary" size="sm" />
                      <div class="hexRight">
                        <div class="hexName cjkText">{{ hexNameShort(store.birthTemporalHex.year.hex.num ?? null, store.birthTemporalHex.year.hex.nameCn) }}</div>
                        <div class="hexPinyin">
                          <PronunciationText
                            :pinyin="hexLabel(store.birthTemporalHex.year.hex.num)?.pinyin_name || ''"
                            :jyutping="hexLabel(store.birthTemporalHex.year.hex.num)?.jyutping_name"
                            :zhuyin="hexLabel(store.birthTemporalHex.year.hex.num)?.zhuyin_name"
                            :taigi="hexLabel(store.birthTemporalHex.year.hex.num)?.taigi_name"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Month</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.birthTemporalHex.month.ganzhi) }}</div>
                  <PillarBounds pillar-type="month" :pillar="store.birthTemporalHex.month" :reference-date="birthReferenceDate" :use-true-solar-time="!!(store.useTrueSolarTime && store.birthLongitude != null)" :date-format="store.dateFormat" />
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.birthTemporalHex.month.hex.num }"
                    role="button"
                    :tabindex="store.birthTemporalHex.month.hex.num ? 0 : -1"
                    :aria-disabled="!store.birthTemporalHex.month.hex.num"
                    @click="openHexModal(store.birthTemporalHex.month.hex)"
                    @keydown.enter.prevent="openHexModal(store.birthTemporalHex.month.hex)"
                    @keydown.space.prevent="openHexModal(store.birthTemporalHex.month.hex)"
                  >
                    <div class="hexTop">{{ hexLabel(store.birthTemporalHex.month.hex.num)?.english_name || "—" }}</div>
                    <div class="hexRow">
                      <div class="hexNum">#{{ store.birthTemporalHex.month.hex.num ?? "—" }}</div>
                      <HexagramLines :binary="store.birthTemporalHex.month.hex.binary" size="sm" />
                      <div class="hexRight">
                        <div class="hexName cjkText">{{ hexNameShort(store.birthTemporalHex.month.hex.num ?? null, store.birthTemporalHex.month.hex.nameCn) }}</div>
                        <div class="hexPinyin">
                          <PronunciationText
                            :pinyin="hexLabel(store.birthTemporalHex.month.hex.num)?.pinyin_name || ''"
                            :jyutping="hexLabel(store.birthTemporalHex.month.hex.num)?.jyutping_name"
                            :zhuyin="hexLabel(store.birthTemporalHex.month.hex.num)?.zhuyin_name"
                            :taigi="hexLabel(store.birthTemporalHex.month.hex.num)?.taigi_name"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Day</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.birthTemporalHex.day.ganzhi) }}</div>
                  <PillarBounds pillar-type="day" :pillar="store.birthTemporalHex.day" :reference-date="birthReferenceDate" :use-true-solar-time="!!(store.useTrueSolarTime && store.birthLongitude != null)" :date-format="store.dateFormat" />
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.birthTemporalHex.day.hex.num }"
                    role="button"
                    :tabindex="store.birthTemporalHex.day.hex.num ? 0 : -1"
                    :aria-disabled="!store.birthTemporalHex.day.hex.num"
                    @click="openHexModal(store.birthTemporalHex.day.hex)"
                    @keydown.enter.prevent="openHexModal(store.birthTemporalHex.day.hex)"
                    @keydown.space.prevent="openHexModal(store.birthTemporalHex.day.hex)"
                  >
                    <div class="hexTop">{{ hexLabel(store.birthTemporalHex.day.hex.num)?.english_name || "—" }}</div>
                    <div class="hexRow">
                      <div class="hexNum">#{{ store.birthTemporalHex.day.hex.num ?? "—" }}</div>
                      <HexagramLines :binary="store.birthTemporalHex.day.hex.binary" size="sm" />
                      <div class="hexRight">
                        <div class="hexName cjkText">{{ hexNameShort(store.birthTemporalHex.day.hex.num ?? null, store.birthTemporalHex.day.hex.nameCn) }}</div>
                        <div class="hexPinyin">
                          <PronunciationText
                            :pinyin="hexLabel(store.birthTemporalHex.day.hex.num)?.pinyin_name || ''"
                            :jyutping="hexLabel(store.birthTemporalHex.day.hex.num)?.jyutping_name"
                            :zhuyin="hexLabel(store.birthTemporalHex.day.hex.num)?.zhuyin_name"
                            :taigi="hexLabel(store.birthTemporalHex.day.hex.num)?.taigi_name"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Hour</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.birthTemporalHex.hour.ganzhi) }}</div>
                  <PillarBounds pillar-type="hour" :pillar="store.birthTemporalHex.hour" :reference-date="birthReferenceDate" :use-true-solar-time="!!(store.useTrueSolarTime && store.birthLongitude != null)" :date-format="store.dateFormat" />
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.birthTemporalHex.hour.hex.num }"
                    role="button"
                    :tabindex="store.birthTemporalHex.hour.hex.num ? 0 : -1"
                    :aria-disabled="!store.birthTemporalHex.hour.hex.num"
                    @click="openHexModal(store.birthTemporalHex.hour.hex)"
                    @keydown.enter.prevent="openHexModal(store.birthTemporalHex.hour.hex)"
                    @keydown.space.prevent="openHexModal(store.birthTemporalHex.hour.hex)"
                  >
                    <div class="hexTop">{{ hexLabel(store.birthTemporalHex.hour.hex.num)?.english_name || "—" }}</div>
                    <div class="hexRow">
                      <div class="hexNum">#{{ store.birthTemporalHex.hour.hex.num ?? "—" }}</div>
                      <HexagramLines :binary="store.birthTemporalHex.hour.hex.binary" size="sm" />
                      <div class="hexRight">
                        <div class="hexName cjkText">{{ hexNameShort(store.birthTemporalHex.hour.hex.num ?? null, store.birthTemporalHex.hour.hex.nameCn) }}</div>
                        <div class="hexPinyin">
                          <PronunciationText
                            :pinyin="hexLabel(store.birthTemporalHex.hour.hex.num)?.pinyin_name || ''"
                            :jyutping="hexLabel(store.birthTemporalHex.hour.hex.num)?.jyutping_name"
                            :zhuyin="hexLabel(store.birthTemporalHex.hour.hex.num)?.zhuyin_name"
                            :taigi="hexLabel(store.birthTemporalHex.hour.hex.num)?.taigi_name"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="meta">Enter a valid birth datetime.</div>
              <div v-if="store.pastSummaryLoading" class="baselineSummary baselineSummaryHint">
                <p class="baselineSummaryText">Generating summary…</p>
              </div>
              <div v-else-if="store.pastSummary" class="baselineSummary">
                <div class="baselineSummaryLabel">Past Summary</div>
                <p class="baselineSummaryText">{{ store.pastSummary }}</p>
              </div>
              <div v-else-if="!hasLlmKey() && store.birthTemporalHex" class="baselineSummary baselineSummaryHint">
                <p class="baselineSummaryText">Add VITE_DEEPSEEK_API_KEY or VITE_LLM_API_KEY to .env and restart to see summaries.</p>
              </div>
            </section>

            <section class="panel">
              <div class="panelHeader">
                <div>
                  <div class="secTitle">Present (Moment)</div>
                  <div class="organLine">Organ: <strong>{{ store.presentOrgan }}</strong></div>
                </div>
                <div class="panelControls">
                  <input class="input inlineInput" type="datetime-local" v-model="store.presentDatetimeLocal" />
                  <button class="btn small" :class="{ primary: store.presentAuto }" @click="store.togglePresentAuto">Auto {{ store.presentAuto ? "On" : "Off" }}</button>
                  <button class="btn small" @click="store.shiftPresentHours(-2)">◀</button>
                  <button class="btn small" @click="store.shiftPresentHours(2)">▶</button>
                </div>
              </div>
              <div class="pillarGrid">
                <div class="pillarBox">
                  <div class="pillarLabel">Year</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.temporalHex.year.ganzhi) }}</div>
                  <PillarBounds pillar-type="year" :pillar="store.temporalHex.year" :reference-date="store.solarAdjustedSelectedDate" :use-true-solar-time="store.useTrueSolarTime" :date-format="store.dateFormat" />
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.temporalHex.year.hex.num }"
                    role="button"
                    :tabindex="store.temporalHex.year.hex.num ? 0 : -1"
                    :aria-disabled="!store.temporalHex.year.hex.num"
                    @click="openHexModal(store.temporalHex.year.hex)"
                    @keydown.enter.prevent="openHexModal(store.temporalHex.year.hex)"
                    @keydown.space.prevent="openHexModal(store.temporalHex.year.hex)"
                  >
                    <div class="hexTop">{{ hexLabel(store.temporalHex.year.hex.num)?.english_name || "—" }}</div>
                    <div class="hexRow">
                      <div class="hexNum">#{{ store.temporalHex.year.hex.num ?? "—" }}</div>
                      <HexagramLines :binary="store.temporalHex.year.hex.binary" size="sm" />
                      <div class="hexRight">
                        <div class="hexName cjkText">{{ hexNameShort(store.temporalHex.year.hex.num ?? null, store.temporalHex.year.hex.nameCn) }}</div>
                        <div class="hexPinyin">
                          <PronunciationText
                            :pinyin="hexLabel(store.temporalHex.year.hex.num)?.pinyin_name || ''"
                            :jyutping="hexLabel(store.temporalHex.year.hex.num)?.jyutping_name"
                            :zhuyin="hexLabel(store.temporalHex.year.hex.num)?.zhuyin_name"
                            :taigi="hexLabel(store.temporalHex.year.hex.num)?.taigi_name"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Month</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.temporalHex.month.ganzhi) }}</div>
                  <PillarBounds pillar-type="month" :pillar="store.temporalHex.month" :reference-date="store.solarAdjustedSelectedDate" :use-true-solar-time="store.useTrueSolarTime" :date-format="store.dateFormat" />
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.temporalHex.month.hex.num }"
                    role="button"
                    :tabindex="store.temporalHex.month.hex.num ? 0 : -1"
                    :aria-disabled="!store.temporalHex.month.hex.num"
                    @click="openHexModal(store.temporalHex.month.hex)"
                    @keydown.enter.prevent="openHexModal(store.temporalHex.month.hex)"
                    @keydown.space.prevent="openHexModal(store.temporalHex.month.hex)"
                  >
                    <div class="hexTop">{{ hexLabel(store.temporalHex.month.hex.num)?.english_name || "—" }}</div>
                    <div class="hexRow">
                      <div class="hexNum">#{{ store.temporalHex.month.hex.num ?? "—" }}</div>
                      <HexagramLines :binary="store.temporalHex.month.hex.binary" size="sm" />
                      <div class="hexRight">
                        <div class="hexName cjkText">{{ hexNameShort(store.temporalHex.month.hex.num ?? null, store.temporalHex.month.hex.nameCn) }}</div>
                        <div class="hexPinyin">
                          <PronunciationText
                            :pinyin="hexLabel(store.temporalHex.month.hex.num)?.pinyin_name || ''"
                            :jyutping="hexLabel(store.temporalHex.month.hex.num)?.jyutping_name"
                            :zhuyin="hexLabel(store.temporalHex.month.hex.num)?.zhuyin_name"
                            :taigi="hexLabel(store.temporalHex.month.hex.num)?.taigi_name"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Day</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.temporalHex.day.ganzhi) }}</div>
                  <PillarBounds pillar-type="day" :pillar="store.temporalHex.day" :reference-date="store.solarAdjustedSelectedDate" :use-true-solar-time="store.useTrueSolarTime" :date-format="store.dateFormat" />
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.temporalHex.day.hex.num }"
                    role="button"
                    :tabindex="store.temporalHex.day.hex.num ? 0 : -1"
                    :aria-disabled="!store.temporalHex.day.hex.num"
                    @click="openHexModal(store.temporalHex.day.hex)"
                    @keydown.enter.prevent="openHexModal(store.temporalHex.day.hex)"
                    @keydown.space.prevent="openHexModal(store.temporalHex.day.hex)"
                  >
                    <div class="hexTop">{{ hexLabel(store.temporalHex.day.hex.num)?.english_name || "—" }}</div>
                    <div class="hexRow">
                      <div class="hexNum">#{{ store.temporalHex.day.hex.num ?? "—" }}</div>
                      <HexagramLines :binary="store.temporalHex.day.hex.binary" size="sm" />
                      <div class="hexRight">
                        <div class="hexName cjkText">{{ hexNameShort(store.temporalHex.day.hex.num ?? null, store.temporalHex.day.hex.nameCn) }}</div>
                        <div class="hexPinyin">
                          <PronunciationText
                            :pinyin="hexLabel(store.temporalHex.day.hex.num)?.pinyin_name || ''"
                            :jyutping="hexLabel(store.temporalHex.day.hex.num)?.jyutping_name"
                            :zhuyin="hexLabel(store.temporalHex.day.hex.num)?.zhuyin_name"
                            :taigi="hexLabel(store.temporalHex.day.hex.num)?.taigi_name"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Hour</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.temporalHex.hour.ganzhi) || "—" }}</div>
                  <PillarBounds pillar-type="hour" :pillar="store.temporalHex.hour" :reference-date="store.solarAdjustedSelectedDate" :use-true-solar-time="store.useTrueSolarTime" :date-format="store.dateFormat" />
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.temporalHex.hour.hex.num }"
                    role="button"
                    :tabindex="store.temporalHex.hour.hex.num ? 0 : -1"
                    :aria-disabled="!store.temporalHex.hour.hex.num"
                    @click="openHexModal(store.temporalHex.hour.hex)"
                    @keydown.enter.prevent="openHexModal(store.temporalHex.hour.hex)"
                    @keydown.space.prevent="openHexModal(store.temporalHex.hour.hex)"
                  >
                    <div class="hexTop">{{ hexLabel(store.temporalHex.hour.hex.num)?.english_name || "—" }}</div>
                    <div class="hexRow">
                      <div class="hexNum">#{{ store.temporalHex.hour.hex.num ?? "—" }}</div>
                      <HexagramLines :binary="store.temporalHex.hour.hex.binary" size="sm" />
                      <div class="hexRight">
                        <div class="hexName cjkText">{{ hexNameShort(store.temporalHex.hour.hex.num ?? null, store.temporalHex.hour.hex.nameCn) }}</div>
                        <div class="hexPinyin">
                          <PronunciationText
                            :pinyin="hexLabel(store.temporalHex.hour.hex.num)?.pinyin_name || ''"
                            :jyutping="hexLabel(store.temporalHex.hour.hex.num)?.jyutping_name"
                            :zhuyin="hexLabel(store.temporalHex.hour.hex.num)?.zhuyin_name"
                            :taigi="hexLabel(store.temporalHex.hour.hex.num)?.taigi_name"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="store.presentSummaryLoading" class="baselineSummary baselineSummaryHint">
                <p class="baselineSummaryText">Generating summary…</p>
              </div>
              <div v-else-if="store.presentSummary" class="baselineSummary">
                <div class="baselineSummaryLabel">Present Summary</div>
                <p class="baselineSummaryText">{{ store.presentSummary }}</p>
              </div>
              <div v-else-if="!hasLlmKey()" class="baselineSummary baselineSummaryHint">
                <p class="baselineSummaryText">Add VITE_DEEPSEEK_API_KEY or VITE_LLM_API_KEY to .env and restart to see summaries.</p>
              </div>
            </section>
          </div>

          <!-- Current Flow: Generate button + analysis -->
          <div class="sec currentFlowSec">
            <button
              type="button"
              class="btn primary currentFlowBtn"
              :disabled="store.currentFlowLoading"
              @click="store.requestCurrentFlowAnalysis()"
            >
              {{ store.currentFlowLoading ? "Synthesizing…" : "🌊 Generate Current Flow Analysis" }}
            </button>

            <div v-if="store.currentFlowLoading" class="currentFlowBlock currentFlowLoading">
              <p class="currentFlowMeta">Synthesizing…</p>
            </div>

            <div v-else-if="displayableCurrentFlow" class="currentFlowBlock">
              <div class="currentFlowHeader">
                <span class="currentFlowLabel">Current Flow</span>
                <span class="currentFlowMeta">{{ store.presentDatetimeLocal }} · {{ store.location || "location unspecified" }}</span>
              </div>
              <div class="currentFlowText">{{ store.currentFlowAnalysis }}</div>
              <div class="currentFlowActions">
                <button class="btn small" @click="copyCurrentFlow">Copy</button>
              </div>
            </div>

            <div v-else class="currentFlowBlock currentFlowHint">
              <p class="currentFlowMeta" v-if="hasLlmKey()">Click above to synthesize your Birth chart, the Moment's chart, and the Active Meridian.</p>
              <p class="currentFlowMeta" v-else>Add VITE_DEEPSEEK_API_KEY or VITE_LLM_API_KEY to .env and restart the dev server to enable synthesis.</p>
            </div>

            <div class="advanced-wrapper" style="margin-top: 16px;">
              <button
                type="button"
                class="advanced-toggle"
                :aria-expanded="advancedExpanded"
                @click="advancedExpanded = !advancedExpanded"
              >
                <span class="advanced-toggle-label">Advanced ⚙️</span>
                <span class="advanced-toggle-icon" :class="{ expanded: advancedExpanded }">▼</span>
              </button>
              <Transition name="advanced-slide">
                <div v-if="advancedExpanded" class="advanced-content">
                  <label class="advanced-option">
                    <input
                      type="checkbox"
                      v-model="store.useTrueSolarTime"
                      :disabled="store.longitude === null"
                    />
                    <span>Enable True Solar Time <span v-if="store.longitude === null" class="muted">(Requires Longitude)</span></span>
                  </label>
                  <label class="advanced-option">
                    Date Format
                    <select class="input inlineInput inlineSelect" v-model="store.dateFormat">
                      <option value="US">US (MM/DD/YYYY)</option>
                      <option value="EU">EU (DD/MM/YYYY)</option>
                      <option value="ASIAN">Asian (YYYY/MM/DD)</option>
                    </select>
                  </label>
                  <CosmicBoard
                    :qimen-chart-hour="store.qimenChartHour"
                    :qimen-chart-day="store.qimenChartDay"
                    :selected-date="store.selectedDate"
                  />
                </div>
              </Transition>
            </div>
          </div>

          <div class="sec">
            <div class="secTitle">Future (Destiny)</div>
            <div class="secBody">
              <textarea
                class="destinyBox"
                placeholder="Destiny is yours to write."
                v-model="store.generatedReading"
                :readonly="store.isGenerating"
              ></textarea>
            </div>
          </div>
        </div>
      </main>

      <HexagramModal
        :open="isHexModalOpen"
        :hex-num="selectedHexNum"
        :hex-name="selectedHexDisplayName"
        :summaries="selectedHexSummary"
        :moving-lines="selectedMovingLines"
        @close="closeHexModal"
        @view-hexagram="onViewHexagram"
      />
    </div>
  </div>
</template>

<style scoped>
.activeMeridianSection {
  margin-bottom: 16px;
  padding: 0 18px;
}

@media (max-width: 680px) {
  .activeMeridianSection {
    padding-left: 12px;
    padding-right: 12px;
  }
}

.advanced-wrapper {
  border-top: 1px solid var(--b2);
  padding-top: 10px;
}

.advanced-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  background: none;
  border: none;
  color: var(--muted);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: color 0.2s;
}

.advanced-toggle:hover {
  color: var(--txt);
}

.advanced-toggle-icon {
  display: inline-block;
  font-size: 10px;
  transition: transform 0.2s;
}

.advanced-toggle-icon.expanded {
  transform: rotate(180deg);
}

.advanced-content {
  margin-top: 8px;
}

.advanced-option {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
  cursor: pointer;
}
.advanced-option input {
  flex-shrink: 0;
}
.advanced-option .muted {
  color: var(--muted, rgba(255, 255, 255, 0.55));
  font-size: 12px;
}

.advanced-option {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
  cursor: pointer;
}
.advanced-option input[type="checkbox"] {
  margin: 0;
}
.advanced-option .muted {
  color: var(--muted, rgba(255, 255, 255, 0.5));
  font-size: 12px;
}

.advanced-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 13px;
  color: var(--txt);
}
.advanced-option input[type="checkbox"] {
  margin: 0;
}
.advanced-option .muted {
  color: var(--muted, rgba(255, 255, 255, 0.55));
  font-size: 12px;
}

.advanced-slide-enter-active,
.advanced-slide-leave-active {
  transition: opacity 0.2s ease, margin 0.2s ease;
}

.advanced-slide-enter-from,
.advanced-slide-leave-to {
  opacity: 0;
  margin-top: -8px;
}

/* Task 12.2: Oracle Engine — baseline summaries & Current Flow */
.baselineSummary {
  margin-top: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  border: 1px solid var(--b2);
}
.baselineSummaryLabel {
  font-size: 11px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 6px;
}
.baselineSummaryText {
  font-size: 13px;
  line-height: 1.5;
  color: var(--txt);
  margin: 0;
}

.currentFlowSec {
  margin-top: 24px;
}
.currentFlowBtn {
  width: 100%;
  padding: 16px 24px;
  font-size: 16px;
  font-weight: 700;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(0, 120, 140, 0.4), rgba(0, 80, 100, 0.5));
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: transform 0.15s, opacity 0.15s;
}
.currentFlowBtn:hover:not(:disabled) {
  transform: translateY(-1px);
  opacity: 0.95;
}
.currentFlowBlock {
  margin-top: 16px;
  padding: 18px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 12px;
  border: 1px solid var(--b2);
}
.currentFlowLabel {
  font-size: 12px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 10px;
}
.currentFlowText {
  font-size: 15px;
  line-height: 1.6;
  color: var(--txt);
  white-space: pre-wrap;
}
</style>

