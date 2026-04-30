# Task 12.4 — Language Engine (replaces "Dialects")

**Domain:** Phase 3.0 — UI & Internationalization
**Date:** 2026-04-30
**Status:** Superseded — see [Task 12.5 — Pan-Asian Language Engine](./Task12.5_LanguageEngineV2.md)
**Supersedes:** [Task 12.3 — Dialect Wrapper Component & Hexagram Mapping](./Task12.3_DialectWrapper.md)

---

## Overview

Task 12.4 generalizes the per-hexagram pronunciation system from "dialects" (4 Chinese romanizations) into a registry-driven **language engine** that supports 8 languages today and is configured to make adding a 9th, 10th, … language a one-file change.

Concretely, the user can now choose any of:

| Group        | Code       | Label                  | Source                                            |
| ------------ | ---------- | ---------------------- | ------------------------------------------------- |
| Chinese      | `pinyin`   | Mandarin (Pinyin)      | Mandarin pinyin (existing)                        |
| Chinese      | `jyutping` | Cantonese (Jyutping)   | Cantonese jyutping (existing)                     |
| Chinese      | `zhuyin`   | Taiwanese (Zhuyin)     | Bopomofo (existing)                               |
| Chinese      | `taigi`    | Taiwanese (Tâi-gí)     | Pe̍h-ōe-jī (existing)                              |
| Other Asian  | `japanese` | Japanese (On'yomi)     | Sino-Japanese on'yomi readings of the Hanzi names |
| Other Asian  | `korean`   | Korean (한글 / RR)      | Sino-Korean Hangul + Revised Romanization         |
| Other Asian  | `tibetan`  | Tibetan (བོད་སྐད་)       | Phonetic transliteration of Mandarin pinyin       |
| Other Asian  | `hindi`    | Hindi (हिन्दी)           | Phonetic transliteration of Mandarin pinyin       |

> **A note on accuracy:** Tibetan and Hindi do not have a classical Yi-Jing transliteration tradition. The values shipped in `seed_hexagrams.json` are best-effort phonetic spellings of each hexagram's Mandarin pinyin in the target script. They are intended as approximate pronunciation aids, not canonical names. Japanese on'yomi and Korean Hanja readings, by contrast, are deterministic and well-attested.

---

## Architecture

### 1. Registry (`src/lib/languages.ts`)

Single source of truth. Each language is a `LanguageDefinition`:

```ts
export interface LanguageDefinition {
  code: LanguageCode;            // "pinyin" | "jyutping" | … | "hindi"
  label: string;                 // dropdown text
  group: string;                 // optgroup label
  hexagramFieldKey: HexagramFieldKey; // "pinyin_name" | … | "hindi_name"
  hexagramTsField: HexagramTsField;   // "pinyinName" | … | "hindiName"
  crawlRomanizer?: (char: string) => string; // optional per-char ruby
  legacyAliases?: readonly string[];          // localStorage migration
}
```

Public helpers:

- `LANGUAGES` — ordered tuple of all definitions.
- `LANGUAGE_BY_CODE` — `Map<LanguageCode, LanguageDefinition>`.
- `DEFAULT_LANGUAGE` — `"pinyin"`.
- `isLanguageCode(v)` — type guard.
- `migrateLegacyLanguage(v)` — accepts unknown input (including legacy `mandarin`/`cantonese`/`preferredDialect` payloads) and returns a current `LanguageCode`.
- `getGroupedLanguages()` — dropdown groups in registry order.
- `romanizeCharForLanguage(char, code)` — per-char ruby with pinyin fallback.

### 2. State (`src/stores/appStore.ts`)

- `preferredLanguage: LanguageCode` (default `"pinyin"`).
- Persisted in localStorage key `current_almanac_user_state_v1` under field `preferredLanguage`.
- Backward compat: `loadFromStorage` reads `preferredLanguage` if present, otherwise falls back to legacy `preferredDialect`. Both routes pass through `migrateLegacyLanguage`, so even older `mandarin`/`cantonese` strings migrate cleanly.
- `PreferredDialect` type is retained as a deprecated alias of `PreferredLanguage` for one release.

### 3. Display (`src/components/ui/PronunciationText.vue`)

Backward-compatible API: existing props (`pinyin`, `jyutping`, `zhuyin`, `taigi`) are unchanged; four new optional props (`japanese`, `korean`, `tibetan`, `hindi`) extend the component. Internally `displayText` is a registry-driven lookup that falls back to `pinyin` if the chosen language has no value.

### 4. Crawl ruby (`src/lib/crawlRomanization.ts`)

The opening-crawl backdrop renders per-character ruby above each Hanzi. The romanizer is delegated to the registry (`romanizeCharForLanguage`). Languages without a bundled per-character library — including `taigi`, `japanese`, `korean`, `tibetan`, `hindi` — fall back to no-tone Mandarin pinyin. This matches the original Taigi behaviour. **Authoritative per-hexagram readings live in the seed JSON, not in the crawl.**

### 5. Settings UI (`src/components/settings/AppSettingsFields.vue`)

The dropdown is rendered from `getGroupedLanguages()` with `<optgroup>` per group. Adding a language to the registry auto-populates the dropdown.

### 6. Per-hex data (`src/data/seed_hexagrams.json`)

Each of the 64 hexagrams now has 8 reading fields:

```json
{
  "id": 1,
  "pinyin_name": "Qián",
  "jyutping_name": "kin4",
  "zhuyin_name": "ㄑㄧㄢˊ",
  "taigi_name": "Kiân",
  "japanese_name": "Ken",
  "korean_name": "건 (geon)",
  "tibetan_name": "ཁྱན",
  "hindi_name": "छ्येन",
  …
}
```

The Japanese/Korean/Tibetan/Hindi values are committed by `scripts/12_enrich_hexagram_languages.py`, which is idempotent — re-run it whenever the source mapping changes.

`src/data/yiJing.ts` projects these snake-case fields onto the camel-case `YiJingHexagram` interface.

---

## Adding a 9th language

1. **Registry**: add a new entry to `LANGUAGES` in `src/lib/languages.ts` with a unique `code`, `label`, `group`, and `hexagramFieldKey` / `hexagramTsField`.
2. **Seed data**: add a new column to each hex in `src/data/seed_hexagrams.json` (e.g. via a script in `scripts/`). Mirror to `data/output/seed_hexagrams.json`.
3. **PronunciationText**: add an optional prop to `src/components/ui/PronunciationText.vue` and wire it into the lookup map.
4. **Optional**: extend `src/data/yiJing.ts` to expose the new TS field.

That's it. The settings dropdown, the home pillars, and the hexagram modal will pick up the new language automatically.

---

## Files touched

**New**
- `src/lib/languages.ts`
- `src/lib/languages.spec.ts`
- `scripts/12_enrich_hexagram_languages.py`
- `docs/architecture/phase_3/Task12.4_LanguageEngine.md` (this doc)

**Modified**
- `src/stores/appStore.ts`
- `src/components/ui/PronunciationText.vue`
- `src/components/AstrologyCrawlBackdrop.vue`
- `src/components/settings/AppSettingsFields.vue`
- `src/lib/crawlRomanization.ts`
- `src/data/seed_hexagrams.json` (and `data/output/` mirror)
- `src/data/yiJing.ts`
- `src/views/HomeView.vue`
- `src/components/HexagramModal.vue`
