/**
 * Per-language localized numeral systems for the HexagramCenterView grid
 * cell that renders 1..64 in the script slot.
 *
 * For Sinosphere (Mandarin/Cantonese/Zhuyin/Taigi/Japanese/Korean/Vietnamese),
 * the canonical Chinese numeral system 一二三…十 is preserved (Korean/Japanese
 * use the same Hanzi/Hanja). For non-Sinosphere languages we use the
 * language's own digit system (Devanagari १-९, Thai ๑-๙, Lao ໑-໙, Khmer ១-៩,
 * Burmese ၁-၉, Tibetan ༡-༩) or transliterated number names where applicable.
 */

import type { LanguageCode } from "@/lib/languages";

// Digit 0..9 per language. Index = digit value.
const DIGITS_BY_LANG: Partial<Record<LanguageCode, readonly string[]>> = {
  // Chinese numerals — used by every Sinosphere language whose script slot is Hanzi/Kanji/Hangul/Vietnamese-Latin.
  // For the Chinese script slot the composer uses 十 logic; for other scripts we use plain digits.
  pinyin: ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"],
  jyutping: ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"],
  zhuyin: ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"],
  taigi: ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"],
  japanese: ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"],
  korean: ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"],
  // Vietnamese: Sino-Vietnamese digit names (Hán-Việt).
  vietnamese: [
    "",
    "Nhất",
    "Nhị",
    "Tam",
    "Tứ",
    "Ngũ",
    "Lục",
    "Thất",
    "Bát",
    "Cửu",
  ],
  hindi: ["", "१", "२", "३", "४", "५", "६", "७", "८", "९"],
  thai: ["", "๑", "๒", "๓", "๔", "๕", "๖", "๗", "๘", "๙"],
  lao: ["", "໑", "໒", "໓", "໔", "໕", "໖", "໗", "໘", "໙"],
  khmer: ["", "១", "២", "៣", "៤", "៥", "៦", "៧", "៨", "៩"],
  burmese: ["", "၁", "၂", "၃", "၄", "၅", "၆", "၇", "၈", "၉"],
  tibetan: ["", "༡", "༢", "༣", "༤", "༥", "༦", "༧", "༨", "༩"],
  // Mongolian Cyrillic — Mongolian uses Arabic digits in modern usage; render Arabic.
  mongolian: ["", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
  // Latin-script SE Asian languages — Arabic digits.
  indonesian: ["", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
  balinese: ["", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
  malay: ["", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
  filipino: ["", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
};

const SINOSPHERE_HANZI_TENS: Set<LanguageCode> = new Set([
  "pinyin",
  "jyutping",
  "zhuyin",
  "taigi",
  "japanese",
  "korean",
]);

/**
 * Format a number 1–64 as the language's localized numeral.
 * Falls back to canonical Chinese numerals.
 */
export function localizedNumeral(num: number, lang: LanguageCode): string {
  const digits = DIGITS_BY_LANG[lang];
  if (!digits) return canonicalChineseNumeral(num);

  if (SINOSPHERE_HANZI_TENS.has(lang)) {
    // Use 十 composer logic.
    if (num < 10) return digits[num] ?? "";
    if (num === 10) return "十";
    if (num < 20) return "十" + (digits[num % 10] ?? "");
    const tens = Math.floor(num / 10);
    const units = num % 10;
    return (digits[tens] ?? "") + "十" + (units === 0 ? "" : digits[units] ?? "");
  }

  // Vietnamese: Sino-Vietnamese with mười (ten) composer.
  if (lang === "vietnamese") {
    if (num < 10) return digits[num] ?? "";
    if (num === 10) return "Mười";
    if (num < 20) return "Mười " + (digits[num % 10] ?? "").toLowerCase();
    const tens = Math.floor(num / 10);
    const units = num % 10;
    const tensWord = (digits[tens] ?? "") + " mươi";
    return tensWord + (units === 0 ? "" : " " + (digits[units] ?? "").toLowerCase());
  }

  // Default for non-Sinosphere: render as the language's digit positional system.
  const tens = Math.floor(num / 10);
  const units = num % 10;
  if (tens === 0) return digits[units] ?? "";
  if (units === 0) return digits[tens] + "0";
  return (digits[tens] ?? "") + (digits[units] ?? "");
}

function canonicalChineseNumeral(num: number): string {
  const cn = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"];
  if (num < 10) return cn[num] ?? "";
  if (num === 10) return "十";
  if (num < 20) return "十" + (cn[num % 10] ?? "");
  const tens = Math.floor(num / 10);
  const units = num % 10;
  return (cn[tens] ?? "") + "十" + (units === 0 ? "" : cn[units] ?? "");
}
