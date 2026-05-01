import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import { Geolocation } from "@capacitor/geolocation";
import { serializeAdvancedAstro } from "@/core/advancedAstro";
import { buildQimenChart } from "@/core/qimen";
import { getTemporalXkdg } from "@/core/hexagramsXKDG";
import {
  computeBirthProfile,
  parseDatetimeLocal,
  type BirthProfileResult,
  type Sect,
} from "@/lib/personal/baziNineStar";
import { generateZWDSMatrix, type ZWDSGender } from "@/core/zwds";
import { buildSystemPrompt, fetchDaoistReading } from "@/services/intelligenceService";
import { fetchContractBoundChat, hasLlmKey } from "@/services/llmService";
import { synthesizeHeavens } from "@/services/oracle";
import { useAlchemyStore } from "@/stores/alchemyStore";
import { Lunar, LunarMonth, Solar } from "lunar-typescript";
import { getTrueSolarTime } from "@/utils/solarTime";
import { getShichenDetail } from "@/core/shichenDetail";
import { getCurrentOrganHour } from "@/data/organClock";
import {
  DEFAULT_WAVE_VARIANT_ID,
  isWaveVariantId,
  LEGACY_WAVE_VARIANT_FLASH_RIPPLE,
  type WaveVariantId,
} from "@/components/waves/waveVariants";
import {
  DEFAULT_LANGUAGE,
  migrateLegacyLanguage,
  type LanguageCode,
} from "@/lib/languages";

// --- Types ---
type SignalStrength = "none" | "weak" | "moderate" | "dominant";

export type Reading = {
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

export type WeatherSnapshot = {
  temp_f: number | null;
  precip: number | null;
  wind: number | null;
  notes: string | null;
};

export type GeoCoords = { lat: number; lon: number };
/**
 * Task 12.3/12.3b/12.4: Preferred language for pronunciation display.
 * Sourced from the language registry in `src/lib/languages.ts`.
 *
 * `PreferredDialect` is kept as a deprecated alias for back-compat with any
 * external callers; new code should use `PreferredLanguage`.
 */
export type PreferredLanguage = LanguageCode;
/** @deprecated Renamed to `PreferredLanguage`. Will be removed in a future release. */
export type PreferredDialect = PreferredLanguage;

// --- Constants ---
const LS_KEY = "current_almanac_log_v0";
const LS_KEY_USER_STATE = "current_almanac_user_state_v1";
const LS_KEY_BIRTH_DT = "current.birth.datetimeLocal";
const LS_KEY_BIRTH_SECT = "current.birth.sect";

function safeLocalStorageGet(key: string): string | null {
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
    // ignore
  }
}

function toDateISO(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function toHHMM(d: Date) {
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  return `${h}:${m}`;
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

function normalizeDatetimeLocal(raw: string) {
  if (!raw) return "1990-01-01T12:00";
  try {
    parseDatetimeLocal(raw);
    return raw;
  } catch {
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return "1990-01-01T12:00";
    return `${toDateISO(d)}T${toHHMM(d)}`;
  }
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

function solarToDate(solar: Solar) {
  return new Date(solar.toYmdHms().replace(" ", "T"));
}

function normalizeOptionalNumber(value: number | null) {
  return Number.isFinite(value ?? NaN) ? value : null;
}

// --- Reading generation (from App.vue) ---
type Band = "low" | "moderate" | "high";
type Timing = "premature" | "neutral" | "ripe";

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
    signalStrength === "none" ||
    (signalStrength === "weak" && timing === "neutral" && load !== "low");

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

  return enforceConstraints({
    id: uid(),
    createdAtISO: new Date().toISOString(),
    inputs: { ...input },
    meta: { signalStrength, silence },
    sections: { snapshot, dynamics, misalignment, capacity, phase, notes },
  });
}

// --- Store ---
export const useAppStore = defineStore("app", () => {
  // Moment
  const dateISO = ref(isoToday());
  const timeHHMM = ref(hhmmNow());
  const location = ref("");
  const geoCoords = ref<GeoCoords | null>(null);
  const timezoneLabel = ref("unknown");
  const presentAuto = ref(true);
  /** Location sync status for UI: idle | loading | resolved | denied | error */
  const geoStatus = ref<"idle" | "loading" | "resolved" | "denied" | "error">("idle");
  /** Source: auto (geolocation) or manual (user override) */
  const geoSource = ref<"auto" | "manual">("auto");

  // Birth
  const birthDatetimeLocal = ref<string>(
    normalizeDatetimeLocal(safeLocalStorageGet(LS_KEY_BIRTH_DT) ?? "1990-01-01T12:00")
  );
  const birthSect = ref<Sect>((Number(safeLocalStorageGet(LS_KEY_BIRTH_SECT)) as Sect) || 2);
  /** Task 12.5: Birth location (city name) for display. */
  const birthLocationName = ref("");
  /** Task 12.5: Birth longitude for True Solar Time on natal chart. null = not set. */
  const birthLongitude = ref<number | null>(null);
  /** For ZWDS; not rendered in UI. Default "male" when unknown. */
  const userGender = ref<ZWDSGender>("male");

  // User State (Task 12.1: sane defaults)
  const intentDomain = ref("General Wellness");
  const intentGoalConstraint = ref("General wellness and balance.");
  const userCapacity = ref<number | null>(6);
  const userLoad = ref<number | null>(4);
  const userSleepQuality = ref<number | null>(6);
  const userCognitiveNoise = ref<number | null>(3);
  const userSocialLoad = ref<number | null>(4);
  const userEmotionalTone = ref("Steady, focused, lightly distracted.");
  const preferredLanguage = ref<PreferredLanguage>(DEFAULT_LANGUAGE);

  /** Task 12.4: True Solar Time (Local Apparent Time) — EoT + longitude offset. Default off. */
  const useTrueSolarTime = ref(false);
  /** Task 12.5: Date format for bounds display. US | EU | ASIAN. */
  const dateFormat = ref<"US" | "EU" | "ASIAN">("US");

  /** Home wave background variant (calming water layer). */
  const waveVariantId = ref<WaveVariantId>(DEFAULT_WAVE_VARIANT_ID);
  /** Ambient brook audio when variant supports it (user toggle). */
  const waveAudioEnabled = ref(false);
  /** Click/tap ripple overlay (independent of water style). */
  const waveRippleClicksEnabled = ref(true);

  // Readings
  const log = ref<Reading[]>([]);
  const activeReading = ref<Reading | null>(null);

  // Interpretation stub state (replaces AI)
  const interpretationPlaceholder = ref<string | null>(null);
  const interpretationLoading = ref(false);
  /** Signature of BaZi state when we last generated interpretation. */
  const interpretationBaZiSignature = ref<string | null>(null);

  // Task 12.2 — Oracle Engine: baseline summaries (auto-generated) and Current Flow synthesis
  const pastSummary = ref<string | null>(null);
  const presentSummary = ref<string | null>(null);
  const pastSummaryLoading = ref(false);
  const presentSummaryLoading = ref(false);
  const pastSummarySignature = ref<string | null>(null);
  const presentSummarySignature = ref<string | null>(null);
  const currentFlowAnalysis = ref<string | null>(null);
  const currentFlowLoading = ref(false);

  // Phase notes — user-owned free-form notes on the longer arc.
  // Persisted via persistUserState. NOT generated by the LLM.
  const userPhaseNotes = ref("");
  // Legacy: kept for back-compat on `generateDaoistReading()` callers.
  const generatedReading = ref("");
  const isGenerating = ref(false);

  // Computed: selected date
  const selectedDate = computed(() => {
    return new Date(`${dateISO.value}T${timeHHMM.value}:00`);
  });

  /** Longitude for True Solar Time (from geoCoords). null when unresolved. */
  const longitude = computed<number | null>(() => {
    const c = geoCoords.value;
    return c && Number.isFinite(c.lon) ? c.lon : null;
  });

  /**
   * Apply True Solar Time (EoT + longitude offset) when useTrueSolarTime and longitude are set.
   * Otherwise returns raw selectedDate.
   */
  const solarAdjustedSelectedDate = computed(() => {
    const date = selectedDate.value;
    const lon = longitude.value;
    if (!useTrueSolarTime.value || lon === null) return date;
    return getTrueSolarTime(date, lon);
  });

  // Computed: birth profile
  const birthProfile = computed<BirthProfileResult | null>(() => {
    try {
      const input = parseDatetimeLocal(birthDatetimeLocal.value);
      return computeBirthProfile(input, birthSect.value);
    } catch {
      return null;
    }
  });

  // Computed: temporal hex (present moment) — uses True Solar Time when geoCoords available
  const temporalHex = computed(() => getTemporalXkdg(solarAdjustedSelectedDate.value));

  /** Chu / Zheng / Ke subdivisions (15-minute Ke); uses solar-adjusted moment when TST on. */
  const presentShichenDetail = computed(() => getShichenDetail(solarAdjustedSelectedDate.value));

  /** Changes every Ke (~15 min); independent of BaZi hour pillar. */
  const presentKeSignature = computed(() => {
    const d = presentShichenDetail.value;
    return `${d.branchCn}|${d.chuZheng}|${d.keInShichen}|${d.keBoundsDisplay}`;
  });

  /** BaZi pillar signatures — only change when year/month/day/hour pillars change (e.g. crossing 2h organ block). */
  const presentBaziSignature = computed(() => {
    const h = temporalHex.value;
    return `${h.year.ganzhi}|${h.month.ganzhi}|${h.day.ganzhi}|${h.hour.ganzhi}`;
  });
  const pastBaziSignature = computed(() => {
    const h = birthTemporalHex.value;
    return h ? `${h.year.ganzhi}|${h.month.ganzhi}|${h.day.ganzhi}|${h.hour.ganzhi}` : "";
  });

  // Computed: birth temporal hex
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
    const baseDate = birthInputToDate(b.input);
    const effectiveDate =
      useTrueSolarTime.value && birthLongitude.value != null
        ? getTrueSolarTime(baseDate, birthLongitude.value)
        : baseDate;
    return getTemporalXkdg(effectiveDate);
  });

  // Computed: qimen charts
  const qimenChartHour = computed(() => buildQimenChart(selectedDate.value, "hour"));
  const qimenChartDay = computed(() => buildQimenChart(selectedDate.value, "day"));

  // Computed: advanced astro firehose (moment - for present-moment context) — True Solar Time when geoCoords available
  const advancedAstroMoment = computed(() => {
    try {
      const date = solarAdjustedSelectedDate.value;
      const solar = Solar.fromDate(date);
      const lunar = Lunar.fromSolar(solar);
      const eightChar = lunar.getEightChar();
      eightChar.setSect(birthSect.value);
      return serializeAdvancedAstro(lunar, eightChar, birthSect.value);
    } catch {
      return null;
    }
  });

  // Computed: advanced astro firehose (birth - for natal context)
  const advancedAstroBirth = computed(() => {
    const b = birthProfile.value;
    if (!b) return null;
    try {
      const solar = Solar.fromYmdHms(
        b.input.year,
        b.input.month,
        b.input.day,
        b.input.hour,
        b.input.minute ?? 0,
        b.input.second ?? 0
      );
      const lunar = Lunar.fromSolar(solar);
      const eightChar = lunar.getEightChar();
      eightChar.setSect(birthSect.value);
      return serializeAdvancedAstro(lunar, eightChar, birthSect.value);
    } catch {
      return null;
    }
  });

  // Computed: Zi Wei Dou Shu matrix (from birth; for hidden AI payload)
  const zwdsMatrix = computed(() => {
    const b = birthProfile.value;
    if (!b) return null;
    return generateZWDSMatrix(
      b.input.year,
      b.input.month,
      b.input.day,
      b.input.hour,
      userGender.value
    );
  });

  // Computed: present datetime local (getter/setter via actions)
  const presentDatetimeLocal = computed({
    get: () => `${dateISO.value}T${timeHHMM.value}`,
    set: (value: string) => {
      if (!value || !value.includes("T")) return;
      const [d, t] = value.split("T");
      if (!d || !t) return;
      dateISO.value = d;
      timeHHMM.value = t.slice(0, 5);
      presentAuto.value = false;
    },
  });

  // Computed: present organ (same clock basis as temporal hex / shichen detail)
  const presentOrgan = computed(() => {
    const h = solarAdjustedSelectedDate.value.getHours();
    return getCurrentOrganHour(h).organ;
  });

  // Computed: sorted log
  const sortedLog = computed(() =>
    [...log.value].sort((a, b) => (a.createdAtISO < b.createdAtISO ? 1 : -1))
  );

  /** Current BaZi signature (birth + present). Used to detect when interpretation is stale. */
  const currentBaZiSignature = computed(
    () => `${birthDatetimeLocal.value}|${dateISO.value}|${timeHHMM.value}`
  );

  /** True when we need to regenerate (no interpretation yet, or BaZi changed). */
  const interpretationNeedsRefresh = computed(() => {
    const sig = interpretationBaZiSignature.value;
    const cur = currentBaZiSignature.value;
    return !sig || sig !== cur;
  });

  // Actions
  function loadFromStorage() {
    const rawLog = localStorage.getItem(LS_KEY);
    if (rawLog) {
      try {
        const parsed = JSON.parse(rawLog) as Reading[];
        log.value = Array.isArray(parsed) ? parsed.sort((a, b) => (a.createdAtISO < b.createdAtISO ? 1 : -1)) : [];
        activeReading.value = log.value[0] ?? null;
      } catch {
        log.value = [];
        activeReading.value = null;
      }
    }
    const saved = localStorage.getItem(LS_KEY_USER_STATE);
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as Record<string, unknown>;
        if (parsed && typeof parsed === "object") {
          if (typeof parsed.intentDomain === "string") intentDomain.value = parsed.intentDomain;
          if (typeof parsed.intentGoalConstraint === "string")
            intentGoalConstraint.value = parsed.intentGoalConstraint;
          if (Number.isFinite(parsed.userCapacity)) userCapacity.value = parsed.userCapacity as number;
          if (Number.isFinite(parsed.userLoad)) userLoad.value = parsed.userLoad as number;
          if (Number.isFinite(parsed.userSleepQuality)) userSleepQuality.value = parsed.userSleepQuality as number;
          if (Number.isFinite(parsed.userCognitiveNoise))
            userCognitiveNoise.value = parsed.userCognitiveNoise as number;
          if (Number.isFinite(parsed.userSocialLoad)) userSocialLoad.value = parsed.userSocialLoad as number;
          if (typeof parsed.userEmotionalTone === "string") userEmotionalTone.value = parsed.userEmotionalTone;
          if (typeof parsed.useTrueSolarTime === "boolean") useTrueSolarTime.value = parsed.useTrueSolarTime;
          if (typeof parsed.userPhaseNotes === "string") userPhaseNotes.value = parsed.userPhaseNotes;
          if (typeof parsed.birthLocationName === "string") birthLocationName.value = parsed.birthLocationName;
          if (Number.isFinite(parsed.birthLongitude)) birthLongitude.value = parsed.birthLongitude as number;
          else if (parsed.birthLongitude === null) birthLongitude.value = null;
          if (parsed.dateFormat === "US" || parsed.dateFormat === "EU" || parsed.dateFormat === "ASIAN")
            dateFormat.value = parsed.dateFormat;
          // Task 12.4: read either `preferredLanguage` (current) or legacy
          // `preferredDialect` (which may itself contain `mandarin`/`cantonese`
          // from an even older release). The registry handles all aliases.
          const rawLang =
            parsed.preferredLanguage !== undefined
              ? parsed.preferredLanguage
              : parsed.preferredDialect;
          if (rawLang !== undefined) {
            preferredLanguage.value = migrateLegacyLanguage(rawLang);
          }
          if (typeof parsed.waveVariantId === "string") {
            if (parsed.waveVariantId === LEGACY_WAVE_VARIANT_FLASH_RIPPLE) {
              waveVariantId.value = DEFAULT_WAVE_VARIANT_ID;
              waveRippleClicksEnabled.value = true;
            } else if (isWaveVariantId(parsed.waveVariantId)) {
              waveVariantId.value = parsed.waveVariantId;
            }
          }
          if (typeof parsed.waveAudioEnabled === "boolean") {
            waveAudioEnabled.value = parsed.waveAudioEnabled;
          }
          if (typeof parsed.waveRippleClicksEnabled === "boolean") {
            waveRippleClicksEnabled.value = parsed.waveRippleClicksEnabled;
          }
        }
      } catch {
        // ignore
      }
    }
  }

  function persistUserState() {
    localStorage.setItem(
      LS_KEY_USER_STATE,
      JSON.stringify({
        intentDomain: intentDomain.value,
        intentGoalConstraint: intentGoalConstraint.value,
        userCapacity: userCapacity.value,
        userLoad: userLoad.value,
        userSleepQuality: userSleepQuality.value,
        userCognitiveNoise: userCognitiveNoise.value,
        userSocialLoad: userSocialLoad.value,
        userEmotionalTone: userEmotionalTone.value,
        userPhaseNotes: userPhaseNotes.value,
        preferredLanguage: preferredLanguage.value,
        useTrueSolarTime: useTrueSolarTime.value,
        birthLocationName: birthLocationName.value,
        birthLongitude: birthLongitude.value,
        dateFormat: dateFormat.value,
        waveVariantId: waveVariantId.value,
        waveAudioEnabled: waveAudioEnabled.value,
        waveRippleClicksEnabled: waveRippleClicksEnabled.value,
      })
    );
  }

  function setWaveVariant(id: WaveVariantId) {
    waveVariantId.value = id;
  }

  function setWaveAudioEnabled(enabled: boolean) {
    waveAudioEnabled.value = enabled;
  }

  function setWaveRippleClicksEnabled(enabled: boolean) {
    waveRippleClicksEnabled.value = enabled;
  }

  function syncLocalTimeNow(force = false) {
    if (!force && !presentAuto.value) return;
    const now = new Date();
    dateISO.value = toDateISO(now);
    timeHHMM.value = toHHMM(now);
  }

  async function hydrateFromGeolocation() {
    geoStatus.value = "loading";
    geoSource.value = "auto";
    try {
      const pos = await Geolocation.getCurrentPosition({
        enableHighAccuracy: false,
        timeout: 8000,
        maximumAge: 60000,
      });
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      geoCoords.value = { lat, lon };
      try {
        const res = await fetch(
          `https://geocoding-api.open-meteo.com/v1/reverse?latitude=${lat}&longitude=${lon}&language=en&format=json`
        );
        if (res.ok) {
          const data = await res.json();
          const result = data?.results?.[0];
          if (result)
            location.value =
              `${result.name}${result.admin1 ? `, ${result.admin1}` : ""}${result.country ? `, ${result.country}` : ""}`;
        }
      } catch {
        // ignore reverse geocode
      }
      timezoneLabel.value = Intl.DateTimeFormat().resolvedOptions().timeZone || "unknown";
      geoStatus.value = "resolved";
    } catch {
      // Permission denied or API failed — fallback to ipapi
      try {
        const res = await fetch("https://ipapi.co/json/");
        if (res.ok) {
          const data = await res.json();
          const lat = Number(data?.latitude);
          const lon = Number(data?.longitude);
          if (Number.isFinite(lat) && Number.isFinite(lon)) {
            geoCoords.value = { lat, lon };
            const name = [data?.city, data?.region, data?.country_name].filter(Boolean).join(", ");
            if (name) location.value = name;
            if (typeof data?.timezone === "string") timezoneLabel.value = data.timezone;
            geoStatus.value = "resolved";
          } else {
            geoStatus.value = "error";
          }
        } else {
          geoStatus.value = "error";
        }
      } catch {
        geoStatus.value = "error";
      }
    }
  }

  function setManualLocation(value: string) {
    geoSource.value = "manual";
    location.value = value || "";
  }

  function setManualTimezone(value: string) {
    geoSource.value = "manual";
    timezoneLabel.value = value || "unknown";
  }

  function setManualGeoCoords(coords: GeoCoords | null) {
    geoSource.value = "manual";
    geoCoords.value = coords;
  }

  async function fetchWeatherSnapshot(): Promise<WeatherSnapshot | null> {
    const coords = geoCoords.value;
    if (!coords) return null;
    try {
      const url =
        `https://api.open-meteo.com/v1/forecast?latitude=${coords.lat}&longitude=${coords.lon}` +
        `&current=temperature_2m,precipitation,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph`;
      const res = await fetch(url);
      if (!res.ok) return null;
      const data = await res.json();
      const current = data?.current ?? {};
      return {
        temp_f: Number.isFinite(current.temperature_2m) ? current.temperature_2m : null,
        precip: Number.isFinite(current.precipitation) ? current.precipitation : null,
        wind: Number.isFinite(current.wind_speed_10m) ? current.wind_speed_10m : null,
        notes: null,
      };
    } catch {
      return null;
    }
  }

  function togglePresentAuto() {
    presentAuto.value = !presentAuto.value;
  }

  function shiftPresentHours(deltaHours: number) {
    presentAuto.value = false;
    const base = new Date(`${dateISO.value}T${timeHHMM.value}:00`);
    base.setHours(base.getHours() + deltaHours);
    dateISO.value = toDateISO(base);
    timeHHMM.value = toHHMM(base);
  }

  function generate() {
    const r = generateReading({
      dateISO: dateISO.value,
      timeHHMM: timeHHMM.value,
      location: location.value,
    });
    log.value = [r, ...log.value].slice(0, 50);
    activeReading.value = r;
    localStorage.setItem(LS_KEY, JSON.stringify(log.value.slice(0, 50)));
  }

  function clearLog() {
    log.value = [];
    activeReading.value = null;
    localStorage.removeItem(LS_KEY);
  }

  function setActiveReading(r: Reading | null) {
    activeReading.value = r;
  }

  function setGeneratedReading(value: string) {
    generatedReading.value = value;
  }

  async function generateDaoistReading() {
    isGenerating.value = true;
    generatedReading.value = "";
    try {
      const alchemyStore = useAlchemyStore();
      const systemPrompt = buildSystemPrompt(useAppStore(), alchemyStore);
      const text = await fetchDaoistReading(systemPrompt);
      generatedReading.value = text;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to generate reading.";
      generatedReading.value = `Error: ${msg}`;
      console.error("[generateDaoistReading]", err);
    } finally {
      isGenerating.value = false;
    }
  }

  const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "";

  async function requestInterpretation() {
    interpretationLoading.value = true;
    interpretationPlaceholder.value = null;
    try {
      const snapshot = await fetchWeatherSnapshot();
      const payload = serializeForApi(snapshot);
      if (!payload) {
        interpretationPlaceholder.value =
          "Enter a valid birth datetime to interpret.";
        return;
      }
      const url = `${API_BASE || ""}/api/interpret`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        if (res.status === 404 && hasLlmKey()) {
          try {
            const text = await interpretViaDeepSeekDirect();
            interpretationPlaceholder.value = text;
            interpretationBaZiSignature.value = currentBaZiSignature.value;
          } catch (fallbackErr) {
            interpretationPlaceholder.value =
              "Backend 404. Direct DeepSeek failed: " +
              (fallbackErr instanceof Error ? fallbackErr.message : String(fallbackErr));
            console.error("[requestInterpretation 404 fallback]", fallbackErr);
          }
          return;
        }
        const text = await res.text();
        throw new Error(`API error (${res.status}): ${text || res.statusText}`);
      }
      const data = (await res.json()) as {
        current_summary?: string | null;
        shi?: string | null;
        shun?: string | null;
        ji?: string | null;
        load_capacity?: string | null;
        misalignment_signals?: string | null;
        recommended_modes?: string | null;
        avoid?: string | null;
        self_check?: string | null;
      };
      const parts: string[] = [];
      if (data.current_summary) parts.push(data.current_summary);
      if (data.shi) parts.push(`Shi: ${data.shi}`);
      if (data.shun) parts.push(`Shun: ${data.shun}`);
      if (data.ji) parts.push(`Ji: ${data.ji}`);
      if (data.load_capacity) parts.push(`Load/Capacity: ${data.load_capacity}`);
      if (data.recommended_modes) parts.push(`Recommended: ${data.recommended_modes}`);
      if (data.avoid) parts.push(`Avoid: ${data.avoid}`);
      interpretationPlaceholder.value =
        parts.length > 0 ? parts.join("\n\n") : "Interpretation received (no content yet).";
      interpretationBaZiSignature.value = currentBaZiSignature.value;
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Failed to get interpretation.";
      const is404 = errMsg.includes("404");
      if (is404 && hasLlmKey()) {
        try {
          const text = await interpretViaDeepSeekDirect();
          interpretationPlaceholder.value = text;
          interpretationBaZiSignature.value = currentBaZiSignature.value;
        } catch (fallbackErr) {
          interpretationPlaceholder.value =
            errMsg + " (Direct DeepSeek also failed: " + (fallbackErr instanceof Error ? fallbackErr.message : String(fallbackErr)) + ")";
          console.error("[requestInterpretation fallback]", fallbackErr);
        }
      } else {
        interpretationPlaceholder.value = errMsg;
        console.error("[requestInterpretation]", err);
      }
    } finally {
      interpretationLoading.value = false;
    }
  }

  /** Fallback when backend returns 404 — call DeepSeek directly. Contract-bound. */
  async function interpretViaDeepSeekDirect(): Promise<string> {
    const payload = serializeForApi(null);
    if (!payload) throw new Error("No payload");
    const userPrompt = [
      "Describe how the natal BaZi configuration interacts with the present moment.",
      "Treat the JSON as canonical; do not recompute math.",
      "Identify dominant dynamics (what is increasing / decreasing) and the interaction pattern",
      "(what happens if force is applied). 2–4 short paragraphs.",
      "",
      JSON.stringify(payload, null, 2),
    ].join("\n");
    return fetchContractBoundChat(
      [{ role: "user", content: userPrompt }],
      { maxTokens: 600, temperature: 0.3 }
    );
  }

  /** Task 12.2: Lightweight Past (Birth) summary. Silent, auto-triggered. */
  async function requestPastSummary() {
    if (!hasLlmKey()) {
      console.debug("[requestPastSummary] No LLM key — add VITE_DEEPSEEK_API_KEY or VITE_LLM_API_KEY to .env");
      return;
    }
    const sig = pastBaziSignature.value;
    if (!sig || pastSummarySignature.value === sig) return;
    const hex = birthTemporalHex.value;
    if (!hex) return;
    pastSummarySignature.value = sig;
    pastSummaryLoading.value = true;
    try {
      const json = JSON.stringify({
        year: hex.year.ganzhi,
        month: hex.month.ganzhi,
        day: hex.day.ganzhi,
        hour: hex.hour.ganzhi,
        hexagrams: {
          year: hex.year.hex?.num,
          month: hex.month.hex?.num,
          day: hex.day.hex?.num,
          hour: hex.hour.hex?.num,
        },
      });
      const text = await fetchContractBoundChat(
        [
          {
            role: "user",
            content:
              "Describe the configuration of this natal Four Pillars chart in 2–3 sentences. " +
              "Treat the JSON as canonical (no recomputation). Note dominant dynamics.\n\n" +
              json,
          },
        ],
        { maxTokens: 200, temperature: 0.3 }
      );
      pastSummary.value = text?.trim() || null;
    } catch (err) {
      pastSummarySignature.value = null;
      const msg = err instanceof Error ? err.message : String(err);
      pastSummary.value = `Summary failed: ${msg}`;
      console.error("[requestPastSummary] API error:", err);
    } finally {
      pastSummaryLoading.value = false;
    }
  }

  /** Task 12.2: Lightweight Present (Moment) summary. Silent, auto-triggered. */
  async function requestPresentSummary() {
    if (!hasLlmKey()) {
      console.debug("[requestPresentSummary] No LLM key — add VITE_DEEPSEEK_API_KEY or VITE_LLM_API_KEY to .env");
      return;
    }
    const sig = presentBaziSignature.value;
    if (presentSummarySignature.value === sig) return;
    const hex = temporalHex.value;
    presentSummarySignature.value = sig;
    presentSummaryLoading.value = true;
    try {
      const json = JSON.stringify({
        year: hex.year.ganzhi,
        month: hex.month.ganzhi,
        day: hex.day.ganzhi,
        hour: hex.hour.ganzhi,
        organ: presentOrgan.value,
        hexagrams: {
          year: hex.year.hex?.num,
          month: hex.month.hex?.num,
          day: hex.day.hex?.num,
          hour: hex.hour.hex?.num,
        },
      });
      const text = await fetchContractBoundChat(
        [
          {
            role: "user",
            content:
              "Describe the configuration of this present-moment chart and the active meridian " +
              "in 2–3 sentences. Treat the JSON as canonical. Note dominant dynamics.\n\n" +
              json,
          },
        ],
        { maxTokens: 200, temperature: 0.3 }
      );
      presentSummary.value = text?.trim() || null;
    } catch (err) {
      presentSummarySignature.value = null;
      const msg = err instanceof Error ? err.message : String(err);
      presentSummary.value = `Summary failed: ${msg}`;
      console.error("[requestPresentSummary] API error:", err);
    } finally {
      presentSummaryLoading.value = false;
    }
  }

  /** Task 12.2: Full synthesis — Birth + Moment + Active Meridian. The primary "Generate Current Flow" action. */
  async function requestCurrentFlowAnalysis() {
    if (!hasLlmKey()) {
      console.debug("[requestCurrentFlowAnalysis] No LLM key — add VITE_DEEPSEEK_API_KEY or VITE_LLM_API_KEY to .env");
      currentFlowAnalysis.value = null;
      return;
    }
    currentFlowLoading.value = true;
    currentFlowAnalysis.value = null;
    console.debug("[requestCurrentFlowAnalysis] Calling LLM...");
    const timeoutMs = 120_000;
    try {
      const bHex = birthTemporalHex.value;
      const mHex = temporalHex.value;
      const organ = presentOrgan.value;
      if (!bHex || !mHex) {
        currentFlowAnalysis.value = "Enter a valid birth datetime and ensure the moment is set.";
        return;
      }
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const text = await synthesizeHeavens(
          {
            natal: {
              year: bHex.year.ganzhi,
              month: bHex.month.ganzhi,
              day: bHex.day.ganzhi,
              hour: bHex.hour.ganzhi,
            },
            present: {
              year: mHex.year.ganzhi,
              month: mHex.month.ganzhi,
              day: mHex.day.ganzhi,
              hour: mHex.hour.ganzhi,
              active_meridian: organ,
            },
          },
          { signal: controller.signal }
        );
        currentFlowAnalysis.value = text?.trim() || null;
        console.debug("[requestCurrentFlowAnalysis] Success");
      } finally {
        clearTimeout(timeoutId);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      const friendlyMsg =
        msg.includes("aborted") || msg.includes("AbortError")
          ? `Request timed out (${timeoutMs / 1000}s). Try again or use a faster model (gpt-4o-mini) in .env.`
          : msg;
      currentFlowAnalysis.value = "Error: " + friendlyMsg;
      console.error("[requestCurrentFlowAnalysis]", err);
      if (msg.includes("404") || msg.includes("401") || msg.includes("403")) {
        console.warn("[requestCurrentFlowAnalysis] If using DeepSeek, verify the API URL and model. You can switch to OpenAI: set VITE_LLM_API_URL=https://api.openai.com/v1/chat/completions and VITE_LLM_MODEL=gpt-4o-mini in .env");
      }
    } finally {
      currentFlowLoading.value = false;
    }
  }

  /** Produces the payload for the FastAPI backend. Contract for Phase 2. */
  function serializeForApi(snapshot: WeatherSnapshot | null): Record<string, unknown> | null {
    const b = birthProfile.value;
    if (!b) return null;

    const hex = temporalHex.value;
    const date = selectedDate.value;
    const solar = Solar.fromDate(date);
    const lunar = Lunar.fromSolar(solar);
    const monthObj = LunarMonth.fromYm(lunar.getYear(), lunar.getMonth());
    const nextJieQi = lunar.getNextJieQi?.() ?? null;
    const nextJieQiSolar = nextJieQi ? nextJieQi.getSolar() : null;
    const daysToNext =
      nextJieQiSolar
        ? Math.max(0, Math.round((solarToDate(nextJieQiSolar).getTime() - date.getTime()) / 86400000))
        : null;

    const resolveIntent = (value: string) => value.trim() || "unknown";

    const yiTags = (lunar.getDayYi?.() ?? []) as string[];
    const jiTags = (lunar.getDayJi?.() ?? []) as string[];

    const qimenHour = qimenChartHour.value;
    const qimenDay = qimenChartDay.value;
    const serializeQimen = (chart: typeof qimenHour | null) => {
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

    const advancedAstroMom = advancedAstroMoment.value;
    const advancedAstroNat = advancedAstroBirth.value;
    const zwds = zwdsMatrix.value;

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
          shichen_detail: (() => {
            const s = presentShichenDetail.value;
            return {
              branch: s.branch,
              branch_cn: s.branchCn,
              chu_zheng: s.chuZheng,
              chu_zheng_cn: s.chuZhengLabel,
              ke_in_shichen: s.keInShichen,
              ke_in_half: s.keInHalf,
              label_cn: s.fullLabel,
              label_en: s.fullLabelEn,
              ke_bounds_local: s.keBoundsDisplay,
            };
          })(),
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
              hour: serializeQimen(qimenHour),
              day: serializeQimen(qimenDay),
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
      advanced_astro: {
        moment: advancedAstroMom,
        birth: advancedAstroNat,
      },
      zwds: zwds,
    };
  }

  watch(presentAuto, (v) => {
    if (v) syncLocalTimeNow(true);
  });

  // Persistence watchers (run after store is used in app)
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
      userPhaseNotes,
      preferredLanguage,
      useTrueSolarTime,
      waveVariantId,
      waveAudioEnabled,
      waveRippleClicksEnabled,
    ],
    () => persistUserState()
  );
  watch(birthDatetimeLocal, (v) => safeLocalStorageSet(LS_KEY_BIRTH_DT, v));
  watch(birthSect, (v) => safeLocalStorageSet(LS_KEY_BIRTH_SECT, String(v)));

  return {
    // State
    dateISO,
    timeHHMM,
    location,
    geoCoords,
    geoStatus,
    geoSource,
    timezoneLabel,
    presentAuto,
    birthDatetimeLocal,
    birthSect,
    birthLocationName,
    birthLongitude,
    dateFormat,
    intentDomain,
    intentGoalConstraint,
    userCapacity,
    userLoad,
    userSleepQuality,
    userCognitiveNoise,
    userSocialLoad,
    userEmotionalTone,
    userPhaseNotes,
    preferredLanguage,
    useTrueSolarTime,
    waveVariantId,
    waveAudioEnabled,
    waveRippleClicksEnabled,
    longitude,
    log,
    activeReading,
    interpretationPlaceholder,
    interpretationLoading,
    pastSummary,
    presentSummary,
    pastSummaryLoading,
    presentSummaryLoading,
    currentFlowAnalysis,
    currentFlowLoading,
    generatedReading,
    isGenerating,
    // Computed
    selectedDate,
    solarAdjustedSelectedDate,
    birthProfile,
    temporalHex,
    presentShichenDetail,
    presentKeSignature,
    birthTemporalHex,
    pastBaziSignature,
    presentBaziSignature,
    qimenChartHour,
    qimenChartDay,
    advancedAstroMoment,
    advancedAstroBirth,
    zwdsMatrix,
    interpretationNeedsRefresh,
    presentDatetimeLocal,
    presentOrgan,
    sortedLog,
    // Actions
    loadFromStorage,
    persistUserState,
    setWaveVariant,
    setWaveAudioEnabled,
    setWaveRippleClicksEnabled,
    syncLocalTimeNow,
    shiftPresentHours,
    hydrateFromGeolocation,
    setManualLocation,
    setManualTimezone,
    setManualGeoCoords,
    fetchWeatherSnapshot,
    togglePresentAuto,
    generate,
    generateDaoistReading,
    clearLog,
    setActiveReading,
    setGeneratedReading,
    requestInterpretation,
    requestPastSummary,
    requestPresentSummary,
    requestCurrentFlowAnalysis,
    serializeForApi,
  };
});
