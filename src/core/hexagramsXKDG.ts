import { Lunar, Solar } from "lunar-typescript";
import { formatBranchDisplay, formatStemDisplay, parseGanZhi } from "./ganzhi";
import { HEX_BINARY_TOP_TO_BOTTOM } from "./iching";

type TrigramToken = "天" | "地" | "水" | "火" | "风" | "雷" | "山" | "泽";

const TRIGRAM_BIN: Record<TrigramToken, string> = {
    天: "111", // 乾
    地: "000", // 坤
    水: "010", // 坎
    火: "101", // 离
    雷: "001", // 震
    风: "110", // 巽
    山: "100", // 艮
    泽: "011", // 兑
};

const BINARY_TO_HEX_NUM: Record<string, number> = (() => {
    const out: Record<string, number> = {};
    for (const [numStr, bin] of Object.entries(HEX_BINARY_TOP_TO_BOTTOM)) {
        out[bin] = Number(numStr);
    }
    return out;
})();

/**
 * XKDG table: GanZhi -> hexagram full trigram-name (upper+lower+name)
 * Source structure matches common XKDG “60 JiaZi ↔ 64 Gua” tables.
 * Data below transcribed from the table you referenced.  [oai_citation:3‡yixiansheng.com](https://www.yixiansheng.com/article/4520.html)
 */
const XKDG_TABLE_TEXT = `
甲子 地雷复
乙丑 火雷噬嗑
丙寅 风火家人
丁卯 山泽损
戊辰 天泽履
己巳 雷天大壮
庚午 雷风恒
辛未 天水讼
壬申 地水师
癸酉 风山渐
甲戌 水山蹇
乙亥 火地晋
丙子 山雷颐
丁丑 泽雷随
戊寅 雷火丰
己卯 水泽节
庚辰 地天泰
辛巳 火天大有
壬午 巽为风
癸未 泽水困
甲申 水火既济
乙酉 天山遁
丙戌 艮为山
丁亥 雷地豫
戊子 水雷屯
己丑 天雷无妄
庚寅 泽火革
辛卯 风泽中孚
壬辰 山天大畜
癸巳 泽天夬
甲午 天风姤
乙未 水风井
丙申 雷水解
丁酉 泽山咸
戊戌 地山谦
己亥 风地观
庚子 风雷益
辛丑 地火明夷
壬寅 天火同人
癸卯 雷泽归妹
甲辰 火泽睽
乙巳 水天需
丙午 泽风大过
丁未 山风蛊
戊申 风水涣
己酉 火山旅
庚戌 天地否
辛亥 水地比
壬子 震为雷
癸丑 山火贲
甲寅 水火既济
乙卯 地泽临
丙辰 兑为泽
丁巳 风天小畜
戊午 火风鼎
己未 地风升
庚申 山水蒙
辛酉 雷山小过
壬戌 泽地萃
癸亥 山地剥
`.trim();

const XKDG_GZ_TO_HEXNAME: Record<string, string> = (() => {
    const out: Record<string, string> = {};
    for (const line of XKDG_TABLE_TEXT.split("\n")) {
        const [gz, name] = line.trim().split(/\s+/);
        if (gz && name) out[gz] = name;
    }
    return out;
})();

function parseHexNameToBinary(name: string): string | null {
    // Pure trigram forms like "巽为风"
    if (name.includes("为")) {
        const tok = name.slice(-1) as TrigramToken;
        const tri = TRIGRAM_BIN[tok];
        return tri ? tri + tri : null;
    }

    const upper = name[0] as TrigramToken;
    const lower = name[1] as TrigramToken;
    const upBin = TRIGRAM_BIN[upper];
    const loBin = TRIGRAM_BIN[lower];
    return upBin && loBin ? upBin + loBin : null;
}

// English hexagram names (simple, almanac-friendly set).
// Base list from “I Ching Online” (names in King Wen order).  [oai_citation:4‡iching-online.com](https://www.iching-online.com/hexagrams/)
// We override #28 to “Great Exceeding” to match common almanac phrasing. 
const HEX_NAME_EN: string[] = [
    "", // 0 unused
    "Creative", "Receptive", "Difficulty", "Folly",
    "Waiting", "Conflict", "Army", "Union",
    "Taming", "Treading", "Peace", "Standstill",
    "Fellowship", "Possession", "Modesty", "Enthusiasm",
    "Following", "Decay", "Approach", "View",
    "Biting", "Grace", "Splitting", "Return",
    "Innocence", "Taming", "Mouth", "Great Exceeding", // 28 override
    "Abysmal", "Clinging", "Influence", "Duration",
    "Retreat", "Power", "Progress", "Darkening",
    "Family", "Opposition", "Obstruction", "Deliverance",
    "Decrease", "Increase", "Resoluteness", "Coming",
    "Gathering", "Pushing", "Oppression", "Well",
    "Revolution", "Caldron", "Arousing", "Still",
    "Development", "Marrying", "Abundance", "Wanderer",
    "Gentle", "Joyous", "Dispersion", "Limitation",
    "Truth", "Small", "After", "Before",
];

export type TemporalXkdgPillar = {
    ganzhi: string | null;
    stemLine: string | null;   // e.g., "Stem: Wood Yin (乙)"
    branchLine: string | null; // e.g., "Branch: Fire Yin Snake (巳)"
    hex: {
        nameCn: string | null;   // e.g., 水天需
        num: number | null;      // e.g., 5
        nameEn: string | null;   // e.g., Waiting
        binary: string | null;   // e.g., 010111
    };
};

export type TemporalXkdg = {
    year: TemporalXkdgPillar;
    month: TemporalXkdgPillar;
    day: TemporalXkdgPillar;
    hour: TemporalXkdgPillar;
};

function toSolarFromLocalDate(d: Date) {
    // Use local clock fields (matches your UI expectation).
    return Solar.fromYmdHms(
        d.getFullYear(),
        d.getMonth() + 1,
        d.getDate(),
        d.getHours(),
        d.getMinutes(),
        d.getSeconds()
    );
}

function getGanZhiExact(lunar: any) {
    // Year: Li Chun exact moment preferred (per your choice)
    const year =
        lunar.getYearInGanZhiExact?.() ??
        lunar.getYearInGanZhiExactByLiChun?.() ??
        lunar.getYearInGanZhiByLiChun?.() ??
        lunar.getYearInGanZhi?.() ??
        null;

    const month =
        lunar.getMonthInGanZhiExact?.() ??
        lunar.getMonthInGanZhi?.() ??
        null;

    const day =
        lunar.getDayInGanZhiExact?.() ??
        lunar.getDayInGanZhi?.() ??
        null;

    const hour =
        lunar.getTimeInGanZhi?.() ??
        lunar.getTimeInGanZhiExact?.() ??
        null;

    return { year, month, day, hour };
}

function buildPillar(gz: string | null): TemporalXkdgPillar {
    const parsed = parseGanZhi(gz);
    const nameCn = gz ? (XKDG_GZ_TO_HEXNAME[gz] ?? null) : null;
    const binary = nameCn ? parseHexNameToBinary(nameCn) : null;
    const num = binary ? (BINARY_TO_HEX_NUM[binary] ?? null) : null;

    return {
        ganzhi: gz,
        stemLine: parsed.stem ? `Stem: ${formatStemDisplay(parsed.stem.char)}` : null,
        branchLine: parsed.branch ? `Branch: ${formatBranchDisplay(parsed.branch.char)}` : null,
        hex: {
            nameCn,
            num,
            nameEn: num ? (HEX_NAME_EN[num] ?? null) : null,
            binary,
        },
    };
}

export function getTemporalXkdg(d: Date): TemporalXkdg {
    const solar = toSolarFromLocalDate(d);
    const lunar = Lunar.fromSolar(solar) as any;

    const gz = getGanZhiExact(lunar);

    return {
        year: buildPillar(gz.year),
        month: buildPillar(gz.month),
        day: buildPillar(gz.day),
        hour: buildPillar(gz.hour),
    };
}