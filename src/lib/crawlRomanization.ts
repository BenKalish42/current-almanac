import {
  romanizeCharForLanguage,
  type LanguageCode,
} from "@/lib/languages";

/** Mirrors `LanguageCode` for the crawl ruby. Kept as a separate alias so
 *  callers that only need the crawl subset don't depend on the entire enum. */
export type CrawlLanguage = LanguageCode;
/** @deprecated Renamed to `CrawlLanguage`. Kept temporarily for back-compat. */
export type CrawlDialect = CrawlLanguage;

/**
 * Per-character ruby romanization for the opening crawl. Delegates entirely to
 * the language registry; languages without a bundled romanizer fall back to
 * Mandarin pinyin (no tones), matching the pre-existing `taigi` behaviour.
 */
export function romanizeCrawlChar(char: string, lang: CrawlLanguage): string {
  return romanizeCharForLanguage(char, lang);
}
