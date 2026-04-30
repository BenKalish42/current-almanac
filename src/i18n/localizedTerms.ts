/**
 * Central lookup helpers for the language-aware **script** and
 * **romanization** slots across the app.
 *
 * Source of truth is the static seed JSON (hexagrams now, formulas + herbs
 * landing in later phases). Returns plain `Partial<Record<LanguageCode, …>>`
 * maps that can be spread into `<LocalizedScript :scripts>` and
 * `<PronunciationText>` props.
 */

import { YI_JING_BY_ID } from "@/data/yiJing";
import type { LanguageCode } from "@/lib/languages";

export type ScriptMap = Partial<Record<LanguageCode, string>>;
export type RomanMap = Partial<Record<LanguageCode, string>>;

/** All-empty map for terms with no per-language overrides. */
const EMPTY: Readonly<ScriptMap> = Object.freeze({});

/**
 * Per-language script-slot values for one hexagram. Missing languages fall
 * back to the canonical Hanzi at the call site (see `<LocalizedScript>`).
 */
export function hexagramScripts(hexId: number | null | undefined): ScriptMap {
  if (!hexId) return EMPTY;
  const hex = YI_JING_BY_ID.get(hexId);
  if (!hex) return EMPTY;
  const out: ScriptMap = {};
  for (const [lang, cell] of Object.entries(hex.translations) as Array<
    [LanguageCode, { script?: string; roman?: string } | undefined]
  >) {
    if (cell?.script) out[lang] = cell.script;
  }
  return out;
}

/**
 * Per-language romanization-slot values for one hexagram. Missing languages
 * fall back to the canonical Hanyu Pinyin (`<PronunciationText>`'s default).
 */
export function hexagramRomans(hexId: number | null | undefined): RomanMap {
  if (!hexId) return EMPTY;
  const hex = YI_JING_BY_ID.get(hexId);
  if (!hex) return EMPTY;
  const out: RomanMap = {};
  for (const [lang, cell] of Object.entries(hex.translations) as Array<
    [LanguageCode, { script?: string; roman?: string } | undefined]
  >) {
    if (cell?.roman) out[lang] = cell.roman;
  }
  return out;
}

/** Convenience: canonical Hanzi (simplified) for a hex. */
export function hexagramHanzi(hexId: number | null | undefined): string {
  if (!hexId) return "";
  return YI_JING_BY_ID.get(hexId)?.hanziSimplified ?? "";
}

/** Convenience: canonical traditional Hanzi for a hex. */
export function hexagramHanziTraditional(
  hexId: number | null | undefined
): string {
  if (!hexId) return "";
  const hex = YI_JING_BY_ID.get(hexId);
  return hex?.hanziTraditional ?? hex?.hanziSimplified ?? "";
}
