/**
 * Da Liu Ren (大六壬) engine.
 * Ji Gong map, Heaven Pan (Yue Jiang rotation), Si Ke (Four Classes), San Chuan with Zei Ke priority.
 * For hidden AI context only — not rendered in UI.
 */
import { Lunar, Solar } from "lunar-typescript";

/** Branch names in order (Zi=1 .. Hai=12). */
const BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"] as const;
/** Ji Gong (遁干): Stem → Earthly Branch index (1-based). Exact mapping from spec. */
const JI_GONG: Record<string, number> = {
  甲: 3,
  乙: 5,
  丙: 6,
  丁: 8,
  戊: 6,
  己: 8,
  庚: 9,
  辛: 11,
  壬: 12,
  癸: 2,
};

/** Jie (节) terms that determine Yue Jiang; each maps to a branch index (1-based). */
const JIE_TO_YUE_JIANG: Record<string, number> = {
  立春: 12,   // 亥
  惊蛰: 11,   // 戌
  清明: 10,   // 酉
  立夏: 9,    // 申
  芒种: 8,    // 未
  小暑: 7,    // 午
  立秋: 6,    // 巳
  白露: 5,    // 辰
  寒露: 4,    // 卯
  立冬: 3,    // 寅
  大雪: 2,    // 丑
  小寒: 1,    // 子
};

/** Five Elements for stems and branches (for Ke/克). */
const STEM_ELEMENT: Record<string, string> = {
  甲: "木", 乙: "木", 丙: "火", 丁: "火", 戊: "土", 己: "土",
  庚: "金", 辛: "金", 壬: "水", 癸: "水",
};
const BRANCH_ELEMENT: Record<string, string> = {
  子: "水", 丑: "土", 寅: "木", 卯: "木", 辰: "土", 巳: "火",
  午: "火", 未: "土", 申: "金", 酉: "金", 戌: "土", 亥: "水",
};

/** Element overcoming: 克 (ke). */
const KE: Record<string, string> = {
  木: "土", 火: "金", 土: "水", 金: "木", 水: "火",
};

function branchIndex(zhi: string): number {
  const i = BRANCHES.indexOf(zhi as (typeof BRANCHES)[number]);
  return i >= 0 ? i + 1 : 0;
}

function branchByIndex(idx: number): string {
  const i = ((idx - 1) % 12 + 12) % 12;
  return BRANCHES[i] ?? "子";
}

function doesOvercome(lower: string, upper: string): boolean {
  const lowerEl = STEM_ELEMENT[lower] ?? BRANCH_ELEMENT[lower];
  const upperEl = STEM_ELEMENT[upper] ?? BRANCH_ELEMENT[upper];
  if (!lowerEl || !upperEl) return false;
  return (KE[lowerEl] ?? "") === upperEl; // lower 克 upper
}

export type DaLiuRenResult = {
  dayGan: string;
  dayZhi: string;
  hourGan: string;
  hourZhi: string;
  yueJiang: string;
  yueJiangJie: string;
  heavenPan: Record<string, string>; // Earth branch position -> Heaven god (branch)
  siKe: Array<{ upper: string; lower: string }>;
  sanChuan: { chu: string; zhong: string; mo: string };
  zeiKeMethod: boolean;
};

function solarToDate(s: Solar): Date {
  return new Date(s.getYear(), s.getMonth() - 1, s.getDay(), s.getHour(), s.getMinute(), s.getSecond());
}

function getCurrentJieName(date: Date): string {
  const solar = Solar.fromDate(date);
  const lunar = Lunar.fromSolar(solar);
  const table = lunar.getJieQiTable() as Record<string, Solar | undefined>;
  const jieNames = Object.keys(JIE_TO_YUE_JIANG);
  let current = "";
  let latestTime = 0;
  for (const name of jieNames) {
    const term = table[name];
    if (!term) continue;
    const t = solarToDate(term).getTime();
    if (t <= date.getTime() && t > latestTime) {
      latestTime = t;
      current = name;
    }
  }
  if (current) return current;
  const prevYearSolar = Solar.fromYmdHms(date.getFullYear() - 1, 12, 22, 0, 0, 0);
  const prevLunar = Lunar.fromSolar(prevYearSolar);
  const prevTable = prevLunar.getJieQiTable() as Record<string, Solar | undefined>;
  for (const name of jieNames) {
    const term = prevTable[name];
    if (!term) continue;
    const t = solarToDate(term).getTime();
    if (t > latestTime) {
      latestTime = t;
      current = name;
    }
  }
  return current || "小寒";
}

/**
 * Compute Da Liu Ren chart for a given date.
 * Uses Ji Gong map, Yue Jiang from Jie Qi, Heaven Pan rotation, Si Ke, and San Chuan with Zei Ke priority.
 */
export function computeDaLiuRen(date: Date): DaLiuRenResult {
  const solar = Solar.fromDate(date);
  const lunar = Lunar.fromSolar(solar);
  const dayGZ = (lunar.getDayInGanZhi?.() ?? lunar.getDayInGanZhiExact?.() ?? "") as string;
  const hourGZ = lunar.getTimeInGanZhi?.() ?? "";

  const dayGan = dayGZ.charAt(0) || "";
  const dayZhi = dayGZ.charAt(1) || "";
  const hourGan = hourGZ.charAt(0) || "";
  const hourZhi = hourGZ.charAt(1) || "";

  const jieName = getCurrentJieName(date);
  const yueJiangIdx = JIE_TO_YUE_JIANG[jieName] ?? 1;
  const yueJiang = branchByIndex(yueJiangIdx);

  const hourPos = branchIndex(hourZhi) || 1;
  const heavenPan: Record<string, string> = {};
  for (let i = 1; i <= 12; i++) {
    const earthBranch = branchByIndex(i);
    const offset = ((i - hourPos) % 12 + 12) % 12;
    const heavenIdx = ((yueJiangIdx - 1 + offset) % 12) + 1;
    heavenPan[earthBranch] = branchByIndex(heavenIdx);
  }

  const dayStemBranchIdx = JI_GONG[dayGan] ?? 3;
  const dayStemEarthPos = branchByIndex(dayStemBranchIdx);
  const hourStemBranchIdx = JI_GONG[hourGan] ?? 3;
  const hourStemEarthPos = branchByIndex(hourStemBranchIdx);

  const siKe: Array<{ upper: string; lower: string }> = [
    { upper: heavenPan[dayStemEarthPos] ?? "", lower: dayStemEarthPos },
    { upper: heavenPan[dayZhi] ?? "", lower: dayZhi },
    { upper: heavenPan[hourStemEarthPos] ?? "", lower: hourStemEarthPos },
    { upper: heavenPan[hourZhi] ?? "", lower: hourZhi },
  ];

  let chu = "";
  let zhong = "";
  let mo = "";
  let zeiKeMethod = false;

  for (let k = 0; k < 4; k++) {
    const entry = siKe[k];
    if (!entry) continue;
    const { upper, lower } = entry;
    if (upper && lower && doesOvercome(lower, upper)) {
      chu = lower;
      zeiKeMethod = true;
      break;
    }
  }
  if (!zeiKeMethod) {
    for (let k = 0; k < 4; k++) {
      const entry = siKe[k];
      if (!entry) continue;
      const { upper, lower } = entry;
      if (upper && lower && doesOvercome(upper, lower)) {
        chu = upper;
        break;
      }
    }
  }

  if (chu) {
    const chuIdx = branchIndex(chu);
    zhong = branchByIndex(chuIdx + 6);
    mo = branchByIndex(chuIdx + 6 + 6);
  }

  return {
    dayGan,
    dayZhi,
    hourGan,
    hourZhi,
    yueJiang,
    yueJiangJie: jieName,
    heavenPan,
    siKe,
    sanChuan: { chu, zhong, mo },
    zeiKeMethod,
  };
}
