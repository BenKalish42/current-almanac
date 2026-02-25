/**
 * Zi Wei Dou Shu (ZWDS) wrapper for hidden AI context.
 * Uses iztro to generate the 12-Palace chart and star placements.
 * Not rendered in UI — for Zhuang's hyper-dimensional understanding only.
 */
import { astro } from "iztro";

/** Gender for ZWDS: male or female. */
export type ZWDSGender = "male" | "female";

/** Map our gender string to iztro format. */
const GENDER_MAP: Record<ZWDSGender, "男" | "女"> = {
  male: "男",
  female: "女",
};

/** Convert hour (0-23) to Zi Wei double-hour index (0-11). */
function hourToTimeIndex(hour: number): number {
  if (hour < 0 || hour > 23) return 0;
  // 子时 23-1, 丑时 1-3, 寅时 3-5, ..., 亥时 21-23
  const idx = Math.floor(((hour + 1) % 24) / 2);
  return idx % 12;
}

type PalaceLike = Record<string, unknown>;
type StarLike = Record<string, unknown>;

/** Serialize a star for JSON output. */
function serializeStar(star: StarLike): Record<string, unknown> {
  return {
    name: (star?.name as string) ?? null,
    type: (star?.type as string) ?? null,
    brightness: (star?.brightness as string) ?? null,
    mutagen: (star?.mutagen as string) ?? null,
  };
}

/** Serialize a palace for JSON output. */
function serializePalace(palace: PalaceLike): Record<string, unknown> {
  const decadal = palace?.decadal as Record<string, unknown> | undefined;
  return {
    name: (palace?.name as string) ?? null,
    heavenly_stem: (palace?.heavenlyStem as string) ?? null,
    earthly_branch: (palace?.earthlyBranch as string) ?? null,
    major_stars: ((palace?.majorStars as StarLike[]) ?? []).map(serializeStar),
    minor_stars: ((palace?.minorStars as StarLike[]) ?? []).map(serializeStar),
    adjective_stars: ((palace?.adjectiveStars as StarLike[]) ?? []).map(serializeStar),
    decadal: decadal
      ? {
          range: (decadal?.range as string) ?? null,
          heavenly_stem: (decadal?.heavenlyStem as string) ?? null,
          earthly_branch: (decadal?.earthlyBranch as string) ?? null,
        }
      : null,
    ages: (palace?.ages as number[]) ?? [],
  };
}

/** ZWDS matrix result for AI payload. */
export interface ZWDSMatrix {
  solar_date: string;
  lunar_date: string;
  chinese_date: string;
  time: string;
  time_range: string;
  sign: string;
  zodiac: string;
  soul_palace_branch: string;
  body_palace_branch: string;
  soul: string;
  body: string;
  five_elements_class: string;
  palaces: Record<string, unknown>[];
}

/**
 * Generate the Zi Wei Dou Shu 12-Palace matrix from birth data.
 * @param year - Birth year
 * @param month - Birth month (1-12)
 * @param day - Birth day
 * @param hour - Birth hour (0-23)
 * @param gender - "male" or "female"
 * @returns Serialized ZWDS matrix or null on error
 */
export function generateZWDSMatrix(
  year: number,
  month: number,
  day: number,
  hour: number,
  gender: ZWDSGender
): ZWDSMatrix | null {
  try {
    const solarStr = `${year}-${month}-${day}`;
    const timeIndex = hourToTimeIndex(hour);
    const genderParam = GENDER_MAP[gender];

    const astrolabe = astro.bySolar(solarStr, timeIndex, genderParam, true, "en");

    const palaces = (astrolabe.palaces ?? []).map((p: unknown) =>
      serializePalace(p as PalaceLike)
    );

    return {
      solar_date: (astrolabe as { solarDate?: string }).solarDate ?? solarStr,
      lunar_date: (astrolabe as { lunarDate?: string }).lunarDate ?? "",
      chinese_date: (astrolabe as { chineseDate?: string }).chineseDate ?? "",
      time: (astrolabe as { time?: string }).time ?? "",
      time_range: (astrolabe as { timeRange?: string }).timeRange ?? "",
      sign: (astrolabe as { sign?: string }).sign ?? "",
      zodiac: (astrolabe as { zodiac?: string }).zodiac ?? "",
      soul_palace_branch:
        (astrolabe as { earthlyBranchOfSoulPalace?: string }).earthlyBranchOfSoulPalace ?? "",
      body_palace_branch:
        (astrolabe as { earthlyBranchOfBodyPalace?: string }).earthlyBranchOfBodyPalace ?? "",
      soul: (astrolabe as { soul?: string }).soul ?? "",
      body: (astrolabe as { body?: string }).body ?? "",
      five_elements_class:
        (astrolabe as { fiveElementsClass?: string }).fiveElementsClass ?? "",
      palaces,
    };
  } catch {
    return null;
  }
}
