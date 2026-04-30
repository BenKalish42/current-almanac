/**
 * Language registry — single source of truth for the app's pronunciation /
 * romanization options. Adding a new language is a registry-only edit (plus
 * a per-hex reading column in `seed_hexagrams.json` and one prop on
 * `PronunciationText`). See `docs/architecture/phase_3/Task12.4_LanguageEngine.md`.
 */

import { pinyin } from "pinyin-pro";
import { getJyutping } from "to-jyutping";
import { pinyinToZhuyin } from "pinyin-zhuyin";

/** All supported language codes. Keep this union as the single source of truth. */
export type LanguageCode =
  | "pinyin"
  | "jyutping"
  | "zhuyin"
  | "taigi"
  | "japanese"
  | "korean"
  | "tibetan"
  | "hindi";

/** Field name in `seed_hexagrams.json` (snake_case). */
export type HexagramFieldKey =
  | "pinyin_name"
  | "jyutping_name"
  | "zhuyin_name"
  | "taigi_name"
  | "japanese_name"
  | "korean_name"
  | "tibetan_name"
  | "hindi_name";

/** Camel-cased TS field name on `YiJingHexagram`. */
export type HexagramTsField =
  | "pinyinName"
  | "jyutpingName"
  | "zhuyinName"
  | "taigiName"
  | "japaneseName"
  | "koreanName"
  | "tibetanName"
  | "hindiName";

export interface LanguageDefinition {
  code: LanguageCode;
  /** UI label shown in the settings dropdown, e.g. "Mandarin (Pinyin)". */
  label: string;
  /** Optgroup label, e.g. "Chinese", "Other Asian". */
  group: string;
  /** Field name in `seed_hexagrams.json`. */
  hexagramFieldKey: HexagramFieldKey;
  /** Camel-cased TS field on `YiJingHexagram`. */
  hexagramTsField: HexagramTsField;
  /**
   * Optional per-character romanizer used by the opening crawl ruby text.
   * If omitted, the crawl falls back to Mandarin pinyin (no tones) for that
   * language — matching the existing `taigi` behaviour. Authoritative
   * per-hexagram readings live in the seed JSON, not here.
   */
  crawlRomanizer?: (char: string) => string;
  /** Legacy localStorage values that should migrate onto this code. */
  legacyAliases?: readonly string[];
}

const isCJK = (ch: string) => ch.length === 1 && /\p{Script=Han}/u.test(ch);

function pinyinFor(char: string): string {
  if (!isCJK(char)) return "";
  try {
    return pinyin(char, { toneType: "none", type: "string", traditional: true }).trim();
  } catch {
    return "";
  }
}

function jyutpingFor(char: string): string {
  if (!isCJK(char)) return "";
  try {
    return getJyutping(char).replace(/\s+/g, " ").trim();
  } catch {
    return "";
  }
}

function zhuyinFor(char: string): string {
  if (!isCJK(char)) return "";
  try {
    const py = pinyin(char, { toneType: "symbol", type: "string", traditional: true }).trim();
    return pinyinToZhuyin(py).trim();
  } catch {
    return "";
  }
}

/**
 * Ordered registry. UI dropdowns honour this order. Groups are rendered as
 * `<optgroup>` blocks in the same order they first appear here.
 */
export const LANGUAGES: readonly LanguageDefinition[] = [
  {
    code: "pinyin",
    label: "Mandarin (Pinyin)",
    group: "Chinese",
    hexagramFieldKey: "pinyin_name",
    hexagramTsField: "pinyinName",
    crawlRomanizer: pinyinFor,
    legacyAliases: ["mandarin"],
  },
  {
    code: "jyutping",
    label: "Cantonese (Jyutping)",
    group: "Chinese",
    hexagramFieldKey: "jyutping_name",
    hexagramTsField: "jyutpingName",
    crawlRomanizer: jyutpingFor,
    legacyAliases: ["cantonese"],
  },
  {
    code: "zhuyin",
    label: "Taiwanese (Zhuyin)",
    group: "Chinese",
    hexagramFieldKey: "zhuyin_name",
    hexagramTsField: "zhuyinName",
    crawlRomanizer: zhuyinFor,
  },
  {
    code: "taigi",
    label: "Taiwanese (Tâi-gí)",
    group: "Chinese",
    hexagramFieldKey: "taigi_name",
    hexagramTsField: "taigiName",
    // No bundled per-character Taigi dictionary — fall back to pinyin (no tones).
    crawlRomanizer: pinyinFor,
  },
  {
    code: "japanese",
    label: "Japanese (On'yomi)",
    group: "Other Asian",
    hexagramFieldKey: "japanese_name",
    hexagramTsField: "japaneseName",
    // No bundled Kanji-on'yomi dictionary — per-hex names live in the seed JSON.
    crawlRomanizer: pinyinFor,
  },
  {
    code: "korean",
    label: "Korean (한글 / RR)",
    group: "Other Asian",
    hexagramFieldKey: "korean_name",
    hexagramTsField: "koreanName",
    crawlRomanizer: pinyinFor,
  },
  {
    code: "tibetan",
    label: "Tibetan (བོད་སྐད་)",
    group: "Other Asian",
    hexagramFieldKey: "tibetan_name",
    hexagramTsField: "tibetanName",
    // Phonetic-only — no classical Yi-Jing transliteration tradition.
    crawlRomanizer: pinyinFor,
  },
  {
    code: "hindi",
    label: "Hindi (हिन्दी)",
    group: "Other Asian",
    hexagramFieldKey: "hindi_name",
    hexagramTsField: "hindiName",
    // Phonetic-only — see Task12.4 doc.
    crawlRomanizer: pinyinFor,
  },
] as const;

export const LANGUAGE_BY_CODE: ReadonlyMap<LanguageCode, LanguageDefinition> = new Map(
  LANGUAGES.map((l) => [l.code, l])
);

export const DEFAULT_LANGUAGE: LanguageCode = "pinyin";

const VALID_CODES: ReadonlySet<string> = new Set(LANGUAGES.map((l) => l.code));

/** Type guard. */
export function isLanguageCode(value: unknown): value is LanguageCode {
  return typeof value === "string" && VALID_CODES.has(value);
}

/**
 * Migrate an arbitrary localStorage value (potentially a legacy "dialect" code,
 * or `undefined`/`null`) onto a current `LanguageCode`. Falls back to the
 * default language for unknown input.
 */
export function migrateLegacyLanguage(value: unknown): LanguageCode {
  if (typeof value !== "string") return DEFAULT_LANGUAGE;
  if (isLanguageCode(value)) return value;
  for (const def of LANGUAGES) {
    if (def.legacyAliases?.includes(value)) return def.code;
  }
  return DEFAULT_LANGUAGE;
}

/** Languages grouped for `<optgroup>` rendering, preserving registry order. */
export function getGroupedLanguages(): Array<{ label: string; items: LanguageDefinition[] }> {
  const order: string[] = [];
  const buckets = new Map<string, LanguageDefinition[]>();
  for (const lang of LANGUAGES) {
    if (!buckets.has(lang.group)) {
      buckets.set(lang.group, []);
      order.push(lang.group);
    }
    buckets.get(lang.group)!.push(lang);
  }
  return order.map((label) => ({ label, items: buckets.get(label)! }));
}

/**
 * Per-character romanization for the crawl ruby. Languages without a bundled
 * dictionary fall back to Mandarin pinyin (no tones) — same convention as
 * the original `taigi` behaviour.
 */
export function romanizeCharForLanguage(char: string, code: LanguageCode): string {
  const def = LANGUAGE_BY_CODE.get(code);
  if (!def) return pinyinFor(char);
  return (def.crawlRomanizer ?? pinyinFor)(char);
}
