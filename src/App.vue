<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import HexagramLines from "./components/HexagramLines.vue";
import HexagramModal from "./components/HexagramModal.vue";
import QimenChart from "@/components/QimenChart.vue";
import { getTemporalXkdg } from "@/core/hexagramsXKDG";
import { parseGanZhi } from "@/core/ganzhi";
import { buildQimenChart } from "@/core/qimen";
import { computeBirthProfile, parseDatetimeLocal, type BirthProfileResult, type Sect } from "@/lib/personal/baziNineStar";
import { Lunar, LunarMonth, Solar } from "lunar-typescript";
import hexagramSummaries from "./data/hexagramSummaries.json";

type SignalStrength = "none" | "weak" | "moderate" | "dominant";
type Band = "low" | "moderate" | "high";
type Timing = "premature" | "neutral" | "ripe";

type HexagramSummary = {
  daoist: string;
  buddhist: string;
  confucian: string;
  humanDesign: string;
  geneKeys: string;
};
type HexagramSummaryMap = Record<string, HexagramSummary>;

type Reading = {
  id: string;
  createdAtISO: string;
  inputs: { dateISO: string; timeHHMM: string; location: string };
  meta: { signalStrength: SignalStrength; silence: boolean };
  sections: {
    snapshot: string;
    dynamics: string;
    misalignment: string;
    capacity: string;
    phase: string;
    notes: string;
  };
};

type WeatherSnapshot = {
  temp_f: number | null;
  precip: number | null;
  wind: number | null;
  notes: string | null;
};
type GeoCoords = { lat: number; lon: number };

const selectedDate = computed(() => {
  // local time (no "Z"); aligns with user-facing almanac behavior
  return new Date(`${dateISO.value}T${timeHHMM.value}:00`);
});

const temporalHex = computed(() => getTemporalXkdg(selectedDate.value));
const presentOrgan = computed(() => {
  const h = selectedDate.value.getHours();
  if (h >= 23 || h < 1) return "Gallbladder";
  if (h >= 1 && h < 3) return "Liver";
  if (h >= 3 && h < 5) return "Lung";
  if (h >= 5 && h < 7) return "Large Intestine";
  if (h >= 7 && h < 9) return "Stomach";
  if (h >= 9 && h < 11) return "Spleen";
  if (h >= 11 && h < 13) return "Heart";
  if (h >= 13 && h < 15) return "Small Intestine";
  if (h >= 15 && h < 17) return "Bladder";
  if (h >= 17 && h < 19) return "Kidney";
  if (h >= 19 && h < 21) return "Pericardium";
  return "Triple Burner";
});
const qimenScope = ref<"hour" | "day">("hour");
const qimenChartHour = computed(() => buildQimenChart(selectedDate.value, "hour"));
const qimenChartDay = computed(() => buildQimenChart(selectedDate.value, "day"));
const qimenChart = computed(() => (qimenScope.value === "hour" ? qimenChartHour.value : qimenChartDay.value));
const hexSummaryMap = hexagramSummaries as HexagramSummaryMap;
const isHexModalOpen = ref(false);
const selectedHexNum = ref<number | null>(null);
const selectedHexNameCn = ref<string | null>(null);
const selectedHexSummary = computed(() => {
  const num = selectedHexNum.value;
  if (!num) return null;
  return hexSummaryMap[String(num)] ?? null;
});
const selectedHexDisplayName = computed(() => hexNameShort(selectedHexNum.value, selectedHexNameCn.value) || "—");

// const temporalHexBinary = computed(() => ({
//   year: getHexBinary(temporalHex.value.hex.year),
//   month: getHexBinary(temporalHex.value.hex.month),
//   day: getHexBinary(temporalHex.value.hex.day),
//   hour: getHexBinary(temporalHex.value.hex.hour),
// }));

const LS_KEY = "current_almanac_log_v0";
const LS_KEY_USER_STATE = "current_almanac_user_state_v1";
const LS_KEY_BIRTH_DT = "current.birth.datetimeLocal";
const LS_KEY_BIRTH_SECT = "current.birth.sect";
const OPENAI_CHAT_ENDPOINT =
  (import.meta.env.VITE_OPENAI_PROXY_URL as string | undefined) ??
  "/.netlify/functions/openai-chat";
const OPENAI_MODEL = "gpt-4o-mini";

function safeLocalStorageGet(key: string) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeLocalStorageSet(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // ignore storage errors (e.g., privacy mode)
  }
}

function toDateISO(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
function toDatetimeLocal(d: Date) {
  return `${toDateISO(d)}T${toHHMM(d)}`;
}

const HEX_NAME_CN_SHORT: string[] = [
  "",
  "乾",
  "坤",
  "屯",
  "蒙",
  "需",
  "讼",
  "师",
  "比",
  "小畜",
  "履",
  "泰",
  "否",
  "同人",
  "大有",
  "谦",
  "豫",
  "随",
  "蛊",
  "临",
  "观",
  "噬嗑",
  "贲",
  "剥",
  "复",
  "无妄",
  "大畜",
  "颐",
  "大过",
  "坎",
  "离",
  "咸",
  "恒",
  "遯",
  "大壮",
  "晋",
  "明夷",
  "家人",
  "睽",
  "蹇",
  "解",
  "损",
  "益",
  "夬",
  "姤",
  "萃",
  "升",
  "困",
  "井",
  "革",
  "鼎",
  "震",
  "艮",
  "渐",
  "归妹",
  "丰",
  "旅",
  "巽",
  "兑",
  "涣",
  "节",
  "中孚",
  "小过",
  "既济",
  "未济",
];

function hexNameShort(num: number | null, fallback: string | null) {
  if (!num || num < 1 || num >= HEX_NAME_CN_SHORT.length) return fallback ?? "—";
  return HEX_NAME_CN_SHORT[num];
}

function openHexModal(hex: { num: number | null; nameCn: string | null }) {
  if (!hex?.num) return;
  selectedHexNum.value = hex.num;
  selectedHexNameCn.value = hex.nameCn ?? null;
  isHexModalOpen.value = true;
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

function normalizeDatetimeLocal(raw: string) {
  if (!raw) return "1990-01-01T12:00";
  try {
    parseDatetimeLocal(raw);
    return raw;
  } catch {
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return "1990-01-01T12:00";
    return toDatetimeLocal(d);
  }
}
function toHHMM(d: Date) {
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  return `${h}:${m}`;
}
function isoToday() {
  return toDateISO(new Date());
}
function hhmmNow() {
  return toHHMM(new Date());
}
function uid() {
  return Math.random().toString(36).slice(2) + "-" + Date.now().toString(36);
}

function loadLog(): Reading[] {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Reading[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}
function saveLog(log: Reading[]) {
  localStorage.setItem(LS_KEY, JSON.stringify(log.slice(0, 50)));
}

function loadUserState() {
  try {
    const raw = localStorage.getItem(LS_KEY_USER_STATE);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}
function saveUserState() {
  const payload = {
    intentDomain: intentDomain.value,
    intentGoalConstraint: intentGoalConstraint.value,
    userCapacity: userCapacity.value,
    userLoad: userLoad.value,
    userSleepQuality: userSleepQuality.value,
    userCognitiveNoise: userCognitiveNoise.value,
    userSocialLoad: userSocialLoad.value,
    userEmotionalTone: userEmotionalTone.value,
  };
  localStorage.setItem(LS_KEY_USER_STATE, JSON.stringify(payload));
}

function enforceConstraints(reading: Reading): Reading {
  const forbidden = [
    /\bshould\b/gi,
    /\byou must\b/gi,
    /\bwill happen\b/gi,
    /\bguarantee\b/gi,
    /\bdestiny\b/gi,
    /\bfate\b/gi,
    /\bgood day\b/gi,
    /\bbad day\b/gi,
    /\bthe universe\b/gi,
  ];

  const scrub = (s: string) => {
    let out = s;
    for (const rx of forbidden) out = out.replace(rx, "[redacted]");
    return out;
  };

  return {
    ...reading,
    sections: {
      snapshot: scrub(reading.sections.snapshot),
      dynamics: scrub(reading.sections.dynamics),
      misalignment: scrub(reading.sections.misalignment),
      capacity: scrub(reading.sections.capacity),
      phase: scrub(reading.sections.phase),
      notes: scrub(reading.sections.notes),
    },
  };
}

/**
 * Minimal, deterministic, descriptive "engine".
 * Purpose: give the UI something real to render today.
 */
function generateReading(input: {
  dateISO: string;
  timeHHMM: string;
  location: string;
}): Reading {
  const seedStr = `${input.dateISO}T${input.timeHHMM}|${input.location.trim().toLowerCase()}`;
  let hash = 0;
  for (let i = 0; i < seedStr.length; i++) hash = (hash * 31 + seedStr.charCodeAt(i)) >>> 0;

  const flow: Band = hash % 3 === 0 ? "high" : hash % 3 === 1 ? "moderate" : "low";
  const resistance: Band =
    (hash >>> 2) % 3 === 0 ? "high" : (hash >>> 2) % 3 === 1 ? "moderate" : "low";
  const pressure: Band =
    (hash >>> 4) % 3 === 0 ? "high" : (hash >>> 4) % 3 === 1 ? "moderate" : "low";

  const timing: Timing =
    (hash >>> 6) % 3 === 0 ? "premature" : (hash >>> 6) % 3 === 1 ? "neutral" : "ripe";
  const load: Band =
    (hash >>> 8) % 3 === 0 ? "high" : (hash >>> 8) % 3 === 1 ? "moderate" : "low";

  const signalStrength: SignalStrength =
    pressure === "high" && resistance === "high"
      ? "dominant"
      : pressure === "high" || resistance === "high" || flow === "high"
      ? "moderate"
      : pressure === "moderate" || resistance === "moderate" || flow === "moderate"
      ? "weak"
      : "none";

  const silence =
    signalStrength === "none" || (signalStrength === "weak" && timing === "neutral" && load !== "low");

  const snapshot = silence
    ? "No dominant signal is present. Conditions read as steady and non-demanding."
    : `Configuration reads as ${timing} timing with ${pressure} pressure, ${resistance} resistance, and ${flow} flow.`;

  const dynamics = silence
    ? "Movement appears incremental rather than directional. Small adjustments register more than major shifts."
    : [
        flow === "high"
          ? "Momentum is available where effort aligns with existing motion."
          : "Flow is limited; movement may require setup rather than push.",
        pressure === "high"
          ? "Pressure is accumulating and tends to compress decision space."
          : pressure === "moderate"
          ? "Pressure is present but not dominant."
          : "Pressure is low; the system is not forcing immediate change.",
      ].join(" ");

  const misalignment = silence
    ? "Misalignment signals are muted. Over-correction is the primary risk."
    : [
        resistance === "high"
          ? "Increased effort may produce diminishing returns; repeated friction is an early warning signal."
          : resistance === "moderate"
          ? "Some friction is expected; watch for escalation when forcing pace."
          : "Friction is low; misalignment is more likely to come from haste than obstruction.",
        timing === "premature"
          ? "Timing reads early; forcing outcomes tends to increase resistance rather than convert effort efficiently."
          : timing === "ripe"
          ? "Timing reads ripe; conversion improves when action matches the existing direction of motion."
          : "Timing reads neutral; signal quality depends on load and local constraints.",
      ].join(" ");

  const capacity = [
    `Load reads ${load}.`,
    load === "high"
      ? "Additional demand is more likely to strain reserves than produce clean conversion."
      : load === "moderate"
      ? "Reserves appear usable but not abundant; conversion improves with selective engagement."
      : "Reserves appear available; capacity is less likely to be the limiting factor.",
  ].join(" ");

  const phase = silence
    ? "This reads as a moment-level fluctuation within a stable phase."
    : pressure === "high" && timing !== "ripe"
    ? "This reads as a phase-level accumulation pattern rather than a single-moment blip."
    : "This reads as primarily moment-level conditions; broader phase signals are not dominant.";

  const notes =
    "Current describes conditions only. It does not provide instructions, predictions, or moral framing.";

  const reading: Reading = {
    id: uid(),
    createdAtISO: new Date().toISOString(),
    inputs: { ...input },
    meta: { signalStrength, silence },
    sections: { snapshot, dynamics, misalignment, capacity, phase, notes },
  };

  return enforceConstraints(reading);
}

// state
const dateISO = ref(isoToday());
const timeHHMM = ref(hhmmNow());
const location = ref("");
const geoCoords = ref<GeoCoords | null>(null);
const timezoneLabel = ref("unknown");
const birthDatetimeLocal = ref<string>(
  normalizeDatetimeLocal(safeLocalStorageGet(LS_KEY_BIRTH_DT) ?? "1990-01-01T12:00")
);
const birthSect = ref<Sect>((Number(safeLocalStorageGet(LS_KEY_BIRTH_SECT)) as Sect) || 2);
const birthProfile = computed<BirthProfileResult | null>(() => {
  try {
    const input = parseDatetimeLocal(birthDatetimeLocal.value);
    return computeBirthProfile(input, birthSect.value);
  } catch {
    return null;
  }
});
const presentAuto = ref(true);
const intentDomain = ref("general");
const intentGoalConstraint = ref("Test the current conditions without changing plans.");
const userCapacity = ref<number | null>(6);
const userLoad = ref<number | null>(4);
const userSleepQuality = ref<number | null>(6);
const userCognitiveNoise = ref<number | null>(3);
const userSocialLoad = ref<number | null>(4);
const userEmotionalTone = ref("Steady, focused, lightly distracted.");

const weatherSnapshot = ref<WeatherSnapshot | null>(null);
const weatherStatus = ref<"idle" | "loading" | "error">("idle");
const weatherError = ref<string | null>(null);

const pastAiSummary = ref<string | null>(null);
const pastAiStatus = ref<"idle" | "loading" | "error">("idle");
const pastAiError = ref<string | null>(null);
const lastPastGzKey = ref<string | null>(null);

const presentAiSummary = ref<string | null>(null);
const presentAiStatus = ref<"idle" | "loading" | "error">("idle");
const presentAiError = ref<string | null>(null);
const lastPresentGzKey = ref<string | null>(null);

const aiSummaryRaw = ref("");
const aiSummaryJson = ref<Record<string, unknown> | null>(null);
const aiStatus = ref<"idle" | "loading" | "error">("idle");
const aiError = ref<string | null>(null);

watch(
  [
    intentDomain,
    intentGoalConstraint,
    userCapacity,
    userLoad,
    userSleepQuality,
    userCognitiveNoise,
    userSocialLoad,
    userEmotionalTone,
  ],
  () => saveUserState()
);

watch(birthDatetimeLocal, (v) => safeLocalStorageSet(LS_KEY_BIRTH_DT, v));
watch(birthSect, (v) => safeLocalStorageSet(LS_KEY_BIRTH_SECT, String(v)));
watch(presentAuto, (v) => {
  if (v) syncLocalTimeNow(true);
});

const log = ref<Reading[]>([]);
const active = ref<Reading | null>(null);

function getLocalTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "unknown";
}

function formatIsoWithOffset(d: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  const y = d.getFullYear();
  const m = pad(d.getMonth() + 1);
  const day = pad(d.getDate());
  const h = pad(d.getHours());
  const min = pad(d.getMinutes());
  const s = pad(d.getSeconds());
  const offsetMin = -d.getTimezoneOffset();
  const sign = offsetMin >= 0 ? "+" : "-";
  const abs = Math.abs(offsetMin);
  const offH = pad(Math.floor(abs / 60));
  const offM = pad(abs % 60);
  return `${y}-${m}-${day}T${h}:${min}:${s}${sign}${offH}:${offM}`;
}

async function reverseGeocode(lat: number, lon: number) {
  const res = await fetch(
    `https://geocoding-api.open-meteo.com/v1/reverse?latitude=${lat}&longitude=${lon}&language=en&format=json`
  );
  if (!res.ok) return null;
  const data = await res.json();
  const result = data?.results?.[0];
  if (!result) return null;
  return `${result.name}${result.admin1 ? `, ${result.admin1}` : ""}${result.country ? `, ${result.country}` : ""}`;
}

async function fetchIpLocation() {
  try {
    const res = await fetch("https://ipapi.co/json/");
    if (!res.ok) return null;
    const data = await res.json();
    const lat = Number(data?.latitude);
    const lon = Number(data?.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    const name = [data?.city, data?.region, data?.country_name].filter(Boolean).join(", ");
    return {
      lat,
      lon,
      name: name || null,
      timezone: typeof data?.timezone === "string" ? data.timezone : null,
    };
  } catch {
    return null;
  }
}

async function hydrateFromGeolocation() {
  if (!("geolocation" in navigator)) return;
  return new Promise<void>((resolve) => {
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        geoCoords.value = { lat, lon };
        const name = await reverseGeocode(lat, lon);
        if (name) location.value = name;
        resolve();
      },
      async () => {
        const fallback = await fetchIpLocation();
        if (fallback) {
          geoCoords.value = { lat: fallback.lat, lon: fallback.lon };
          if (fallback.name) location.value = fallback.name;
          if (fallback.timezone) timezoneLabel.value = fallback.timezone;
        }
        resolve();
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 }
    );
  });
}

function syncLocalTimeNow(force = false) {
  if (!force && !presentAuto.value) return;
  const now = new Date();
  dateISO.value = toDateISO(now);
  timeHHMM.value = toHHMM(now);
}

function shiftPresentHours(deltaHours: number) {
  presentAuto.value = false;
  const base = new Date(`${dateISO.value}T${timeHHMM.value}:00`);
  base.setHours(base.getHours() + deltaHours);
  dateISO.value = toDateISO(base);
  timeHHMM.value = toHHMM(base);
}

async function fetchWeatherSnapshotFromCoords(coords: GeoCoords | null): Promise<WeatherSnapshot | null> {
  if (!coords) {
    weatherStatus.value = "idle";
    weatherError.value = null;
    weatherSnapshot.value = null;
    return null;
  }

  try {
    weatherStatus.value = "loading";
    weatherError.value = null;

    const url =
      `https://api.open-meteo.com/v1/forecast?latitude=${coords.lat}&longitude=${coords.lon}` +
      `&current=temperature_2m,precipitation,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Weather fetch failed.");
    const data = await res.json();

    const current = data?.current ?? {};
    const snapshot: WeatherSnapshot = {
      temp_f: Number.isFinite(current.temperature_2m) ? current.temperature_2m : null,
      precip: Number.isFinite(current.precipitation) ? current.precipitation : null,
      wind: Number.isFinite(current.wind_speed_10m) ? current.wind_speed_10m : null,
      notes: null,
    };

    weatherSnapshot.value = snapshot;
    weatherStatus.value = "idle";
    return snapshot;
  } catch (err) {
    weatherStatus.value = "error";
    weatherError.value = err instanceof Error ? err.message : "Weather lookup failed.";
    return null;
  }
}

let localSyncTimer: number | null = null;

onMounted(() => {
  const l = loadLog();
  log.value = l.sort((a, b) => (a.createdAtISO < b.createdAtISO ? 1 : -1));
  active.value = log.value[0] ?? null;
  syncLocalTimeNow(true);
  timezoneLabel.value = getLocalTimezone();
  void hydrateFromGeolocation();
  localSyncTimer = window.setInterval(() => {
    syncLocalTimeNow();
    timezoneLabel.value = getLocalTimezone();
  }, 60_000);

  const saved = loadUserState();
  if (saved) {
    if (typeof saved.intentDomain === "string") intentDomain.value = saved.intentDomain;
    if (typeof saved.intentGoalConstraint === "string") intentGoalConstraint.value = saved.intentGoalConstraint;
    if (Number.isFinite(saved.userCapacity)) userCapacity.value = saved.userCapacity as number;
    if (Number.isFinite(saved.userLoad)) userLoad.value = saved.userLoad as number;
    if (Number.isFinite(saved.userSleepQuality)) userSleepQuality.value = saved.userSleepQuality as number;
    if (Number.isFinite(saved.userCognitiveNoise)) userCognitiveNoise.value = saved.userCognitiveNoise as number;
    if (Number.isFinite(saved.userSocialLoad)) userSocialLoad.value = saved.userSocialLoad as number;
    if (typeof saved.userEmotionalTone === "string") userEmotionalTone.value = saved.userEmotionalTone;
  }
});

onUnmounted(() => {
  if (localSyncTimer) window.clearInterval(localSyncTimer);
});

const sortedLog = computed(() =>
  [...log.value].sort((a, b) => (a.createdAtISO < b.createdAtISO ? 1 : -1))
);

function generate() {
  const r = generateReading({ dateISO: dateISO.value, timeHHMM: timeHHMM.value, location: location.value });
  log.value = [r, ...log.value].slice(0, 50);
  active.value = r;
  saveLog(log.value);
}

function clearLog() {
  log.value = [];
  active.value = null;
  localStorage.removeItem(LS_KEY);
}

function normalizeOptionalNumber(value: number | null) {
  return Number.isFinite(value ?? NaN) ? value : null;
}

function solarToDate(solar: Solar) {
  return new Date(solar.toYmdHms().replace(" ", "T"));
}

function buildInterpretationPayload(snapshot: WeatherSnapshot | null) {
  if (!active.value) return null;

  const b = birthProfile.value;
  const hex = temporalHex.value;
  const date = selectedDate.value;
  const solar = Solar.fromDate(date);
  const lunar = Lunar.fromSolar(solar);
  const monthObj = LunarMonth.fromYm(lunar.getYear(), lunar.getMonth());
  const nextJieQi = lunar.getNextJieQi?.() ?? null;
  const nextJieQiSolar = nextJieQi ? nextJieQi.getSolar() : null;
  const daysToNext =
    nextJieQiSolar ? Math.max(0, Math.round((solarToDate(nextJieQiSolar).getTime() - date.getTime()) / 86400000)) : null;

  const resolveIntent = (value: string) => value.trim() || "unknown";

  const yiTags = (lunar.getDayYi?.() ?? []) as string[];
  const jiTags = (lunar.getDayJi?.() ?? []) as string[];
  const serializeQimen = (chart: typeof qimenChartHour.value | null) => {
    if (!chart) return null;
    return {
      method: chart.method,
      scope: chart.scope,
      solar: chart.solar,
      lunar: chart.lunar,
      zhiRun: chart.zhiRun,
      palaces: chart.palaces,
      grid: chart.grid,
    };
  };

  return {
    schema_version: "current_v1",
    inputs: {
      moment: {
        timestamp_iso: formatIsoWithOffset(date),
        timezone: timezoneLabel.value || "unknown",
        location: location.value || "unknown",
        local_weather: {
          temp_f: snapshot?.temp_f ?? null,
          precip: snapshot?.precip ?? null,
          wind: snapshot?.wind ?? null,
          notes: snapshot?.notes ?? null,
        },
      },
      calendar: {
        jieqi: {
          current: lunar.getJieQi?.() || null,
          days_to_next: daysToNext,
        },
        lunar_date: {
          lunar_month: Number.isFinite(lunar.getMonth()) ? Math.abs(lunar.getMonth()) : null,
          lunar_day: Number.isFinite(lunar.getDay()) ? lunar.getDay() : null,
          is_leap_month: monthObj ? monthObj.isLeap() : null,
        },
        ganzhi_moment: {
          year: hex.year.ganzhi ?? null,
          month: hex.month.ganzhi ?? null,
          day: hex.day.ganzhi ?? null,
          hour: hex.hour.ganzhi ?? null,
        },
      },
      user: {
        bazi_natal: {
          year: b?.bazi.pillars.year.ganZhi ?? null,
          month: b?.bazi.pillars.month.ganZhi ?? null,
          day: b?.bazi.pillars.day.ganZhi ?? null,
          hour: b?.bazi.pillars.hour.ganZhi ?? null,
          day_master: b?.bazi.pillars.day.gan ?? null,
          dayun_current: null,
        },
        nine_star: {
          year_star: b?.nineStar.year.number ?? null,
          month_star: b?.nineStar.month.number ?? null,
          day_star: b?.nineStar.day.number ?? null,
        },
        state: {
          capacity_0_10: normalizeOptionalNumber(userCapacity.value),
          load_0_10: normalizeOptionalNumber(userLoad.value),
          sleep_quality_0_10: normalizeOptionalNumber(userSleepQuality.value),
          cognitive_noise_0_10: normalizeOptionalNumber(userCognitiveNoise.value),
          social_load_0_10: normalizeOptionalNumber(userSocialLoad.value),
          emotional_tone: userEmotionalTone.value.trim() || null,
        },
        intent: {
          domain: resolveIntent(intentDomain.value),
          goal_constraint: resolveIntent(intentGoalConstraint.value),
        },
      },
      optional_systems: {
        tongshu: {
          day_quality: null,
          avoid_tags: Array.isArray(jiTags) ? jiTags : [],
          do_tags: Array.isArray(yiTags) ? yiTags : [],
        },
        qimen: {
          chart: {
            hour: serializeQimen(qimenChartHour.value),
            day: serializeQimen(qimenChartDay.value),
          },
          primary: "hour",
          notes: "Zhi Run rotating-plate Qimen (hour + day) with intercalary rules applied.",
        },
      },
    },
    output_contract: {
      format: "json",
      fields: [
        "current_summary",
        "shi",
        "shun",
        "ji",
        "load_capacity",
        "misalignment_signals",
        "recommended_modes",
        "avoid",
        "self_check",
      ],
      style: {
        tone: "neutral_descriptive",
        no_prediction: true,
        no_moralizing: true,
        no_destiny: true,
        max_length_words: 260,
      },
    },
  };
}

function birthInputToDate(input: BirthProfileResult["input"]) {
  return new Date(
    input.year,
    input.month - 1,
    input.day,
    input.hour,
    input.minute ?? 0,
    input.second ?? 0
  );
}

const birthTemporalHex = computed(() => {
  const b = birthProfile.value;
  if (!b) return null;
  return getTemporalXkdg(birthInputToDate(b.input));
});

const presentDatetimeLocal = computed({
  get() {
    return `${dateISO.value}T${timeHHMM.value}`;
  },
  set(value: string) {
    if (!value || !value.includes("T")) return;
    const [d, t] = value.split("T");
    if (!d || !t) return;
    dateISO.value = d;
    timeHHMM.value = t.slice(0, 5);
    presentAuto.value = false;
  },
});

function buildPastPayload() {
  const b = birthProfile.value;
  const hex = birthTemporalHex.value;
  if (!b || !hex) return null;
  return {
    birth_datetime_local: birthDatetimeLocal.value,
    bazi_pillars: {
      year: b.bazi.pillars.year.ganZhi,
      month: b.bazi.pillars.month.ganZhi,
      day: b.bazi.pillars.day.ganZhi,
      hour: b.bazi.pillars.hour.ganZhi,
    },
    temporal_hexagrams: {
      year: hex.year.ganzhi,
      month: hex.month.ganzhi,
      day: hex.day.ganzhi,
      hour: hex.hour.ganzhi,
    },
  };
}

function buildPresentPayload() {
  return {
    present_datetime_local: presentDatetimeLocal.value,
    temporal_hexagrams: {
      year: temporalHex.value.year.ganzhi,
      month: temporalHex.value.month.ganzhi,
      day: temporalHex.value.day.ganzhi,
      hour: temporalHex.value.hour.ganzhi,
    },
    organ_window: presentOrgan.value,
  };
}

async function requestInterpretation(kind: "past" | "present", payload: Record<string, unknown>) {
  if (kind === "past") {
    pastAiStatus.value = "loading";
    pastAiError.value = null;
  } else {
    presentAiStatus.value = "loading";
    presentAiError.value = null;
  }

  const systemPrompt =
    kind === "past"
      ? "You are a BaZi temperament interpreter. Address the user directly as \"you\". Use the provided birth pillars and temporal hexagrams to describe temperament, strengths, stress patterns, and preferred environments. Be descriptive, not predictive. Avoid medical/legal/financial advice. Avoid destiny/fate framing. Output 2 short paragraphs plus 4-6 concise bullet points."
      : "You are a present-moment conditions interpreter. Use the provided temporal hexagrams and timing to describe flow, resistance, harmony/clash, and practical options. Offer action guidance as possibilities (not directives). Include activities that are favorable or unfavorable (e.g., travel, outreach, rest). Avoid destiny/fate framing. Output 2 short paragraphs plus 4-6 concise bullet points.";

  try {
    const res = await fetch(OPENAI_CHAT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: OPENAI_MODEL,
        temperature: 0.4,
        max_tokens: 360,
        messages: [
          { role: "system", content: systemPrompt },
          {
            role: "user",
            content: `Use this data:\n${JSON.stringify(payload, null, 2)}`,
          },
        ],
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`OpenAI error (${res.status}): ${text || res.statusText}`);
    }

    const data = await res.json();
    const content = data?.choices?.[0]?.message?.content?.trim() ?? "";

    if (kind === "past") {
      pastAiSummary.value = content || null;
      pastAiStatus.value = "idle";
    } else {
      presentAiSummary.value = content || null;
      presentAiStatus.value = "idle";
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Interpretation request failed.";
    if (kind === "past") {
      pastAiStatus.value = "error";
      pastAiError.value = msg;
    } else {
      presentAiStatus.value = "error";
      presentAiError.value = msg;
    }
  }
}

watch(
  () => birthTemporalHex.value,
  () => {
    const hex = birthTemporalHex.value;
    if (!hex) return;
    const key = [hex.year.ganzhi, hex.month.ganzhi, hex.day.ganzhi, hex.hour.ganzhi].join("|");
    if (key === lastPastGzKey.value) return;
    lastPastGzKey.value = key;
    const payload = buildPastPayload();
    if (payload) void requestInterpretation("past", payload);
  },
  { immediate: true }
);

watch(
  () => temporalHex.value,
  () => {
    const hex = temporalHex.value;
    const key = [hex.year.ganzhi, hex.month.ganzhi, hex.day.ganzhi, hex.hour.ganzhi].join("|");
    if (key === lastPresentGzKey.value) return;
    lastPresentGzKey.value = key;
    const payload = buildPresentPayload();
    void requestInterpretation("present", payload);
  },
  { immediate: true }
);

function formatAiValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "unknown";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function hasAiValue(value: unknown) {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim().length > 0 && value.trim().toLowerCase() !== "unknown";
  if (Array.isArray(value)) return value.length > 0;
  return true;
}

async function generateInterpretation() {
  aiError.value = null;
  aiSummaryRaw.value = "";
  aiSummaryJson.value = null;

  if (!active.value) {
    aiStatus.value = "error";
    aiError.value = "Generate a reading before requesting AI interpretation.";
    return;
  }

  aiStatus.value = "loading";

  try {
    const snapshot = await fetchWeatherSnapshotFromCoords(geoCoords.value);
    const payload = buildInterpretationPayload(snapshot);
    if (!payload) {
      aiStatus.value = "error";
      aiError.value = "Unable to build interpretation payload.";
      return;
    }

    const res = await fetch(OPENAI_CHAT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: OPENAI_MODEL,
        temperature: 0.4,
        max_tokens: 420,
        messages: [
          {
            role: "system",
            content: `You are a Wu Wei Daoist master consulting the charts for a person and giving them the state of play for their day to help them stay in the current and navigate the Dao effectively. Please write a paragraph answering the following question:

How does this person's unique BaZi chart meet the current conditions right now? Where is there harmony? Where is there clash? What is available in this moment? What is unavailable? What is low resistance? What is high resistance?

Please be descriptive of the moment, not prescriptive of fate or destiny. The User input will contain the data neccessary for this answer.`,
          },
          {
            role: "user",
            content:
              "Use the following JSON as the Data JSON for this request. " +
              "Follow the output contract exactly.\n\n" +
              `${JSON.stringify(payload, null, 2)}`,
          },
        ],
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`OpenAI error (${res.status}): ${text || res.statusText}`);
    }

    const data = await res.json();
    const content = data?.choices?.[0]?.message?.content?.trim();
    if (!content) throw new Error("No content returned from OpenAI.");

    aiSummaryRaw.value = content;
    try {
      aiSummaryJson.value = JSON.parse(content);
    } catch {
      aiSummaryJson.value = null;
    }
    aiStatus.value = "idle";
  } catch (err) {
    aiStatus.value = "error";
    aiError.value = err instanceof Error ? err.message : "Failed to generate AI interpretation.";
  }
}

async function copyActive() {
  if (!active.value) return;
  const r = active.value;
  const text = [
    `Current Reading`,
    `${r.inputs.dateISO} ${r.inputs.timeHHMM} • ${r.inputs.location || "location unspecified"}`,
    ``,
    `Current Snapshot: ${r.sections.snapshot}`,
    ``,
    `Dominant Dynamics: ${r.sections.dynamics}`,
    ``,
    `Misalignment Signals: ${r.sections.misalignment}`,
    ``,
    `Capacity / Load: ${r.sections.capacity}`,
    ``,
    `Phase vs Moment: ${r.sections.phase}`,
    ``,
    `Notes: ${r.sections.notes}`,
  ].join("\n");
  await navigator.clipboard.writeText(text);
}
</script>

<template>
  <div class="appRoot">
    <div class="appHeader">
      <div class="title">Current (v0)</div>
      <div class="subtitle">You're in the Present... Would you like to get in the Current?</div>
      <div class="sub">Stored locally. No accounts. Descriptive only.</div>
    </div>

    <div class="wrap">
      <aside class="side">

      <div class="controls">
        <label class="lbl">
          Location (auto)
          <input class="input" type="text" :value="location || 'unknown'" readonly />
        </label>

        <button class="btn" @click="hydrateFromGeolocation">Use current location</button>

        <label class="lbl">
          Timezone
          <input class="input" type="text" :value="timezoneLabel" readonly />
        </label>

        <button class="btn primary" @click="generate">Generate Reading</button>
        <button class="btn" @click="clearLog">Clear Log</button>
      </div>

      <div class="sectionHdr">User Intent</div>
      <div class="controls">
        <label class="lbl">
          Domain
          <input class="input" type="text" placeholder="e.g., work, relationships" v-model="intentDomain" />
        </label>
        <label class="lbl">
          Goal Constraint
          <input class="input" type="text" placeholder="One sentence" v-model="intentGoalConstraint" />
        </label>
      </div>

      <div class="sectionHdr">User State (Optional)</div>
      <div class="controls">
        <label class="lbl">
          Capacity (0-10)
          <input class="input" type="number" min="0" max="10" step="1" v-model.number="userCapacity" />
        </label>
        <label class="lbl">
          Load (0-10)
          <input class="input" type="number" min="0" max="10" step="1" v-model.number="userLoad" />
        </label>
        <label class="lbl">
          Sleep Quality (0-10)
          <input class="input" type="number" min="0" max="10" step="1" v-model.number="userSleepQuality" />
        </label>
        <label class="lbl">
          Cognitive Noise (0-10)
          <input class="input" type="number" min="0" max="10" step="1" v-model.number="userCognitiveNoise" />
        </label>
        <label class="lbl">
          Social Load (0-10)
          <input class="input" type="number" min="0" max="10" step="1" v-model.number="userSocialLoad" />
        </label>
        <label class="lbl">
          Emotional Tone
          <input class="input" type="text" placeholder="One sentence" v-model="userEmotionalTone" />
        </label>
      </div>

      <div class="sectionHdr">Recent</div>

      <div class="recent">
        <div v-if="sortedLog.length === 0" class="empty">No readings yet.</div>

        <button
          v-for="r in sortedLog"
          :key="r.id"
          class="item"
          :class="{ active: active?.id === r.id }"
          @click="active = r"
        >
          <div class="itemTitle">{{ r.inputs.dateISO }} {{ r.inputs.timeHHMM }}</div>
          <div class="itemSub">{{ r.inputs.location || "—" }}</div>
          <div class="itemMeta">{{ r.meta.silence ? "Silence" : `Signal: ${r.meta.signalStrength}` }}</div>
        </button>
      </div>
    </aside>

    <main class="main">
      <div class="card">
        <div class="topSections">
          <section class="panel">
            <div class="panelHeader">
              <div class="secTitle">Past (Birth)</div>
              <div class="panelControls">
                <label class="inlineLbl">
                  Birth datetime
                  <input class="input inlineInput" type="datetime-local" v-model="birthDatetimeLocal" />
                </label>
                <label class="inlineLbl">
                  BaZi sect
                  <select class="input inlineInput inlineSelect" v-model.number="birthSect">
                    <option :value="1">sect 1</option>
                    <option :value="2">sect 2</option>
                  </select>
                </label>
              </div>
            </div>

            <div v-if="birthTemporalHex" class="pillarGrid">
              <div class="pillarBox">
                <div class="pillarLabel">Year</div>
                <div class="pillarGz cjkText">{{ formatGanZhiLines(birthTemporalHex.year.ganzhi) }}</div>
                <div
                  class="pillarHex"
                  :class="{ clickable: !!birthTemporalHex.year.hex.num }"
                  role="button"
                  :tabindex="birthTemporalHex.year.hex.num ? 0 : -1"
                  :aria-disabled="!birthTemporalHex.year.hex.num"
                  @click="openHexModal(birthTemporalHex.year.hex)"
                  @keydown.enter.prevent="openHexModal(birthTemporalHex.year.hex)"
                  @keydown.space.prevent="openHexModal(birthTemporalHex.year.hex)"
                >
                  <div class="hexNum">#{{ birthTemporalHex.year.hex.num ?? "—" }}</div>
                  <HexagramLines :binary="birthTemporalHex.year.hex.binary" size="sm" />
                  <div class="hexName cjkText">
                    {{ hexNameShort(birthTemporalHex.year.hex.num ?? null, birthTemporalHex.year.hex.nameCn) }}
                  </div>
                </div>
              </div>
              <div class="pillarBox">
                <div class="pillarLabel">Month</div>
                <div class="pillarGz cjkText">{{ formatGanZhiLines(birthTemporalHex.month.ganzhi) }}</div>
                <div
                  class="pillarHex"
                  :class="{ clickable: !!birthTemporalHex.month.hex.num }"
                  role="button"
                  :tabindex="birthTemporalHex.month.hex.num ? 0 : -1"
                  :aria-disabled="!birthTemporalHex.month.hex.num"
                  @click="openHexModal(birthTemporalHex.month.hex)"
                  @keydown.enter.prevent="openHexModal(birthTemporalHex.month.hex)"
                  @keydown.space.prevent="openHexModal(birthTemporalHex.month.hex)"
                >
                  <div class="hexNum">#{{ birthTemporalHex.month.hex.num ?? "—" }}</div>
                  <HexagramLines :binary="birthTemporalHex.month.hex.binary" size="sm" />
                  <div class="hexName cjkText">
                    {{ hexNameShort(birthTemporalHex.month.hex.num ?? null, birthTemporalHex.month.hex.nameCn) }}
                  </div>
                </div>
              </div>
              <div class="pillarBox">
                <div class="pillarLabel">Day</div>
                <div class="pillarGz cjkText">{{ formatGanZhiLines(birthTemporalHex.day.ganzhi) }}</div>
                <div
                  class="pillarHex"
                  :class="{ clickable: !!birthTemporalHex.day.hex.num }"
                  role="button"
                  :tabindex="birthTemporalHex.day.hex.num ? 0 : -1"
                  :aria-disabled="!birthTemporalHex.day.hex.num"
                  @click="openHexModal(birthTemporalHex.day.hex)"
                  @keydown.enter.prevent="openHexModal(birthTemporalHex.day.hex)"
                  @keydown.space.prevent="openHexModal(birthTemporalHex.day.hex)"
                >
                  <div class="hexNum">#{{ birthTemporalHex.day.hex.num ?? "—" }}</div>
                  <HexagramLines :binary="birthTemporalHex.day.hex.binary" size="sm" />
                  <div class="hexName cjkText">
                    {{ hexNameShort(birthTemporalHex.day.hex.num ?? null, birthTemporalHex.day.hex.nameCn) }}
                  </div>
                </div>
              </div>
              <div class="pillarBox">
                <div class="pillarLabel">Hour</div>
                <div class="pillarGz cjkText">{{ formatGanZhiLines(birthTemporalHex.hour.ganzhi) }}</div>
                <div
                  class="pillarHex"
                  :class="{ clickable: !!birthTemporalHex.hour.hex.num }"
                  role="button"
                  :tabindex="birthTemporalHex.hour.hex.num ? 0 : -1"
                  :aria-disabled="!birthTemporalHex.hour.hex.num"
                  @click="openHexModal(birthTemporalHex.hour.hex)"
                  @keydown.enter.prevent="openHexModal(birthTemporalHex.hour.hex)"
                  @keydown.space.prevent="openHexModal(birthTemporalHex.hour.hex)"
                >
                  <div class="hexNum">#{{ birthTemporalHex.hour.hex.num ?? "—" }}</div>
                  <HexagramLines :binary="birthTemporalHex.hour.hex.binary" size="sm" />
                  <div class="hexName cjkText">
                    {{ hexNameShort(birthTemporalHex.hour.hex.num ?? null, birthTemporalHex.hour.hex.nameCn) }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="meta">Enter a valid birth datetime.</div>
            <div class="placeholder">
              <div v-if="pastAiStatus === 'loading'">Generating interpretation...</div>
              <div v-else-if="pastAiStatus === 'error'">{{ pastAiError }}</div>
              <div v-else-if="pastAiSummary" class="mono">{{ pastAiSummary }}</div>
              <div v-else>Awaiting birth interpretation.</div>
            </div>
          </section>

          <section class="panel">
            <div class="panelHeader">
              <div>
                <div class="secTitle">Present (Moment)</div>
                <div class="organLine">Organ: <strong>{{ presentOrgan }}</strong></div>
              </div>
              <div class="panelControls">
                <input class="input inlineInput" type="datetime-local" v-model="presentDatetimeLocal" />
                <button class="btn small" :class="{ primary: presentAuto }" @click="presentAuto = !presentAuto">
                  Auto {{ presentAuto ? "On" : "Off" }}
                </button>
                <button class="btn small" @click="shiftPresentHours(-2)">◀</button>
                <button class="btn small" @click="shiftPresentHours(2)">▶</button>
              </div>
            </div>

            <div class="pillarGrid">
              <div class="pillarBox">
                <div class="pillarLabel">Year</div>
                <div class="pillarGz cjkText">{{ formatGanZhiLines(temporalHex.year.ganzhi) }}</div>
                <div
                  class="pillarHex"
                  :class="{ clickable: !!temporalHex.year.hex.num }"
                  role="button"
                  :tabindex="temporalHex.year.hex.num ? 0 : -1"
                  :aria-disabled="!temporalHex.year.hex.num"
                  @click="openHexModal(temporalHex.year.hex)"
                  @keydown.enter.prevent="openHexModal(temporalHex.year.hex)"
                  @keydown.space.prevent="openHexModal(temporalHex.year.hex)"
                >
                  <div class="hexNum">#{{ temporalHex.year.hex.num ?? "—" }}</div>
                  <HexagramLines :binary="temporalHex.year.hex.binary" size="sm" />
                  <div class="hexName cjkText">
                    {{ hexNameShort(temporalHex.year.hex.num ?? null, temporalHex.year.hex.nameCn) }}
                  </div>
                </div>
              </div>
              <div class="pillarBox">
                <div class="pillarLabel">Month</div>
                <div class="pillarGz cjkText">{{ formatGanZhiLines(temporalHex.month.ganzhi) }}</div>
                <div
                  class="pillarHex"
                  :class="{ clickable: !!temporalHex.month.hex.num }"
                  role="button"
                  :tabindex="temporalHex.month.hex.num ? 0 : -1"
                  :aria-disabled="!temporalHex.month.hex.num"
                  @click="openHexModal(temporalHex.month.hex)"
                  @keydown.enter.prevent="openHexModal(temporalHex.month.hex)"
                  @keydown.space.prevent="openHexModal(temporalHex.month.hex)"
                >
                  <div class="hexNum">#{{ temporalHex.month.hex.num ?? "—" }}</div>
                  <HexagramLines :binary="temporalHex.month.hex.binary" size="sm" />
                  <div class="hexName cjkText">
                    {{ hexNameShort(temporalHex.month.hex.num ?? null, temporalHex.month.hex.nameCn) }}
                  </div>
                </div>
              </div>
              <div class="pillarBox">
                <div class="pillarLabel">Day</div>
                <div class="pillarGz cjkText">{{ formatGanZhiLines(temporalHex.day.ganzhi) }}</div>
                <div
                  class="pillarHex"
                  :class="{ clickable: !!temporalHex.day.hex.num }"
                  role="button"
                  :tabindex="temporalHex.day.hex.num ? 0 : -1"
                  :aria-disabled="!temporalHex.day.hex.num"
                  @click="openHexModal(temporalHex.day.hex)"
                  @keydown.enter.prevent="openHexModal(temporalHex.day.hex)"
                  @keydown.space.prevent="openHexModal(temporalHex.day.hex)"
                >
                  <div class="hexNum">#{{ temporalHex.day.hex.num ?? "—" }}</div>
                  <HexagramLines :binary="temporalHex.day.hex.binary" size="sm" />
                  <div class="hexName cjkText">
                    {{ hexNameShort(temporalHex.day.hex.num ?? null, temporalHex.day.hex.nameCn) }}
                  </div>
                </div>
              </div>
              <div class="pillarBox">
                <div class="pillarLabel">Hour</div>
                <div class="pillarGz cjkText">{{ formatGanZhiLines(temporalHex.hour.ganzhi) || "—" }}</div>
                <div
                  class="pillarHex"
                  :class="{ clickable: !!temporalHex.hour.hex.num }"
                  role="button"
                  :tabindex="temporalHex.hour.hex.num ? 0 : -1"
                  :aria-disabled="!temporalHex.hour.hex.num"
                  @click="openHexModal(temporalHex.hour.hex)"
                  @keydown.enter.prevent="openHexModal(temporalHex.hour.hex)"
                  @keydown.space.prevent="openHexModal(temporalHex.hour.hex)"
                >
                  <div class="hexNum">#{{ temporalHex.hour.hex.num ?? "—" }}</div>
                  <HexagramLines :binary="temporalHex.hour.hex.binary" size="sm" />
                  <div class="hexName cjkText">
                    {{ hexNameShort(temporalHex.hour.hex.num ?? null, temporalHex.hour.hex.nameCn) }}
                  </div>
                </div>
              </div>
            </div>
            <div class="placeholder">
              <div v-if="presentAiStatus === 'loading'">Generating interpretation...</div>
              <div v-else-if="presentAiStatus === 'error'">{{ presentAiError }}</div>
              <div v-else-if="presentAiSummary" class="mono">{{ presentAiSummary }}</div>
              <div v-else>Awaiting present interpretation.</div>
            </div>
          </section>
        </div>

        <div class="sec">
          <div class="secTitle">Current (Flow)</div>
          <div class="flowHeader">
            <div class="meta" v-if="active">
              {{ active.inputs.dateISO }} • {{ active.inputs.timeHHMM }} •
              {{ active.inputs.location || "location unspecified" }}
            </div>
            <div class="meta" v-else>Generate a reading to begin.</div>
            <div class="topRight" v-if="active">
              <div class="meta">
                {{ active.meta.silence ? "No dominant signal" : `Signal strength: ${active.meta.signalStrength}` }}
              </div>
              <button class="btn small" @click="copyActive">Copy</button>
            </div>
          </div>

          <div class="secBody">
            <div v-if="aiStatus === 'loading'">Generating interpretation...</div>
            <div v-else-if="aiStatus === 'error'">{{ aiError }}</div>
            <div v-else-if="aiSummaryJson">
              <div class="aiHero" v-if="hasAiValue(aiSummaryJson.current_summary)">
                <div class="aiHeroLabel">Interpretation</div>
                <div class="aiHeroValue">{{ formatAiValue(aiSummaryJson.current_summary) }}</div>
              </div>

              <div class="aiGrid">
                <div v-if="hasAiValue(aiSummaryJson.shi)" class="aiItem">
                  <div class="aiLabel">Shi</div>
                  <div class="aiValue">{{ formatAiValue(aiSummaryJson.shi) }}</div>
                </div>
                <div v-if="hasAiValue(aiSummaryJson.shun)" class="aiItem">
                  <div class="aiLabel">Shun</div>
                  <div class="aiValue">{{ formatAiValue(aiSummaryJson.shun) }}</div>
                </div>
                <div v-if="hasAiValue(aiSummaryJson.ji)" class="aiItem">
                  <div class="aiLabel">Ji</div>
                  <div class="aiValue">{{ formatAiValue(aiSummaryJson.ji) }}</div>
                </div>
                <div v-if="hasAiValue(aiSummaryJson.recommended_modes)" class="aiItem">
                  <div class="aiLabel">Recommended Modes</div>
                  <div class="aiValue">{{ formatAiValue(aiSummaryJson.recommended_modes) }}</div>
                </div>
                <div v-if="hasAiValue(aiSummaryJson.avoid)" class="aiItem">
                  <div class="aiLabel">Avoid</div>
                  <div class="aiValue">{{ formatAiValue(aiSummaryJson.avoid) }}</div>
                </div>
                <div v-if="hasAiValue(aiSummaryJson.load_capacity)" class="aiItem">
                  <div class="aiLabel">Load / Capacity</div>
                  <div class="aiValue">{{ formatAiValue(aiSummaryJson.load_capacity) }}</div>
                </div>
                <div v-if="hasAiValue(aiSummaryJson.misalignment_signals)" class="aiItem">
                  <div class="aiLabel">Misalignment Signals</div>
                  <div class="aiValue">{{ formatAiValue(aiSummaryJson.misalignment_signals) }}</div>
                </div>
                <div v-if="hasAiValue(aiSummaryJson.self_check)" class="aiItem">
                  <div class="aiLabel">Self Check</div>
                  <div class="aiValue">{{ formatAiValue(aiSummaryJson.self_check) }}</div>
                </div>
              </div>
            </div>
            <div v-else-if="aiSummaryRaw" class="mono">
              {{ aiSummaryRaw }}
            </div>
            <div v-else>
              Generate an AI summary that blends the birth profile with the current snapshot and temporal hexagrams.
            </div>
          </div>
          <div class="secActions">
            <button class="btn small" @click="generateInterpretation" :disabled="aiStatus === 'loading'">
              Generate AI Summary
            </button>
            <div v-if="weatherStatus === 'loading'" class="meta">Fetching weather…</div>
            <div v-else-if="weatherStatus === 'error'" class="meta">{{ weatherError }}</div>
          </div>
          <div class="secBody" style="margin-top: 10px;">
            <div class="qimenScope">
              <button class="btn small" :class="{ primary: qimenScope === 'hour' }" @click="qimenScope = 'hour'">
                Hour Chart
              </button>
              <button class="btn small" :class="{ primary: qimenScope === 'day' }" @click="qimenScope = 'day'">
                Day Chart
              </button>
            </div>
            <QimenChart :chart="qimenChart" />
          </div>
        </div>

        <div class="sec">
          <div class="secTitle">Future (Destiny)</div>
          <div class="secBody">
            <textarea class="destinyBox" placeholder="Destiny is yours to write."></textarea>
          </div>
        </div>
      </div>
      </main>
      <HexagramModal
        :open="isHexModalOpen"
        :hex-num="selectedHexNum"
        :hex-name="selectedHexDisplayName"
        :summaries="selectedHexSummary"
        @close="closeHexModal"
      />
    </div>
  </div>
</template>

<style>
:root {
  --b: rgba(0,0,0,0.12);
  --b2: rgba(0,0,0,0.18);
  --bg: rgba(0, 0, 0, 0.04);
  --txt: rgba(255, 255, 255, 0.88);
  --muted: rgba(255, 255, 255, 0.62);
}

#app{
  background-color: rgb(0, 58, 173);
}

.wrap {
  display: flex;
  min-height: 100vh;
  gap: 18px;
  padding: 18px;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial,
    "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
  color: var(--txt);
}

.appRoot {
  display: grid;
  gap: 12px;
}

.appHeader {
  padding: 18px 18px 0 18px;
  display: grid;
  gap: 6px;
}

.appHeader .title {
  font-size: 20px;
  font-weight: 800;
  color: var(--txt);
}

.subtitle {
  font-size: 14px;
  color: var(--txt);
  opacity: 0.9;
}

.side {
  width: 240px;
  border: 1px solid var(--b);
  border-radius: 12px;
  padding: 14px;
  overflow: auto;
}

.title { font-size: 16px; font-weight: 700; }
.sub { font-size: 12px; color: var(--muted); margin-top: 6px; }

.controls { display: grid; gap: 10px; margin-top: 14px; }

.lbl { font-size: 12px; display: grid; gap: 6px; }
.input {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--b2);
  border-radius: 10px;
  outline: none;
  background-color: rgb(173, 0, 40);
}

.btn {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--b2);
  background: transparent;
  cursor: pointer;
}
.btn.primary { background: var(--bg); font-weight: 700; }
.btn.small { padding: 8px 10px; font-size: 12px; }

.sectionHdr {
  margin-top: 16px;
  font-size: 12px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--muted);
}

.recent { margin-top: 10px; display: grid; gap: 8px; }
.empty { font-size: 13px; color: var(--muted); }

.item {
  text-align: left;
  padding: 10px;
  border-radius: 10px;
  border: 1px solid var(--b);
  background: transparent;
  cursor: pointer;
}
.item.active { border-color: rgba(0,0,0,0.35); background: var(--bg); }
.itemTitle { font-size: 13px; font-weight: 700; }
.itemSub, .itemMeta { font-size: 12px; color: var(--muted); margin-top: 4px; }

.main { flex: 1; display: flex; }
.card {
  border: 1px solid var(--b);
  border-radius: 12px;
  padding: 18px;
  max-width: 1200px;
  width: 100%;
}

.topSections {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.panel {
  border: 1px solid var(--b);
  border-radius: 12px;
  padding: 12px;
  background: rgba(255,255,255,0.02);
  display: grid;
  gap: 12px;
  overflow-x: auto;
}

.panelHeader {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  flex-wrap: wrap;
}

.panelControls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
}

.organLine {
  font-size: 12px;
  color: var(--muted);
  margin-top: 4px;
}

.inlineLbl {
  display: grid;
  gap: 6px;
  font-size: 12px;
}

.inlineInput {
  min-width: 180px;
}

.inlineSelect {
  min-width: 110px;
}

.pillarGrid {
  display: grid;
  grid-template-columns: repeat(4, minmax(130px, 1fr));
  gap: 10px;
  min-width: 560px;
}

.pillarBox {
  border: 1px solid var(--b2);
  border-radius: 10px;
  padding: 8px;
  display: grid;
  gap: 8px;
  background: rgba(0,0,0,0.15);
}

.pillarLabel {
  font-size: 11px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--muted);
}

.pillarGz {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  white-space: pre-line;
  line-height: 1.25;
}

.pillarHex {
  display: grid;
  grid-template-columns: minmax(28px, auto) 1fr minmax(28px, auto);
  gap: 6px;
  align-items: center;
}

.pillarHex.clickable {
  cursor: pointer;
}
.pillarHex.clickable:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.6);
  outline-offset: 3px;
  border-radius: 8px;
}

.hexNum {
  font-size: 12px;
  color: var(--muted);
  min-width: 28px;
}

.hexName {
  font-size: 12px;
  color: var(--muted);
  text-align: right;
  min-width: 28px;
}

.cjkText {
  font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei",
    ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}

.destinyBox {
  width: 100%;
  min-height: 140px;
  background: rgba(0,0,0,0.15);
  border: 1px solid var(--b2);
  border-radius: 10px;
  padding: 10px;
  color: var(--txt);
  resize: vertical;
}

.placeholder {
  font-size: 12px;
  color: var(--muted);
  padding: 8px 0;
}

.flowHeader {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  flex-wrap: wrap;
  margin-bottom: 8px;
}


.cardTop { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
.h1 { font-size: 20px; font-weight: 800; }
.meta { font-size: 13px; color: var(--muted); margin-top: 4px; }
.topRight { display: flex; gap: 10px; align-items: center; }

.intro { margin-top: 18px; font-size: 15px; color: var(--muted); line-height: 1.45; }

.sec { margin-top: 14px; }
.secTitle {
  font-size: 14px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--muted);
}
.secBody { margin-top: 6px; font-size: 15px; line-height: 1.45; }
.secActions { margin-top: 10px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

.aiHero {
  padding: 12px 14px;
  border: 1px solid var(--b);
  border-radius: 12px;
  background: var(--bg);
  margin-bottom: 12px;
}
.aiHeroLabel {
  font-size: 12px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.aiHeroValue { margin-top: 8px; font-size: 16px; line-height: 1.5; }

.aiGrid { display: grid; gap: 10px; }
.aiItem { padding: 8px 10px; border: 1px solid var(--b); border-radius: 10px; }
.aiLabel { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.4px; }
.aiValue { margin-top: 6px; font-size: 14px; line-height: 1.45; }
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New",
    "Noto Sans Mono CJK SC", "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Noto Sans SC",
    "Microsoft YaHei", monospace;
}

@media (max-width: 980px) {
  .wrap {
    flex-direction: column;
  }

  .side {
    width: 100%;
  }

  .main {
    width: 100%;
  }

  .card {
    max-width: 100%;
  }
}

@media (max-width: 680px) {
  .wrap {
    padding: 12px;
    gap: 12px;
  }

  .appHeader {
    padding: 12px 12px 0 12px;
  }

  .panel {
    padding: 10px;
  }

  .panelHeader {
    align-items: flex-start;
  }

  .panelControls {
    width: 100%;
    justify-content: flex-start;
  }

  .inlineInput,
  .inlineSelect {
    min-width: 0;
    width: 100%;
  }

  .pillarGrid {
    grid-template-columns: repeat(2, minmax(120px, 1fr));
    min-width: 0;
  }

  .topRight {
    flex-wrap: wrap;
    justify-content: flex-start;
  }
}
</style>