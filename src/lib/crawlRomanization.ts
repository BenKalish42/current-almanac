import { pinyin } from "pinyin-pro";
import { getJyutping } from "to-jyutping";
import { pinyinToZhuyin } from "pinyin-zhuyin";

/** Mirrors PreferredDialect from appStore — keep lib free of Pinia. */
export type CrawlDialect = "pinyin" | "jyutping" | "zhuyin" | "taigi";

/** Han script (includes many classical variants); punctuation uses separate code points and gets no ruby. */
const isCJK = (ch: string) => ch.length === 1 && /\p{Script=Han}/u.test(ch);

/**
 * Romanization for one Hanzi for the classical crawl, following global dialect:
 * - pinyin: Mandarin (tone marks off for density)
 * - jyutping: Cantonese (library segmentation)
 * - zhuyin: Bopomofo via pinyin → zhuyin
 * - taigi: no open-source per-char Taigi in bundle — fallback to Mandarin pinyin (same as hex labels)
 */
export function romanizeCrawlChar(char: string, dialect: CrawlDialect): string {
  if (!isCJK(char)) return "";
  try {
    if (dialect === "pinyin") {
      return pinyin(char, { toneType: "none", type: "string", traditional: true }).trim();
    }
    if (dialect === "jyutping") {
      return getJyutping(char).replace(/\s+/g, " ").trim();
    }
    if (dialect === "zhuyin") {
      const py = pinyin(char, { toneType: "symbol", type: "string", traditional: true }).trim();
      return pinyinToZhuyin(py).trim();
    }
    if (dialect === "taigi") {
      return pinyin(char, { toneType: "none", type: "string", traditional: true }).trim();
    }
  } catch {
    return "";
  }
  return "";
}
