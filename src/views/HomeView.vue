<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import AstrologyCrawlBackdrop from "@/components/AstrologyCrawlBackdrop.vue";
import AppSettingsFields from "@/components/settings/AppSettingsFields.vue";
import WaveBackgroundHost from "@/components/waves/WaveBackgroundHost.vue";
import CosmicBoard from "@/components/CosmicBoard.vue";
import HexagramLines from "@/components/HexagramLines.vue";
import HexagramModal from "@/components/HexagramModal.vue";
import OrganHourCard from "@/components/astrology/OrganHourCard.vue";
import PillarBounds from "@/components/astrology/PillarBounds.vue";
import NinePalacesMatrix from "@/components/astrology/NinePalacesMatrix.vue";
import VedicChart from "@/components/astrology/VedicChart.vue";
import LocationAutocomplete from "@/components/ui/LocationAutocomplete.vue";
import PronunciationText from "@/components/ui/PronunciationText.vue";
import { parseGanZhi } from "@/core/ganzhi";
import { hasLlmKey } from "@/services/llmService";
import { useAppStore } from "@/stores/appStore";
import { useThemeStore } from "@/stores/themeStore";
import { getTrueSolarTime } from "@/utils/solarTime";
import { getVedicChart } from "@/utils/vedicMath";
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
const themeStore = useThemeStore();
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

const vedicUsingSavedBirthplace = computed(
  () => store.birthLatitude != null && store.birthLongitude != null
);

/**
 * Lagṇa needs a coherent (lat, lon) pair. Use saved **birth** coordinates when both exist;
 * otherwise use **device** `geoCoords` only when both lat/lon are available (no mixing sources).
 */
const vedicNatalSnapshot = computed(() => {
  let lat: number;
  let lon: number;
  if (vedicUsingSavedBirthplace.value) {
    lat = store.birthLatitude as number;
    lon = store.birthLongitude as number;
  } else {
    const g = store.geoCoords;
    if (!g || !Number.isFinite(g.lat) || !Number.isFinite(g.lon)) return null;
    lat = g.lat;
    lon = g.lon;
  }
  try {
    return getVedicChart(birthReferenceDate.value, lat, lon);
  } catch {
    return null;
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

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

/** Seconds shown in steps of 4 (0,4,…,56), phase-locked to the top of each hour. */
function quantizedSecond(sec: number) {
  return sec - (sec % 4);
}

const headerClockDatetime = ref("");

/** Same cos²/sin² + blur curve; duration per hand. */
const HEADER_SECONDS_CROSSFADE_MS = 4000;
const HEADER_MINUTES_CROSSFADE_MS = 8000;
const HEADER_HOURS_CROSSFADE_MS = 30_000;
const HEADER_MINUTE_CROSSFADE_START_SEC = 60 - 8; // :52–:59
const HEADER_HOUR_CROSSFADE_START_SEC = 60 - 30; // :59:30–:59:59

const headerHoursOutgoing = ref("00");
const headerHoursIncoming = ref("00");
const headerMinutesOutgoing = ref("00");
const headerMinutesIncoming = ref("00");
const headerSecondsOutgoing = ref("00");
const headerSecondsIncoming = ref("04");

const headerHoursOutStyle = ref<Record<string, string>>({ opacity: "1", filter: "blur(0px)" });
const headerHoursInStyle = ref<Record<string, string>>({ opacity: "0", filter: "blur(4.5px)" });
const headerMinutesOutStyle = ref<Record<string, string>>({ opacity: "1", filter: "blur(0px)" });
const headerMinutesInStyle = ref<Record<string, string>>({ opacity: "0", filter: "blur(4.5px)" });
const headerSecondsOutStyle = ref<Record<string, string>>({
  opacity: "1",
  filter: "blur(0px)",
});
const headerSecondsInStyle = ref<Record<string, string>>({
  opacity: "0",
  filter: "blur(4.5px)",
});

const HEADER_PULSE_TROUGH = 0.79;
const HEADER_PULSE_PEAK = 1;
const headerClockPulseStyle = ref<Record<string, string>>({ opacity: String(HEADER_PULSE_TROUGH) });

function tickHeaderClock() {
  const now = new Date();
  const h = now.getHours();
  const mi = now.getMinutes();
  const s = quantizedSecond(now.getSeconds());
  const y = now.getFullYear();
  const mo = pad2(now.getMonth() + 1);
  const da = pad2(now.getDate());
  headerClockDatetime.value = `${y}-${mo}-${da}T${pad2(h)}:${pad2(mi)}:${pad2(s)}`;
}

function blurForOpacity(o: number) {
  return (1 - Math.min(1, Math.sqrt(Math.max(0, o)))) * 4.5;
}

function crossfadeLayerStyles(outOpacity: number, inOpacity: number) {
  return {
    out: {
      opacity: String(outOpacity),
      filter: `blur(${blurForOpacity(outOpacity)}px)`,
    },
    in: {
      opacity: String(inOpacity),
      filter: `blur(${blurForOpacity(inOpacity)}px)`,
    },
  };
}

function updateHeaderClockAnimations() {
  const now = new Date();
  const h = now.getHours();
  const mi = now.getMinutes();
  const sec = now.getSeconds();
  const ms = now.getMilliseconds();

  const secBase = sec - (sec % 4);
  const secOut = secBase;
  const secIn = (secBase + 4) % 60;
  const secElapsedMs = (sec - secBase) * 1000 + ms;
  const secPhase = Math.min(1, secElapsedMs / HEADER_SECONDS_CROSSFADE_MS);
  const secAngles = crossfadeLayerStyles(
    Math.cos((Math.PI / 2) * secPhase) ** 2,
    Math.sin((Math.PI / 2) * secPhase) ** 2
  );
  headerSecondsOutgoing.value = pad2(secOut);
  headerSecondsIncoming.value = pad2(secIn);
  headerSecondsOutStyle.value = secAngles.out;
  headerSecondsInStyle.value = secAngles.in;

  let minPhase = 0;
  let minOut = mi;
  let minIn = mi;
  if (sec >= HEADER_MINUTE_CROSSFADE_START_SEC) {
    minOut = mi;
    minIn = (mi + 1) % 60;
    const minElapsedMs = (sec - HEADER_MINUTE_CROSSFADE_START_SEC) * 1000 + ms;
    minPhase = Math.min(1, minElapsedMs / HEADER_MINUTES_CROSSFADE_MS);
  }
  const minStyles = crossfadeLayerStyles(
    Math.cos((Math.PI / 2) * minPhase) ** 2,
    Math.sin((Math.PI / 2) * minPhase) ** 2
  );
  headerMinutesOutgoing.value = pad2(minOut);
  headerMinutesIncoming.value = pad2(minIn);
  headerMinutesOutStyle.value = minStyles.out;
  headerMinutesInStyle.value = minStyles.in;

  let hourPhase = 0;
  let hourOut = h;
  let hourIn = h;
  if (mi === 59 && sec >= HEADER_HOUR_CROSSFADE_START_SEC) {
    hourOut = h;
    hourIn = (h + 1) % 24;
    const hourElapsedMs = (sec - HEADER_HOUR_CROSSFADE_START_SEC) * 1000 + ms;
    hourPhase = Math.min(1, hourElapsedMs / HEADER_HOURS_CROSSFADE_MS);
  }
  const hourStyles = crossfadeLayerStyles(
    Math.cos((Math.PI / 2) * hourPhase) ** 2,
    Math.sin((Math.PI / 2) * hourPhase) ** 2
  );
  headerHoursOutgoing.value = pad2(hourOut);
  headerHoursIncoming.value = pad2(hourIn);
  headerHoursOutStyle.value = hourStyles.out;
  headerHoursInStyle.value = hourStyles.in;

  const T =
    now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds() + now.getMilliseconds() / 1000;
  const u = T % 2;
  const cosHalf = Math.cos((Math.PI * u) / 2);
  const pulseOpacity =
    HEADER_PULSE_TROUGH + (HEADER_PULSE_PEAK - HEADER_PULSE_TROUGH) * (cosHalf * cosHalf);
  headerClockPulseStyle.value = { opacity: String(pulseOpacity) };
}

let headerClockTimer: number | null = null;
let headerSecondsRaf: number | null = null;

function headerClockRafLoop() {
  updateHeaderClockAnimations();
  headerSecondsRaf = window.requestAnimationFrame(headerClockRafLoop);
}

let localSyncTimer: number | null = null;

onMounted(() => {
  tickHeaderClock();
  headerClockTimer = window.setInterval(tickHeaderClock, 1000);
  updateHeaderClockAnimations();
  headerSecondsRaf = window.requestAnimationFrame(headerClockRafLoop);
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
  if (headerClockTimer) window.clearInterval(headerClockTimer);
  if (headerSecondsRaf != null) window.cancelAnimationFrame(headerSecondsRaf);
  if (pastDebounce) clearTimeout(pastDebounce);
  if (presentDebounce) clearTimeout(presentDebounce);
});
</script>

<template>
  <div
    class="appRoot appRoot--home"
    :class="{ 'appRoot--cosmicCrawl': themeStore.skinFeatures.cosmicCrawlBackdrop }"
  >
    <WaveBackgroundHost v-if="themeStore.skinFeatures.homeWaveLayer" />
    <AstrologyCrawlBackdrop v-if="themeStore.skinFeatures.cosmicCrawlBackdrop" />
    <div class="homeForeground">
    <div class="homeDesktopGrid">
      <aside class="homeColLeft">
        <div class="homeBrand">
          <div class="titleRow">
            <time class="headerClock" :datetime="headerClockDatetime">
              <span class="headerClockDigitsWrap">
                <span class="headerClockDigitsSizer" aria-hidden="true">00</span>
                <span class="headerClockDigitsLayer" :style="headerHoursOutStyle">{{ headerHoursOutgoing }}</span>
                <span class="headerClockDigitsLayer" :style="headerHoursInStyle">{{ headerHoursIncoming }}</span>
              </span>
              <span class="headerClockPulse" :style="headerClockPulseStyle">時</span>
              <span class="headerClockDigitsWrap">
                <span class="headerClockDigitsSizer" aria-hidden="true">00</span>
                <span class="headerClockDigitsLayer" :style="headerMinutesOutStyle">{{ headerMinutesOutgoing }}</span>
                <span class="headerClockDigitsLayer" :style="headerMinutesInStyle">{{ headerMinutesIncoming }}</span>
              </span>
              <span class="headerClockPulse" :style="headerClockPulseStyle">分</span>
              <span class="headerClockDigitsWrap">
                <span class="headerClockDigitsSizer" aria-hidden="true">00</span>
                <span class="headerClockDigitsLayer" :style="headerSecondsOutStyle">{{ headerSecondsOutgoing }}</span>
                <span class="headerClockDigitsLayer" :style="headerSecondsInStyle">{{ headerSecondsIncoming }}</span>
              </span>
              <span class="headerClockPulse" :style="headerClockPulseStyle">秒</span>
            </time>
            <div class="title">Current (v0)</div>
          </div>
          <div class="subtitle">You're in the Present... Would you like to get in the Current?</div>
          <div class="sub">Stored locally. No accounts. Descriptive only.</div>
        </div>
      </aside>

      <div class="homeOrganHero">
        <OrganHourCard />
      </div>

      <aside class="homeColRight">
        <div class="headerOptionsPanel homeSettingsRail">
          <div class="headerFieldsGrid">
            <AppSettingsFields skin-select-variant="toolbar" skin-select-class="header-skin-select" />
          </div>
        </div>
      </aside>

      <div class="homeMainStream">
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
                    <LocationAutocomplete
                      v-model:locationName="store.birthLocationName"
                      v-model:latitude="store.birthLatitude"
                      v-model:longitude="store.birthLongitude"
                    />
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
              <div v-if="store.birthTemporalHex" class="flex gap-4 overflow-x-auto pb-2 items-start">
                <div class="pillarGrid shrink-0">
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
                <NinePalacesMatrix
                  v-if="store.birthProfile?.nineStar?.year?.number"
                  :center-star="store.birthProfile.nineStar.year.number"
                  class="shrink-0"
                />
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
                  <div class="organLine organSubLine">
                    <span class="cjkText">{{ store.presentShichenDetail.fullLabel }}</span>
                    <span class="organKeEn">{{ store.presentShichenDetail.fullLabelEn }}</span>
                    <span class="organKeBounds">{{ store.presentShichenDetail.keBoundsDisplay }}</span>
                  </div>
                </div>
                <div class="panelControls">
                  <input class="input inlineInput" type="datetime-local" v-model="store.presentDatetimeLocal" />
                  <button class="btn small" :class="{ primary: store.presentAuto }" @click="store.togglePresentAuto">Auto {{ store.presentAuto ? "On" : "Off" }}</button>
                  <button class="btn small" @click="store.shiftPresentHours(-2)">◀</button>
                  <button class="btn small" @click="store.shiftPresentHours(2)">▶</button>
                </div>
              </div>
              <div class="flex gap-4 overflow-x-auto pb-2 items-start">
                <div class="pillarGrid shrink-0">
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
                <NinePalacesMatrix
                  v-if="store.presentProfile?.nineStar?.year?.number"
                  :center-star="store.presentProfile.nineStar.year.number"
                  class="shrink-0"
                />
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
                  <div class="vedic-d1-advanced">
                    <p v-if="!vedicNatalSnapshot" class="vedic-d1-hint">
                      <strong>Vedic D1</strong> needs a full latitude and longitude. Either set
                      <strong>Past (Birth) → Birth location</strong> and pick a city from the list (saves both
                      coordinates), or allow the app to read your <strong>device location</strong> (same pair). Scroll
                      up to Past (Birth) if the birth field is not visible.
                    </p>
                    <p
                      v-else-if="!vedicUsingSavedBirthplace"
                      class="vedic-d1-hint vedic-d1-hint--soft"
                    >
                      Coordinates are not the full saved birthplace pair (using device or mixed fallbacks). For a natal
                      chart tied to your birth place, set <strong>Past (Birth) → Birth location</strong> and pick a city
                      from the search results.
                    </p>
                    <VedicChart v-if="vedicNatalSnapshot" :chart="vedicNatalSnapshot" />
                  </div>
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
    </div>
    </div>
  </div>
</template>

<style scoped>
.appRoot--cosmicCrawl {
  position: relative;
  isolation: isolate;
}

.headerOptionsPanel {
  width: 100%;
  max-width: min(960px, 100%);
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--b2, rgba(255, 255, 255, 0.12));
  background: rgba(0, 0, 0, 0.18);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.06) inset;
}

.headerFieldsGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px 18px;
  align-items: start;
}

.headerFieldsGrid :deep(.headerField--motion) {
  grid-column: 1 / -1;
}

.homeDesktopGrid {
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
}

.homeBrand {
  padding: 18px 18px 0 18px;
  box-sizing: border-box;
}

.homeColLeft,
.homeColRight {
  min-width: 0;
}

@media (max-width: 1199px) {
  .homeDesktopGrid {
    gap: 0;
  }

  .homeOrganHero {
    order: 1;
  }

  .homeColLeft {
    order: 2;
  }

  .homeColRight {
    order: 3;
    width: 100%;
    max-width: 100%;
  }

  .homeMainStream {
    order: 4;
  }
}

@media (min-width: 1200px) {
  .homeDesktopGrid {
    display: grid;
    grid-template-columns: minmax(200px, 280px) minmax(0, 1fr) minmax(260px, 300px);
    grid-template-rows: auto 1fr;
    gap: 16px 24px;
    padding: 0 18px;
    align-items: start;
  }

  /* Side rails: clock/copy and settings stay in view while center column scrolls */
  .homeColLeft,
  .homeColRight {
    position: sticky;
    top: calc(10px + env(safe-area-inset-top, 0px));
    align-self: start;
    z-index: 3;
    max-height: calc(100vh - 20px);
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }

  .homeColLeft {
    grid-column: 1;
    grid-row: 1 / span 2;
  }

  .homeBrand {
    padding-left: 0;
    padding-right: 8px;
  }

  .homeOrganHero {
    grid-column: 2;
    grid-row: 1;
    margin: 0;
    padding: 6px 0 0;
    max-width: none;
    width: 100%;
  }

  .homeColRight {
    grid-column: 3;
    grid-row: 1 / span 2;
    /* Align persistent settings with organ card (matches .homeOrganHero padding-top). */
    padding-top: 6px;
  }

  .homeMainStream {
    grid-column: 2;
    grid-row: 2;
    min-width: 0;
  }

  .titleRow {
    gap: 8px 12px;
  }

  .headerClock {
    font-size: 17px;
  }

  .headerOptionsPanel {
    max-width: none;
    padding: 10px 12px;
  }

  .headerFieldsGrid {
    display: flex;
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }

  .headerFieldsGrid :deep(.headerField--motion) {
    grid-column: auto;
  }
}

.appRoot--home {
  position: relative;
  z-index: 0;
}

.homeForeground {
  position: relative;
  z-index: 1;
}

.titleRow {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 10px 14px;
}

.headerClock {
  font-size: 20px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--muted);
  letter-spacing: 0.02em;
  white-space: nowrap;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial,
    "PingFang SC", "Hiragino Sans GB", "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP",
    "Noto Sans CJK SC", "Noto Sans SC", "Yu Gothic UI", "Microsoft YaHei", sans-serif;
}

.headerClockPulse {
  display: inline-block;
  margin: 0 1px;
  font-size: 0.68em;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.54);
}

.headerClockDigitsWrap {
  display: inline-block;
  position: relative;
  vertical-align: baseline;
  line-height: inherit;
}

.headerClockDigitsSizer {
  visibility: hidden;
  pointer-events: none;
  user-select: none;
  font-variant-numeric: tabular-nums;
}

.headerClockDigitsLayer {
  position: absolute;
  left: 0;
  top: 0;
  white-space: nowrap;
  z-index: 1;
  will-change: opacity, filter;
}

.homeColRight {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  align-self: flex-start;
  justify-content: flex-start;
}

.homeOrganHero {
  width: 100%;
  max-width: min(840px, 100%);
  margin: 0 auto 12px;
  padding: 6px 18px 0;
  box-sizing: border-box;
}

@media (max-width: 680px) {
  .homeOrganHero {
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

.vedic-d1-advanced {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--b2, rgba(51, 65, 85, 0.5));
}

.vedic-d1-hint {
  font-size: 12px;
  color: var(--muted, rgba(255, 255, 255, 0.55));
  line-height: 1.4;
  margin: 0;
}

.vedic-d1-hint--soft {
  margin-bottom: 8px;
  color: var(--muted, rgba(255, 255, 255, 0.65));
  border-left: 3px solid rgba(251, 191, 36, 0.4);
  padding-left: 10px;
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

.organSubLine {
  font-size: 12px;
  color: var(--muted, rgba(255, 255, 255, 0.55));
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  align-items: baseline;
  margin-top: 4px;
}
.organKeEn {
  opacity: 0.88;
  font-size: 11px;
}
.organKeBounds {
  font-variant-numeric: tabular-nums;
  opacity: 0.8;
  font-size: 11px;
}
</style>

