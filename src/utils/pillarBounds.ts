/**
 * Task 12.4 — Pillar Bounds (Start/End times for BaZi pillars)
 *
 * Computes the exact bounds for Year, Month, Day, and Hour pillars.
 * Uses lunar-typescript for solar terms (Li Chun, Jie Qi).
 */

import { Lunar, Solar } from "lunar-typescript";
import { getShichenDetail } from "@/core/shichenDetail";
import { ORGAN_CLOCK } from "@/data/organClock";
import { formatDate, type DateFormatType } from "./formatters";
import { getEquationOfTime } from "./solarTime";

export type PillarType = "year" | "month" | "day" | "hour";

export type PillarBoundsResult = {
  start: string;
  end: string;
  label?: string;
};

const BRANCH_TO_ORGAN: Record<string, string> = {
  子: "Zi",
  丑: "Chou",
  寅: "Yin",
  卯: "Mao",
  辰: "Chen",
  巳: "Si",
  午: "Wu",
  未: "Wei",
  申: "Shen",
  酉: "You",
  戌: "Xu",
  亥: "Hai",
};

function formatTime12h(hour: number, minute: number): string {
  const period = hour >= 12 ? "PM" : "AM";
  const h = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
  const m = String(minute).padStart(2, "0");
  return `${h}:${m} ${period}`;
}

function solarToDate(solar: Solar): Date {
  return new Date(
    solar.getYear(),
    solar.getMonth() - 1,
    solar.getDay(),
    solar.getHour(),
    solar.getMinute(),
    solar.getSecond()
  );
}

function getLiChunForYear(year: number): Solar | null {
  const solar = Solar.fromYmd(year, 2, 15);
  const lunar = Lunar.fromSolar(solar);
  const table = lunar.getJieQiTable?.() as Record<string, Solar> | undefined;
  if (!table) return null;
  return table["立春"] ?? table["LiChun"] ?? null;
}

/**
 * Returns the BaZi year (calendar year) for a given date.
 * Year starts at Li Chun; before Li Chun we're in the previous calendar year's pillar.
 */
export function getBaZiYear(date: Date): number {
  const calYear = date.getFullYear();
  const thisLiChun = getLiChunForYear(calYear);
  if (!thisLiChun) return calYear;
  const liChunDate = solarToDate(thisLiChun);
  return date.getTime() >= liChunDate.getTime() ? calYear : calYear - 1;
}

/**
 * Returns the bounds for the Hour pillar.
 * When useTrueSolarTime is true, applies EoT offset to the displayed bounds.
 */
export function getHourPillarBounds(
  branchChar: string,
  referenceDate: Date,
  useTrueSolarTime: boolean
): PillarBoundsResult {
  const branchKey = BRANCH_TO_ORGAN[branchChar] ?? branchChar;
  const entry = ORGAN_CLOCK.find((e) => e.branchCn === branchChar || e.branch === branchKey);
  if (!entry) return { start: "—", end: "—" };

  let startH = entry.startHour;
  let startM = 0;
  let endH = entry.endHour;
  let endM = 0;

  if (useTrueSolarTime) {
    const eot = Math.round(getEquationOfTime(referenceDate));
    startM = (startM + eot + 60) % 60;
    if (startM >= 60) {
      startM -= 60;
      startH = (startH + 1) % 24;
    }
    endM = (endM + eot + 60) % 60;
    if (endM >= 60) {
      endM -= 60;
      endH = (endH + 1) % 24;
    }
  }

  const endHourNorm = endH === 0 ? 24 : endH;
  return {
    start: formatTime12h(startH, startM),
    end: formatTime12h(endHourNorm === 24 ? 0 : endHourNorm, endM),
  };
}

/** Shift wall clock by EoT minutes for True Solar display. */
function applyTrueSolarOffsetToHm(
  hour: number,
  minute: number,
  referenceDate: Date,
  useTrueSolarTime: boolean
): { hour: number; minute: number } {
  if (!useTrueSolarTime) return { hour, minute };
  const eot = Math.round(getEquationOfTime(referenceDate));
  let total = hour * 60 + minute + eot;
  total = ((total % (24 * 60)) + 24 * 60) % (24 * 60);
  return { hour: Math.floor(total / 60) % 24, minute: total % 60 };
}

/**
 * Current Ke (刻) window — 15 minutes within the shichen.
 * When useTrueSolarTime is true, applies equation-of-time offset to displayed bounds.
 */
export function getKeBounds(referenceDate: Date, useTrueSolarTime: boolean): PillarBoundsResult {
  const detail = getShichenDetail(referenceDate);
  const s = detail.keStartDate;
  const e = detail.keEndDate;
  const sh = applyTrueSolarOffsetToHm(s.getHours(), s.getMinutes(), referenceDate, useTrueSolarTime);
  const eh = applyTrueSolarOffsetToHm(e.getHours(), e.getMinutes(), referenceDate, useTrueSolarTime);
  return {
    start: formatTime12h(sh.hour, sh.minute),
    end: formatTime12h(eh.hour, eh.minute),
    label: "Ke (15 min)",
  };
}

/**
 * Returns the bounds for the Year pillar (Li Chun start to next Li Chun).
 */
export function getYearPillarBounds(year: number, dateFormat: DateFormatType = "US"): PillarBoundsResult | null {
  const thisLiChun = getLiChunForYear(year);
  const nextLiChun = getLiChunForYear(year + 1);
  if (!thisLiChun || !nextLiChun) return null;

  const startDate = solarToDate(thisLiChun);
  const endDate = solarToDate(nextLiChun);

  return {
    start: formatDate(startDate, dateFormat),
    end: formatDate(endDate, dateFormat),
    label: "Li Chun",
  };
}

/**
 * Returns the bounds for the Month pillar (current Jie Qi start to next Jie Qi start).
 */
export function getMonthPillarBounds(date: Date, dateFormat: DateFormatType = "US"): PillarBoundsResult | null {
  const solar = Solar.fromDate(date);
  const lunar = Lunar.fromSolar(solar);
  const prevJieQi = (lunar as { getPrevJieQi?: () => { getSolar: () => Solar } }).getPrevJieQi?.();
  const nextJieQi = (lunar as { getNextJieQi?: () => { getSolar: () => Solar } }).getNextJieQi?.();
  if (!prevJieQi || !nextJieQi) return null;

  const startDate = solarToDate(prevJieQi.getSolar());
  const endDate = solarToDate(nextJieQi.getSolar());

  return {
    start: formatDate(startDate, dateFormat),
    end: formatDate(endDate, dateFormat),
  };
}

/**
 * Returns the bounds for the Day pillar (midnight to midnight).
 */
export function getDayPillarBounds(date: Date, dateFormat: DateFormatType = "US"): PillarBoundsResult {
  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0);
  const end = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59);
  return {
    start: formatDate(start, dateFormat),
    end: formatDate(end, dateFormat),
  };
}
