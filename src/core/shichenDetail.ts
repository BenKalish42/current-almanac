/**
 * Chu (初) / Zheng (正) halves and Ke (刻) — 15-minute subdivisions within a shichen.
 * Pure clock arithmetic on top of the 12 two-hour organ-clock blocks.
 */

import { getCurrentOrganHour, getMinutesIntoShichen, type OrganHourEntry } from "@/data/organClock";

export type ChuZheng = "chu" | "zheng";

const CHU_ZHENG_CN: Record<ChuZheng, string> = {
  chu: "初",
  zheng: "正",
};

/** Ke index within half-shichen (1–4) as Chinese numerals */
const KE_HALF_CN = ["", "一", "二", "三", "四"];

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

function formatHm24(hour: number, minute: number): string {
  return `${pad2(hour)}:${pad2(minute)}`;
}

/**
 * Start instant of the current shichen in local time (calendar date of `date`).
 * Zi beginning at 23:xx uses same calendar day; Zi continuation at 00:xx uses previous day 23:00.
 */
export function getShichenStartDate(date: Date, entry: OrganHourEntry, hour24: number): Date {
  const y = date.getFullYear();
  const mo = date.getMonth();
  const da = date.getDate();
  if (entry.branch === "Zi") {
    if (hour24 >= 23) {
      return new Date(y, mo, da, 23, 0, 0, 0);
    }
    return new Date(y, mo, da - 1, 23, 0, 0, 0);
  }
  return new Date(y, mo, da, entry.startHour, 0, 0, 0);
}

export type ShichenDetail = {
  branch: string;
  branchCn: string;
  branchPinyin: string;
  chuZheng: ChuZheng;
  chuZhengLabel: string;
  keInShichen: number;
  keInHalf: number;
  keStartMinuteOfHour: number;
  keEndMinuteOfHour: number;
  keBoundsDisplay: string;
  keStartDate: Date;
  keEndDate: Date;
  fullLabel: string;
  fullLabelEn: string;
  organEntry: OrganHourEntry;
};

/**
 * Compute Chu/Zheng/Ke for a given local `Date` (caller applies True Solar Time if desired).
 */
export function getShichenDetail(date: Date): ShichenDetail {
  const hour24 = date.getHours();
  const minute = date.getMinutes();
  const organEntry = getCurrentOrganHour(hour24);
  const minutesInto = getMinutesIntoShichen(hour24, minute);

  const chuZheng: ChuZheng = minutesInto < 60 ? "chu" : "zheng";
  const chuZhengLabel = CHU_ZHENG_CN[chuZheng];

  const keInShichen = Math.floor(minutesInto / 15) + 1;
  const minutesIntoHalf = minutesInto % 60;
  const keInHalf = Math.floor(minutesIntoHalf / 15) + 1;

  const keStartWithin = Math.floor(minutesInto / 15) * 15;
  const shichenStart = getShichenStartDate(date, organEntry, hour24);
  const keStartDate = new Date(shichenStart.getTime() + keStartWithin * 60 * 1000);
  const keEndDate = new Date(keStartDate.getTime() + 15 * 60 * 1000);

  const ksH = keStartDate.getHours();
  const ksM = keStartDate.getMinutes();
  const keH = keEndDate.getHours();
  const keM = keEndDate.getMinutes();

  const keBoundsDisplay = `${formatHm24(ksH, ksM)} – ${formatHm24(keH, keM)}`;

  const keHalfCn = KE_HALF_CN[keInHalf] ?? String(keInHalf);
  const fullLabel = `${organEntry.branchCn}${chuZhengLabel}${keHalfCn}刻`;
  const fullLabelEn = `${organEntry.branch} ${chuZheng === "chu" ? "Chu" : "Zheng"} Ke-${keInHalf}`;

  return {
    branch: organEntry.branch,
    branchCn: organEntry.branchCn,
    branchPinyin: organEntry.branch,
    chuZheng,
    chuZhengLabel,
    keInShichen,
    keInHalf,
    keStartMinuteOfHour: ksM,
    keEndMinuteOfHour: keM,
    keBoundsDisplay,
    keStartDate,
    keEndDate,
    fullLabel,
    fullLabelEn,
    organEntry,
  };
}
