import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
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
import { Lunar, LunarMonth, Solar } from "lunar-typescript";

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

  // Birth
  const birthDatetimeLocal = ref<string>(
    normalizeDatetimeLocal(safeLocalStorageGet(LS_KEY_BIRTH_DT) ?? "1990-01-01T12:00")
  );
  const birthSect = ref<Sect>((Number(safeLocalStorageGet(LS_KEY_BIRTH_SECT)) as Sect) || 2);
  /** For ZWDS; not rendered in UI. Default "male" when unknown. */
  const userGender = ref<ZWDSGender>("male");

  // User State
  const intentDomain = ref("general");
  const intentGoalConstraint = ref("Test the current conditions without changing plans.");
  const userCapacity = ref<number | null>(6);
  const userLoad = ref<number | null>(4);
  const userSleepQuality = ref<number | null>(6);
  const userCognitiveNoise = ref<number | null>(3);
  const userSocialLoad = ref<number | null>(4);
  const userEmotionalTone = ref("Steady, focused, lightly distracted.");

  // Readings
  const log = ref<Reading[]>([]);
  const activeReading = ref<Reading | null>(null);

  // Interpretation stub state (replaces AI)
  const interpretationPlaceholder = ref<string | null>(null);
  const interpretationLoading = ref(false);
  /** Signature of BaZi state when we last generated interpretation. */
  const interpretationBaZiSignature = ref<string | null>(null);

  // Computed: selected date
  const selectedDate = computed(() => {
    return new Date(`${dateISO.value}T${timeHHMM.value}:00`);
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

  // Computed: temporal hex (present moment)
  const temporalHex = computed(() => getTemporalXkdg(selectedDate.value));

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
    return getTemporalXkdg(birthInputToDate(b.input));
  });

  // Computed: qimen charts
  const qimenChartHour = computed(() => buildQimenChart(selectedDate.value, "hour"));
  const qimenChartDay = computed(() => buildQimenChart(selectedDate.value, "day"));

  // Computed: advanced astro firehose (moment - for present-moment context)
  const advancedAstroMoment = computed(() => {
    try {
      const date = selectedDate.value;
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

  // Computed: present organ
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
      })
    );
  }

  function syncLocalTimeNow(force = false) {
    if (!force && !presentAuto.value) return;
    const now = new Date();
    dateISO.value = toDateISO(now);
    timeHHMM.value = toHHMM(now);
  }

  async function hydrateFromGeolocation() {
    if (!("geolocation" in navigator)) return;
    return new Promise<void>((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
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
            // ignore
          }
          resolve();
        },
        async () => {
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
              }
            }
          } catch {
            // ignore
          }
          resolve();
        },
        { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 }
      );
    });
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
      const msg = err instanceof Error ? err.message : "Failed to get interpretation.";
      interpretationPlaceholder.value = msg;
      console.error("[requestInterpretation]", err);
    } finally {
      interpretationLoading.value = false;
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
    timezoneLabel,
    presentAuto,
    birthDatetimeLocal,
    birthSect,
    intentDomain,
    intentGoalConstraint,
    userCapacity,
    userLoad,
    userSleepQuality,
    userCognitiveNoise,
    userSocialLoad,
    userEmotionalTone,
    log,
    activeReading,
    interpretationPlaceholder,
    interpretationLoading,
    // Computed
    selectedDate,
    birthProfile,
    temporalHex,
    birthTemporalHex,
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
    syncLocalTimeNow,
    shiftPresentHours,
    hydrateFromGeolocation,
    fetchWeatherSnapshot,
    togglePresentAuto,
    generate,
    clearLog,
    setActiveReading,
    requestInterpretation,
    serializeForApi,
  };
});
