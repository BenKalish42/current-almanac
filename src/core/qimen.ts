import { Lunar, Solar } from "lunar-typescript";

export type DunType = "Yang" | "Yin";
export type Yuan = "Upper" | "Middle" | "Lower";
export type PalaceId = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;

export type PalaceInfo = {
  id: PalaceId;
  name: string;
  direction: string;
  element: string;
};

export type QimenPalace = PalaceInfo & {
  stemEarth: string | null;
  stemHeaven: string | null;
  star: string | null;
  door: string | null;
  spirit: string | null;
};

export type QimenChart = {
  method: "ZhiRun";
  scope: "hour" | "day";
  solar: {
    ymd: string;
    timeLabel: string;
  };
  lunar: {
    dayGanZhi: string;
    hourGanZhi: string | null;
    jieQi: string;
    dun: DunType;
    yuan: Yuan;
    ju: number;
  };
  zhiRun: {
    fuTouDay: string;
    fuTouGanZhi: string;
    termStart: string;
    termStatus: "chao_shen" | "jie_qi" | "zheng_shou";
    intercalary: boolean;
  };
  palaces: Record<PalaceId, QimenPalace>;
  grid: PalaceId[][];
};


const JIEQI_ORDER = [
  "冬至",
  "小寒",
  "大寒",
  "立春",
  "雨水",
  "惊蛰",
  "春分",
  "清明",
  "谷雨",
  "立夏",
  "小满",
  "芒种",
  "夏至",
  "小暑",
  "大暑",
  "立秋",
  "处暑",
  "白露",
  "秋分",
  "寒露",
  "霜降",
  "立冬",
  "小雪",
  "大雪",
];

const SIX_YI = ["戊", "己", "庚", "辛", "壬", "癸"];
const THREE_QI_YANG = ["丁", "丙", "乙"];
const THREE_QI_YIN = ["乙", "丙", "丁"];

const STARS = ["蓬", "任", "冲", "辅", "英", "芮", "柱", "心", "禽"];
const DAY_TAIYI_STARS_BY_PALACE: Partial<Record<PalaceId, string>> = {
  6: "青龙",
  7: "咸池",
  3: "轩辕",
  2: "摄提",
  1: "太乙",
  9: "天乙",
  5: "天符",
  4: "招摇",
  8: "太阴",
};
const DOORS = ["休", "生", "伤", "杜", "景", "死", "惊", "开"];
const SPIRITS_YANG = ["值符", "螣蛇", "太阴", "六合", "勾陈", "朱雀", "九地", "九天"];
const SPIRITS_YIN = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"];

const PALACE_GRID: PalaceId[][] = [
  [4, 9, 2],
  [3, 5, 7],
  [8, 1, 6],
];

const PALACE_ORDER: PalaceId[] = [4, 9, 2, 3, 5, 7, 8, 1, 6];
const PALACE_RING: PalaceId[] = PALACE_ORDER.filter((p) => p !== 5) as PalaceId[];

const PALACE_INFO: Record<PalaceId, Omit<PalaceInfo, "id">> = {
  1: { name: "Kan", direction: "N", element: "Water" },
  2: { name: "Kun", direction: "SW", element: "Earth" },
  3: { name: "Zhen", direction: "E", element: "Wood" },
  4: { name: "Xun", direction: "SE", element: "Wood" },
  5: { name: "Center", direction: "C", element: "Earth" },
  6: { name: "Qian", direction: "NW", element: "Metal" },
  7: { name: "Dui", direction: "W", element: "Metal" },
  8: { name: "Gen", direction: "NE", element: "Earth" },
  9: { name: "Li", direction: "S", element: "Fire" },
};

const YUAN_BY_BRANCH: Record<string, Yuan> = {
  "子": "Upper",
  "午": "Upper",
  "卯": "Upper",
  "酉": "Upper",
  "申": "Middle",
  "寅": "Middle",
  "巳": "Middle",
  "亥": "Middle",
  "辰": "Lower",
  "戌": "Lower",
  "丑": "Lower",
  "未": "Lower",
};

function getJieQiSolar(lunar: Lunar, keys: string[]): Solar | null {
  const table = lunar.getJieQiTable();
  for (const key of keys) {
    const solar = table[key];
    if (solar) return solar;
  }
  return null;
}

function getDunType(lunar: Lunar, solar: Solar, jieQiName: string): DunType {
  const winter = getJieQiSolar(lunar, ["冬至", "DONG_ZHI", "DongZhi"]);
  const summer = getJieQiSolar(lunar, ["夏至", "XIA_ZHI", "XiaZhi"]);
  if (winter && summer) {
    const ymd = solar.toYmd();
    const winterYmd = winter.toYmd();
    const summerYmd = summer.toYmd();
    if (ymd >= winterYmd && ymd < summerYmd) return "Yang";
    return "Yin";
  }
  const idx = JIEQI_ORDER.indexOf(jieQiName);
  if (idx >= 0) return idx < 12 ? "Yang" : "Yin";
  return "Yang";
}

// Traditional Yang Dun "nine-ju" mnemonic table (阳遁九局起例).
const YANG_DUN_JU_TABLE: { terms: string[]; ju: Record<Yuan, number> }[] = [
  { terms: ["冬至", "惊蛰"], ju: { Upper: 1, Middle: 7, Lower: 4 } },
  { terms: ["小寒"], ju: { Upper: 2, Middle: 8, Lower: 5 } },
  { terms: ["春分", "大寒"], ju: { Upper: 3, Middle: 9, Lower: 6 } },
  { terms: ["雨水"], ju: { Upper: 9, Middle: 6, Lower: 3 } },
  { terms: ["清明", "立夏"], ju: { Upper: 4, Middle: 1, Lower: 7 } },
  { terms: ["立春"], ju: { Upper: 8, Middle: 5, Lower: 2 } },
  { terms: ["谷雨", "小满"], ju: { Upper: 5, Middle: 2, Lower: 8 } },
  { terms: ["芒种"], ju: { Upper: 6, Middle: 3, Lower: 9 } },
];

// Traditional Yin Dun "nine-ju" mnemonic table (阴遁九局起例).
const YIN_DUN_JU_TABLE: { terms: string[]; ju: Record<Yuan, number> }[] = [
  { terms: ["夏至", "白露"], ju: { Upper: 9, Middle: 3, Lower: 6 } },
  { terms: ["小暑"], ju: { Upper: 8, Middle: 2, Lower: 5 } },
  { terms: ["大暑", "秋分"], ju: { Upper: 7, Middle: 1, Lower: 4 } },
  { terms: ["立秋"], ju: { Upper: 2, Middle: 5, Lower: 8 } },
  { terms: ["处暑"], ju: { Upper: 1, Middle: 4, Lower: 7 } },
  { terms: ["寒露", "立冬"], ju: { Upper: 6, Middle: 9, Lower: 3 } },
  { terms: ["霜降", "小雪"], ju: { Upper: 5, Middle: 8, Lower: 2 } },
  { terms: ["大雪"], ju: { Upper: 4, Middle: 7, Lower: 1 } },
];

function lookupJu(table: { terms: string[]; ju: Record<Yuan, number> }[], jieQiName: string, yuan: Yuan): number | null {
  for (const group of table) {
    if (group.terms.includes(jieQiName)) return group.ju[yuan];
  }
  return null;
}

function getJuNumberZhiRun(jieQiName: string, dun: DunType, yuan: Yuan): number {
  const table = dun === "Yang" ? YANG_DUN_JU_TABLE : YIN_DUN_JU_TABLE;
  const ju = lookupJu(table, jieQiName, yuan);
  return ju ?? (dun === "Yang" ? 1 : 9);
}

function rotateAssignments<T>(
  palaces: PalaceId[],
  sequence: T[],
  startPalace: PalaceId,
  dun: DunType
): Record<PalaceId, T | null> {
  const out: Record<PalaceId, T | null> = {} as Record<PalaceId, T | null>;
  const startIdx = palaces.indexOf(startPalace);
  const len = palaces.length;
  for (let i = 0; i < palaces.length; i++) {
    const step = dun === "Yang" ? i : -i;
    const palace = palaces[(startIdx + step + len) % len]!;
    out[palace] = sequence[i] ?? null;
  }
  return out;
}

function effectiveHourStem(stem: string): string {
  return stem === "甲" ? "戊" : stem;
}

function formatLocalTimeLabel(d: Date) {
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  return `${h}:${m}`;
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

function daysBetween(a: Solar, b: Solar): number {
  const ms = solarToDate(b).getTime() - solarToDate(a).getTime();
  return Math.floor(ms / 86400000);
}

function getDayGanzhi(solar: Solar): { gan: string; zhi: string; gz: string } {
  const lunar = Lunar.fromSolar(solar);
  const eightChar = lunar.getEightChar();
  return {
    gan: eightChar.getDayGan(),
    zhi: eightChar.getDayZhi(),
    gz: eightChar.getDay(),
  };
}

function findPrevJiaJiDay(solar: Solar): Solar {
  let cursor = solar;
  for (let i = 0; i < 12; i++) {
    const { gan } = getDayGanzhi(cursor);
    if (gan === "甲" || gan === "己") return cursor;
    cursor = cursor.nextDay(-1);
  }
  return solar;
}

function findNearestJiaJiToTerm(termSolar: Solar): { solar: Solar; status: "chao_shen" | "jie_qi" | "zheng_shou"; leadDays: number } {
  let best: Solar | null = null;
  let bestDiff = Number.POSITIVE_INFINITY;
  let status: "chao_shen" | "jie_qi" | "zheng_shou" = "zheng_shou";

  for (let offset = -5; offset <= 5; offset++) {
    const candidate = termSolar.nextDay(offset);
    const { gan } = getDayGanzhi(candidate);
    if (gan !== "甲" && gan !== "己") continue;
    const diff = Math.abs(offset);
    if (diff < bestDiff) {
      best = candidate;
      bestDiff = diff;
      status = offset === 0 ? "zheng_shou" : offset < 0 ? "chao_shen" : "jie_qi";
    }
  }

  if (!best) {
    best = termSolar;
  }

  const leadDays = Math.max(0, daysBetween(best, termSolar));
  return { solar: best, status, leadDays };
}

function getCurrentJieQiSolar(date: Date): { name: string; solar: Solar } {
  const solar = Solar.fromDate(date);
  const lunar = Lunar.fromSolar(solar);
  const table = lunar.getJieQiTable();
  const entries = Object.entries(table);

  let current: { name: string; solar: Solar } | null = null;
  for (const [name, s] of entries) {
    if (!s) continue;
    if (solarToDate(s) <= date) {
      if (!current || solarToDate(s) > solarToDate(current.solar)) {
        current = { name, solar: s };
      }
    }
  }

  if (current) return current;

  const prevYearSolar = Solar.fromYmdHms(
    solar.getYear() - 1,
    solar.getMonth(),
    solar.getDay(),
    solar.getHour(),
    solar.getMinute(),
    solar.getSecond()
  );
  const prevLunar = Lunar.fromSolar(prevYearSolar);
  const prevTable = prevLunar.getJieQiTable();
  const prevEntries = Object.entries(prevTable);
  for (const [name, s] of prevEntries) {
    if (!s) continue;
    if (!current || solarToDate(s) > solarToDate(current.solar)) {
      current = { name, solar: s };
    }
  }

  return current ?? { name: "冬至", solar: solar };
}

function getYuanForDate(date: Date): { yuan: Yuan; fuTouSolar: Solar } {
  const solar = Solar.fromDate(date);
  const fuTou = findPrevJiaJiDay(solar);
  const { zhi } = getDayGanzhi(fuTou);
  const yuan = YUAN_BY_BRANCH[zhi] ?? "Upper";
  return { yuan, fuTouSolar: fuTou };
}

function findNearestJiaziToSolstice(solstice: Solar): Solar {
  let best: Solar | null = null;
  let bestDiff = Number.POSITIVE_INFINITY;
  for (let offset = -30; offset <= 30; offset++) {
    const candidate = solstice.nextDay(offset);
    const { gz } = getDayGanzhi(candidate);
    if (gz !== "甲子") continue;
    const diff = Math.abs(offset);
    if (diff < bestDiff || (diff === bestDiff && offset < 0)) {
      best = candidate;
      bestDiff = diff;
    }
  }
  return best ?? solstice;
}

function getDaySchoolYuanAndJu(date: Date, dun: DunType): { yuan: Yuan; ju: number } {
  const solar = Solar.fromDate(date);
  const lunar = Lunar.fromSolar(solar);
  const table = lunar.getJieQiTable();
  const winter = table["冬至"] ?? table["DONG_ZHI"];
  const summer = table["夏至"] ?? table["XIA_ZHI"];
  const anchor = dun === "Yang" ? findNearestJiaziToSolstice(winter ?? solar) : findNearestJiaziToSolstice(summer ?? solar);
  let days = daysBetween(anchor, solar);
  while (days < 0) days += 15;
  const block = Math.floor((days % 15) / 5);
  const yuan: Yuan = block === 0 ? "Upper" : block === 1 ? "Middle" : "Lower";
  const seq = dun === "Yang" ? [1, 7, 4] : [9, 3, 6];
  return { yuan, ju: seq[block] ?? seq[0]! };
}

function buildChartBase(date: Date, scope: "hour" | "day"): {
  solar: Solar;
  dayGanZhi: string;
  hourGanZhi: string | null;
  hourStem: string;
  jieQiName: string;
  dun: DunType;
  yuan: Yuan;
  ju: number;
  zhiRun: QimenChart["zhiRun"];
} {
  const solar = Solar.fromDate(date);
  const lunar = Lunar.fromSolar(solar);
  const eightChar = lunar.getEightChar();
  const dayGanZhi = eightChar.getDay();
  const hourGanZhi = eightChar.getTime();
  const hourStem = scope === "day" ? eightChar.getDayGan() : eightChar.getTimeGan();
  const currentTerm = getCurrentJieQiSolar(date);
  const termStart = currentTerm.solar;
  const termName = currentTerm.name;
  const { solar: fuTouForTerm, status, leadDays } = findNearestJiaJiToTerm(termStart);
  const zhiRunIntercalary = (termName === "芒种" || termName === "大雪") && status === "chao_shen" && leadDays >= 9;

  let effectiveTermName = termName;
  if (status === "jie_qi" && date < solarToDate(fuTouForTerm)) {
    const prevTerm = getCurrentJieQiSolar(new Date(solarToDate(termStart).getTime() - 60000));
    effectiveTermName = prevTerm.name;
  }

  const { yuan, fuTouSolar } = getYuanForDate(date);
  const dun = getDunType(lunar, solar, termName);
  const ju = getJuNumberZhiRun(effectiveTermName, dun, yuan);

  return {
    solar,
    dayGanZhi,
    hourGanZhi: scope === "day" ? null : hourGanZhi,
    hourStem,
    jieQiName: effectiveTermName,
    dun,
    yuan,
    ju,
    zhiRun: {
      fuTouDay: fuTouSolar.toYmd(),
      fuTouGanZhi: getDayGanzhi(fuTouSolar).gz,
      termStart: termStart.toYmdHms(),
      termStatus: status,
      intercalary: zhiRunIntercalary,
    },
  };
}

export function buildQimenChart(date: Date, scope: "hour" | "day" = "hour"): QimenChart {
  const { solar, dayGanZhi, hourGanZhi, hourStem, jieQiName, dun, yuan, ju, zhiRun } = buildChartBase(
    date,
    scope
  );

  const daySchool = scope === "day";
  const daySchoolValues = daySchool ? getDaySchoolYuanAndJu(date, dun) : null;
  const effectiveYuan = daySchoolValues?.yuan ?? yuan;
  const effectiveJu = daySchoolValues?.ju ?? ju;

  const earthSequence =
    dun === "Yang"
      ? [...SIX_YI, ...THREE_QI_YANG]
      : [...SIX_YI].reverse().concat(THREE_QI_YIN);
  const earthStems = rotateAssignments(PALACE_ORDER, earthSequence, effectiveJu as PalaceId, "Yang");
  const hourStemEffective = effectiveHourStem(hourStem);
  const hourStemPalace =
    (PALACE_ORDER.find((id) => earthStems[id] === hourStemEffective) ?? (effectiveJu as PalaceId));
  const heavenStems = rotateAssignments(PALACE_ORDER, earthSequence, hourStemPalace, "Yang");

  let stars: Record<PalaceId, string | null>;
  if (daySchool) {
    stars = {} as Record<PalaceId, string | null>;
    (PALACE_ORDER as PalaceId[]).forEach((id) => {
      stars[id] = DAY_TAIYI_STARS_BY_PALACE[id] ?? null;
    });
  } else {
    const starHomes: Record<string, PalaceId> = {
      "蓬": 1,
      "任": 8,
      "冲": 3,
      "辅": 4,
      "英": 9,
      "芮": 2,
      "柱": 7,
      "心": 6,
      "禽": dun === "Yang" ? 2 : 8,
    };
    const dayStemPalace =
      (PALACE_ORDER.find((id) => earthStems[id] === dayGanZhi[0]) ?? (effectiveJu as PalaceId));
    const zhiFuStar = Object.entries(starHomes).find(([, palace]) => palace === dayStemPalace)?.[0] ?? "蓬";
    const starSequenceStart = STARS.indexOf(zhiFuStar);
    const starsSeq = starSequenceStart >= 0 ? [...STARS.slice(starSequenceStart), ...STARS.slice(0, starSequenceStart)] : STARS;
    stars = rotateAssignments(PALACE_ORDER, starsSeq, hourStemPalace, dun);
  }

  const doors = rotateAssignments(PALACE_RING, DOORS, effectiveJu as PalaceId, dun);
  const spirits = rotateAssignments(PALACE_RING, dun === "Yang" ? SPIRITS_YANG : SPIRITS_YIN, effectiveJu as PalaceId, dun);

  const palaces: Record<PalaceId, QimenPalace> = {} as Record<PalaceId, QimenPalace>;
  (PALACE_ORDER as PalaceId[]).forEach((id) => {
    palaces[id] = {
      id,
      ...PALACE_INFO[id],
      stemEarth: earthStems[id] ?? null,
      stemHeaven: heavenStems[id] ?? null,
      star: stars[id] ?? null,
      door: doors[id] ?? null,
      spirit: spirits[id] ?? null,
    };
  });

  return {
    method: "ZhiRun",
    scope,
    solar: { ymd: solar.toYmd(), timeLabel: formatLocalTimeLabel(date) },
    lunar: {
      dayGanZhi,
      hourGanZhi,
      jieQi: jieQiName,
      dun,
      yuan: effectiveYuan,
      ju: effectiveJu,
    },
    zhiRun,
    palaces,
    grid: PALACE_GRID,
  };
}
