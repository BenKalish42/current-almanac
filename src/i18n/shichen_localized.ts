/**
 * Per-language localization of the ShiChen sub-label rendered on Home, e.g.
 *   `子初一刻` (Mandarin)
 *   `자초일각` (Korean)
 *   `Tý sơ nhất khắc` (Vietnamese)
 *
 * Composes the localized form from primitives:
 *   - branch (12 Earthly Branches)  — see ganzhi_localized.ts
 *   - chu/zheng                      — 初 / 正
 *   - ke index in half-shichen 1..4
 *   - 刻 (the unit "ke")
 */

import type { LanguageCode } from "@/lib/languages";
import { getBranchCell } from "@/i18n/ganzhi_localized";
import { localizedNumeral } from "@/i18n/numerals_localized";

/** chu (初) / zheng (正) per language. */
const CHU_ZHENG_BY_LANG: Partial<
  Record<LanguageCode, { chu: string; zheng: string }>
> = {
  pinyin: { chu: "初", zheng: "正" },
  jyutping: { chu: "初", zheng: "正" },
  zhuyin: { chu: "初", zheng: "正" },
  taigi: { chu: "初", zheng: "正" },
  japanese: { chu: "初", zheng: "正" },
  korean: { chu: "초", zheng: "정" },
  vietnamese: { chu: "Sơ", zheng: "Chính" },
  tibetan: { chu: "ཁྲུའུ", zheng: "ཀྲིང" },
  hindi: { chu: "छू", zheng: "चङ" },
  mongolian: { chu: "Чу", zheng: "Жэн" },
  thai: { chu: "ฉู", zheng: "เจิ้ง" },
  khmer: { chu: "ឈូ", zheng: "ជឹង" },
  lao: { chu: "ຊູ", zheng: "ເຈິ່ງ" },
  burmese: { chu: "ချူ", zheng: "ဂျင်း" },
  indonesian: { chu: "Chu", zheng: "Zheng" },
  balinese: { chu: "Chu", zheng: "Zheng" },
  malay: { chu: "Chu", zheng: "Zheng" },
  filipino: { chu: "Chu", zheng: "Zheng" },
};

/** "刻" (ke = quarter-hour) per language. */
const KE_BY_LANG: Partial<Record<LanguageCode, string>> = {
  pinyin: "刻",
  jyutping: "刻",
  zhuyin: "刻",
  taigi: "刻",
  japanese: "刻",
  korean: "각",
  vietnamese: "khắc",
  tibetan: "ཁེ",
  hindi: "के",
  mongolian: "Кэ",
  thai: "เข่อ",
  khmer: "ឃឺ",
  lao: "ເຄິ່",
  burmese: "ခေး",
  indonesian: "Ke",
  balinese: "Ke",
  malay: "Ke",
  filipino: "Ke",
};

/**
 * Compose the localized ShiChen full label.
 *
 * @param branchHanzi - the canonical Hanzi branch char (e.g. "子")
 * @param chuZheng - "chu" | "zheng"
 * @param keInHalf - 1..4
 * @param lang - active language code
 */
export function formatShichenScript(
  branchHanzi: string,
  chuZheng: "chu" | "zheng",
  keInHalf: number,
  lang: LanguageCode
): string {
  const branchCell = getBranchCell(branchHanzi, lang);
  const branch = branchCell?.script ?? branchHanzi;
  const cz = CHU_ZHENG_BY_LANG[lang]?.[chuZheng] ?? (chuZheng === "chu" ? "初" : "正");
  const num = localizedNumeral(keInHalf, lang);
  const ke = KE_BY_LANG[lang] ?? "刻";

  // For most non-Latin scripts, no spaces; for Latin-script SE Asian languages and
  // Vietnamese/Mongolian (Cyrillic), use space-separated to match natural reading.
  const useSpaces = [
    "vietnamese",
    "indonesian",
    "balinese",
    "malay",
    "filipino",
    "mongolian",
  ].includes(lang as string);
  return useSpaces
    ? `${branch} ${cz} ${num} ${ke}`
    : `${branch}${cz}${num}${ke}`;
}
