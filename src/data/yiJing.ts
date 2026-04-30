import seedHexagrams from "@/data/seed_hexagrams.json";
import { HEX_BINARY_TOP_TO_BOTTOM } from "@/core/iching";
import type { LanguageCode } from "@/lib/languages";

/**
 * Per-hexagram translation cell — the new canonical shape (Task 12.5).
 *
 * `script` is what fills the "Chinese-character" display slot (e.g. Hanzi for
 * pinyin, Hangul for korean, Devanagari for hindi). `roman` is the
 * romanization-slot value (Hanyu Pinyin for pinyin, Revised Romanization for
 * korean, Hunterian for hindi, …).
 */
export interface HexagramTranslation {
  script: string;
  roman: string;
}

type SeedHexagram = {
  id: number;
  pinyin_name: string;
  english_name: string;
  jyutping_name?: string;
  zhuyin_name?: string;
  taigi_name?: string;
  japanese_name?: string;
  korean_name?: string;
  tibetan_name?: string;
  hindi_name?: string;
  hanzi_simplified?: string;
  hanzi_traditional?: string;
  translations?: Partial<Record<LanguageCode, HexagramTranslation>>;
};

type TrigramDefinition = {
  pinyin: string;
  gloss: string;
};

export type YiJingHexagram = {
  id: number;
  pinyinName: string;
  englishName: string;
  jyutpingName?: string;
  zhuyinName?: string;
  taigiName?: string;
  japaneseName?: string;
  koreanName?: string;
  tibetanName?: string;
  hindiName?: string;
  /** Hanzi simplified form, e.g. "乾". Always present. */
  hanziSimplified: string;
  /** Hanzi traditional form, e.g. "乾". Always present. */
  hanziTraditional: string;
  /** Per-language { script, roman } translation cells, indexed by LanguageCode. */
  translations: Partial<Record<LanguageCode, HexagramTranslation>>;
  trigrams: string;
};

const TRIGRAM_BY_BINARY_TOP_TO_BOTTOM: Record<string, TrigramDefinition> = {
  "111": { pinyin: "Qian", gloss: "Heaven" },
  "000": { pinyin: "Kun", gloss: "Earth" },
  "010": { pinyin: "Kan", gloss: "Water" },
  "101": { pinyin: "Li", gloss: "Fire" },
  "100": { pinyin: "Gen", gloss: "Mountain" },
  "001": { pinyin: "Zhen", gloss: "Thunder" },
  "110": { pinyin: "Sun", gloss: "Wind/Wood" },
  "011": { pinyin: "Dui", gloss: "Lake/Marsh" },
};

const ENGLISH_NAME_OVERRIDES: Record<number, string> = {
  1: "The Creative / Heaven",
  2: "The Receptive / Earth",
  50: "The Caldron",
};

function getTrigramBreakdown(hexagramId: number) {
  const binary = HEX_BINARY_TOP_TO_BOTTOM[hexagramId];
  if (!binary) return "Upper: Unknown / Lower: Unknown";
  const upper = TRIGRAM_BY_BINARY_TOP_TO_BOTTOM[binary.slice(0, 3)];
  const lower = TRIGRAM_BY_BINARY_TOP_TO_BOTTOM[binary.slice(3, 6)];
  if (!upper || !lower) return "Upper: Unknown / Lower: Unknown";
  return `Upper: ${upper.pinyin} (${upper.gloss}) / Lower: ${lower.pinyin} (${lower.gloss})`;
}

export const YI_JING_HEXAGRAMS: YiJingHexagram[] = (seedHexagrams as SeedHexagram[])
  .map((hex) => ({
    id: hex.id,
    pinyinName: hex.pinyin_name,
    englishName: ENGLISH_NAME_OVERRIDES[hex.id] ?? hex.english_name,
    jyutpingName: hex.jyutping_name,
    zhuyinName: hex.zhuyin_name,
    taigiName: hex.taigi_name,
    japaneseName: hex.japanese_name,
    koreanName: hex.korean_name,
    tibetanName: hex.tibetan_name,
    hindiName: hex.hindi_name,
    hanziSimplified: hex.hanzi_simplified ?? "",
    hanziTraditional: hex.hanzi_traditional ?? hex.hanzi_simplified ?? "",
    translations: hex.translations ?? {},
    trigrams: getTrigramBreakdown(hex.id),
  }))
  .sort((a, b) => a.id - b.id);

export const YI_JING_BY_ID = new Map<number, YiJingHexagram>(
  YI_JING_HEXAGRAMS.map((hex) => [hex.id, hex])
);

/**
 * Look up the per-language translation cell for a hexagram. Returns
 * `undefined` if either the hex or the language has no entry — callers
 * should fall back to the canonical Hanzi/Pinyin in that case.
 */
export function getHexagramTranslation(
  hexId: number,
  lang: LanguageCode
): HexagramTranslation | undefined {
  return YI_JING_BY_ID.get(hexId)?.translations[lang];
}
