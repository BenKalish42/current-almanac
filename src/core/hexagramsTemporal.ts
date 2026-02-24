import { Lunar } from "lunar-javascript";

// 10 Heavenly Stems, 12 Earthly Branches (standard sexagenary cycle)
const STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
const BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

// Build the 60 GanZhi strings in order: 甲子 ... 癸亥
const GANZHI_60: string[] = (() => {
    const out: string[] = [];
    for (let i = 0; i < 60; i++) out.push(STEMS[i % 10]! + BRANCHES[i % 12]!);
    return out;
})();

// Benebell Wen-style: remove 4 anchor hexagrams (29, 30, 51, 58) to map 60-cycle → 60 hexagrams.  [oai_citation:4‡benebell wen](https://benebellwen.com/2024/01/05/i-ching-and-the-60-year-lunar-solar-calendar-cycle/)
const ANCHORS = new Set([29, 30, 51, 58]);
const HEXAGRAM_60: number[] = (() => {
    const out: number[] = [];
    for (let h = 1; h <= 64; h++) {
        if (!ANCHORS.has(h)) out.push(h);
    }
    // length must be 60
    return out;
})();

function ganzhiToIndex1(gz: string): number | null {
    const i = GANZHI_60.indexOf(gz);
    return i >= 0 ? i + 1 : null; // 1..60
}

function index1ToHexagram(idx1: number | null): number | null {
    if (!idx1) return null;
    return HEXAGRAM_60[idx1 - 1] ?? null;
}

export type TemporalHexagrams = {
    ganzhi: { year: string; month: string; day: string; hour: string | null };
    index1: { year: number | null; month: number | null; day: number | null; hour: number | null };
    hex: { year: number | null; month: number | null; day: number | null; hour: number | null };
};

export function getTemporalHexagrams(d: Date): TemporalHexagrams {
    const lunar = Lunar.fromDate(d); // API pattern shown in usage examples  [oai_citation:5‡CSDN Blog](https://blog.csdn.net/MAILLIBIN/article/details/145945183)

    const yearGZ = lunar.getYearInGanZhi();
    const monthGZ = lunar.getMonthInGanZhi();
    const dayGZ = lunar.getDayInGanZhi();

    // Hour GanZhi naming differs across versions. Try likely getters safely.
    const hourGZ =
        (lunar as any).getTimeInGanZhi?.() ??
        (lunar as any).getHourInGanZhi?.() ??
        null;

    const yearIdx = ganzhiToIndex1(yearGZ);
    const monthIdx = ganzhiToIndex1(monthGZ);
    const dayIdx = ganzhiToIndex1(dayGZ);
    const hourIdx = hourGZ ? ganzhiToIndex1(hourGZ) : null;

    return {
        ganzhi: { year: yearGZ, month: monthGZ, day: dayGZ, hour: hourGZ },
        index1: { year: yearIdx, month: monthIdx, day: dayIdx, hour: hourIdx },
        hex: {
            year: index1ToHexagram(yearIdx),
            month: index1ToHexagram(monthIdx),
            day: index1ToHexagram(dayIdx),
            hour: index1ToHexagram(hourIdx),
        },
    };
}