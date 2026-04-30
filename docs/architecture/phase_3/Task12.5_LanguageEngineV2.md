# Task 12.5 — Pan-Asian Language Engine (script + romanization swap)

**Domain:** Phase 3.0 — UI & Internationalization
**Date:** 2026-04-30
**Status:** Implemented
**Supersedes:** [Task 12.4 — Language Engine (8 langs, single-string per hex)](./Task12.4_LanguageEngine.md)

---

## Overview

Task 12.5 generalizes the language system from a per-hexagram pronunciation
label (Task 12.4) into a **two-slot script-and-romanization swap engine**
that covers every CJK + Pinyin surface in the app. Picking a language hot-
swaps:

- every **Chinese-character slot** (the big `乾`, ganzhi `甲子`, shichen
  `子初一刻`, hex-center numerals, classical formula `name_hanzi`, herb
  Hanzi) into the language's **native script**, and
- every **pinyin slot** (hex pillar romanizations, modal pronunciation,
  formula `name_pinyin`, herb `tonal_pinyin`) into the language's
  **official English-pronunciation system**.

**Out of scope by design**: English UI labels, English long-form content
(perspectives, line texts, herb actions, formula descriptions, neidan
instructions). The product stays English to unite users; only the
historically-Chinese display slots become language-aware.

---

## Languages — 18 total

| code | label | script slot | romanization standard |
|------|-------|-------------|-----------------------|
| `pinyin` | Mandarin (Pinyin) | Hanzi (Simplified) | Hanyu Pinyin w/ tones |
| `jyutping` | Cantonese (Jyutping) | Hanzi (Traditional) | Jyutping |
| `zhuyin` | Taiwanese (Zhuyin) | Hanzi (Traditional) | Bopomofo |
| `taigi` | Taiwanese (Tâi-gí) | Hanzi (Traditional) | Pe̍h-ōe-jī |
| `japanese` | Japanese (On'yomi) | Kanji | **Hepburn** |
| `korean` | Korean (한글 / RR) | Hangul | **Revised Romanization** |
| `tibetan` | Tibetan (བོད་སྐད་) | Tibetan script | **Wylie** |
| `hindi` | Hindi (हिन्दी) | Devanagari | **Hunterian** |
| `mongolian` | Mongolian (Монгол) | Cyrillic | **MNS 5217** |
| `thai` | Thai (ภาษาไทย) | Thai script | **RTGS** |
| `vietnamese` | Vietnamese (Tiếng Việt) | Latin (Quốc ngữ) | Quốc ngữ (same) |
| `indonesian` | Indonesian (Bahasa Indonesia) | Latin (phonetic) | Latin (phonetic) |
| `balinese` | Balinese (Basa Bali) | Latin (phonetic) | Latin (phonetic) |
| `malay` | Malay (Bahasa Melayu) | Latin (phonetic) | Latin (phonetic) |
| `filipino` | Filipino (Tagalog) | Latin (phonetic) | Latin (phonetic) |
| `khmer` | Khmer (ខ្មែរ) | Khmer script | **UN Romanization of Khmer** |
| `lao` | Lao (ລາວ) | Lao script | **BGN/PCGN** |
| `burmese` | Burmese (မြန်မာ) | Myanmar script | **MLC** |

The Sinosphere languages (Japanese, Korean, Vietnamese) use deterministic
Sino readings of every Hanzi we ship a value for. The non-Sinosphere
languages use phonetic transliteration of the Mandarin pinyin into the
language's native script + the language's official romanization standard.

---

## Architecture

### 1. Registry — `src/lib/languages.ts`

Each language is a `LanguageDefinition`:

```ts
interface LanguageDefinition {
  code: LanguageCode;
  label: string;
  group: string;                  // "Chinese" | "Other Asian" | "Southeast Asian"
  hexagramFieldKey: HexagramFieldKey;
  hexagramTsField: HexagramTsField;
  romanizationStandard: string;   // e.g. "Hepburn", "Revised Romanization"
  nativeScript: string;           // e.g. "Hangul", "Devanagari"
  crawlRomanizer?: (char: string) => string;
  legacyAliases?: readonly string[];
}
```

`LANGUAGES`, `LANGUAGE_BY_CODE`, `DEFAULT_LANGUAGE`, `isLanguageCode`,
`migrateLegacyLanguage`, `getGroupedLanguages`, `romanizeCharForLanguage`
are all exported from this module.

Adding a 19th language is **3 file edits**:
1. Append a `LanguageDefinition` to `LANGUAGES`.
2. Add a `{lang}_name` column / `translations[lang]` cell to seed JSONs.
3. Add an optional prop to `<PronunciationText>` and `<LocalizedScript>`'s
   `scripts` map.

### 2. Per-term `{ script, roman }` data model

Every translatable term carries a `translations` map keyed by language:

```jsonc
"translations": {
  "pinyin":     { "script": "乾", "roman": "Qián" },
  "japanese":   { "script": "乾", "roman": "Ken" },
  "korean":     { "script": "건", "roman": "geon" },
  "tibetan":    { "script": "ཁྱན", "roman": "khyan" },
  "hindi":      { "script": "छ्येन", "roman": "chhyen" },
  …
}
```

This shape is applied to:
- **Hexagrams** (`src/data/seed_hexagrams.json` × 64) — primary key `id`.
- **Classical formulas** (`src/data/formulas.json` × 2; `seed_formulas.json` × 105) — primary key `id`.
- **Herbs** (`src/data/seed_herbs.json` × 698) — `linguistics.translations`, primary key `id`.
- **GanZhi stems & branches** — static table in `src/i18n/ganzhi_localized.ts`.
- **Numerals** — static table in `src/i18n/numerals_localized.ts`.
- **Shichen primitives** — composer in `src/i18n/shichen_localized.ts`.

### 3. Components

- **`<LocalizedScript>`** (`src/components/ui/LocalizedScript.vue`) — fills
  the **script** slot. Props: `hanzi` (canonical Chinese fallback),
  `scripts: Partial<Record<LanguageCode, string>>`.
- **`<PronunciationText>`** (existing) — fills the **romanization** slot.
  18 optional props (one per language) plus the canonical `pinyin`
  fallback. Spreadable via `v-bind="...Romans(...)"`.

### 4. Composable lookups

`src/i18n/localizedTerms.ts` exposes:

- `hexagramScripts(hexId)` / `hexagramRomans(hexId)` — for Yi-Jing surfaces.
- `formulaScripts(formula)` / `formulaRomans(formula)` — for FormulaLibrary.
- `herbScripts(herb)` / `herbRomans(herb)` — for HerbInventoryManager and
  FormulaHierarchy.
- `hexagramHanzi(hexId)` / `hexagramHanziTraditional(hexId)` — canonical
  Chinese fallbacks.

For ganzhi and numerals there are dedicated helpers
(`formatGanZhiScript`, `formatGanZhiRoman`, `localizedNumeral`,
`formatShichenScript`).

### 5. Render pattern

Every CJK display slot becomes:

```vue
<LocalizedScript :hanzi="canonicalHanzi" :scripts="termScripts(termId)" />
```

Every Pinyin display slot becomes:

```vue
<PronunciationText :pinyin="canonicalPinyin" v-bind="termRomans(termId)" />
```

The wrapper components handle the active-language lookup against the
`appStore.preferredLanguage` (which already migrates from the legacy
`preferredDialect` localStorage key).

### 6. Graph database — Neo4j

`scripts/08_build_graph.py` ingests `(:Translation { parent_id, lang,
script, roman })` nodes attached via `[:HAS_TRANSLATION]` edges to
`(:Herb)` and `(:Formula)`. Composite uniqueness on `(parent_id, lang)`
plus an index on `lang`. All Cypher is parameterized.

Schema:

```cypher
(:Herb { id, pinyin, english, safety_tier, pinyin_normalized })
(:Formula { id, pinyin, english, pattern })
(:Translation { parent_id, lang, script, roman })
(:Herb)-[:HAS_TRANSLATION]->(:Translation)
(:Formula)-[:HAS_TRANSLATION]->(:Translation)

CREATE CONSTRAINT translation_parent_lang_unique
    IF NOT EXISTS FOR (t:Translation)
    REQUIRE (t.parent_id, t.lang) IS UNIQUE;

CREATE INDEX translation_lang IF NOT EXISTS
    FOR (t:Translation) ON (t.lang);
```

Query a herb in Korean:

```cypher
MATCH (h:Herb { id: 'herb_shu_di_huang' })-[:HAS_TRANSLATION]->(t:Translation { lang: 'korean' })
RETURN h.pinyin, t.script, t.roman
```

### 7. Server-side database — Supabase / Postgres

`supabase/migrations/20260430000001_create_translations.sql` adds three
tables that mirror the Neo4j shape:

- `herb_translations(herb_id, lang, script, roman, …)` — FK to `herbs(id)`.
- `formula_translations(formula_id, lang, script, roman, …)` — FK to `formulas(id)`.
- `hexagram_translations(hex_id, lang, script, roman, …)` — standalone.

Each has primary key `(parent_id, lang)`, an index on `lang`, and trigram
indexes on `script` and `roman` for substring search.

The frontend reads from seed JSON; the Postgres tables exist so server-
side endpoints (GraphRAG, future search) can adopt the same pattern
without further schema migration.

---

## Pipelines (build-time, idempotent)

| Script | Inputs | Outputs |
|--------|--------|---------|
| `scripts/13_localize_hexagrams.py` | seed_hexagrams.json | adds `translations[18]` per hex |
| `scripts/14_localize_formulas.py` | formulas.json + seed_formulas.json | adds `translations[18]` per formula |
| `scripts/15_localize_herbs.py` | seed_herbs.json | adds `linguistics.translations[18]` per herb |

All three scripts are deterministic + idempotent. Re-running overwrites
cleanly. `data/output/` mirrors are kept in sync.

---

## Component-by-component swap

| Surface | Script slot | Roman slot |
|---------|-------------|------------|
| Home pillar hex name × 8 | `<LocalizedScript>` driven by `hexagramScripts(num)` | `<PronunciationText>` w/ `v-bind="hexagramRomans(num)"` |
| Home pillar ganzhi × 8 | `formatGanZhiScript()` inside `formatGanZhiLines` | `formatGanZhiRoman()` line below |
| Home shichen sub-label | `formatShichenScript()` computed | (English label kept) |
| HexagramModal header | `<LocalizedScript>` | `<PronunciationText>` |
| HexagramCenterView grid | `<LocalizedScript>` driven by per-language `localizedNumeral()` | (no roman slot in that cell) |
| FormulaLibrary `name_hanzi` | `<LocalizedScript>` driven by `formulaScripts(f)` | — |
| FormulaLibrary `name_pinyin` | — | `<PronunciationText>` |
| HerbInventoryManager dropdown | `<LocalizedScript>` (where translation exists) | `<PronunciationText>` |
| FormulaHierarchy active-list | `<LocalizedScript>` | `<PronunciationText>` |

---

## Tests

`npm test` covers:

- `src/lib/languages.spec.ts` (21 tests) — registry shape, 18 codes,
  groups, `romanizationStandard` correctness for all official systems,
  legacy migration, all-language pinyin fallback for the crawl.
- `src/i18n/localizedTerms.spec.ts` (12 tests) — hex/formula/herb script
  + roman extraction; null-safety.
- `src/i18n/ganzhi_localized.spec.ts` (13 tests) — stem + branch readings
  across Sinosphere and non-Sinosphere langs; `甲子` composition.
- `src/i18n/numerals_localized.spec.ts` (10 tests) — Mandarin 十 composer,
  Vietnamese Sino-Vietnamese names, Devanagari/Thai/Lao/Khmer/Burmese
  digits, Tibetan digits, Arabic-digit fallbacks for Latin-script langs.
- `src/lib/alchemyStore.spec.ts` + `src/utils/heuristicRater.spec.ts`
  unchanged.

Total: **58 tests passing**.

---

## Known limitations / honest caveats

- For non-Sinosphere languages and for the 698 herb names, transliterations
  are **best-effort phonetic** based on syllable mappings. They are
  pronunciation aids, not classically attested terminology. The display
  layer falls back to canonical Hanzi/Pinyin whenever a target-language
  cell is empty, so the system never breaks — it just shows the underlying
  Chinese.
- Per-character ruby in the opening crawl (`AstrologyCrawlBackdrop`) still
  uses the existing pinyin fallback for non-Mandarin languages — a real
  per-character JP/KR/etc. dictionary is out of scope.
- Tibetan/Hindi/Khmer/etc. transliteration was authored without native-
  speaker review; community contributions can refine the data via plain
  JSON edits + script re-runs.
- Vietnamese herb / formula names: a full Hán-Việt dictionary is not
  bundled, so script and roman slots both default to the Latin pinyin for
  those terms. Sinosphere readings *are* applied for hex names + ganzhi
  + the 7 chars of the FormulaLibrary's classical formulas.

---

## How to add a 19th language

1. **Registry** (`src/lib/languages.ts`): append a `LanguageDefinition`
   with `code`, `label`, `group`, `hexagramFieldKey`, `hexagramTsField`,
   `romanizationStandard`, `nativeScript`. Add to the `LanguageCode`
   union.
2. **Pipeline scripts**: extend `13_localize_hexagrams.py`,
   `14_localize_formulas.py`, `15_localize_herbs.py` with mappings for
   the new language. Run them.
3. **Components**: add a new optional prop on `<PronunciationText>` and
   include it in the `lookup` map. (`<LocalizedScript>` is already
   generic.)
4. **Static tables**: extend `ganzhi_localized.ts` (10 stems + 12
   branches), `numerals_localized.ts` (digit table + composer rules),
   `shichen_localized.ts` (chu/zheng + ke unit) for the new language.
5. **Neo4j / Supabase**: no schema change needed — both stores key on
   the dynamic `lang` column.

Total: ~6 files touched + a script run. Settings dropdown picks it up
automatically from the registry.

---

## Files touched

**New**
- `src/i18n/localizedTerms.ts` (+ `.spec.ts`)
- `src/i18n/ganzhi_localized.ts` (+ `.spec.ts`)
- `src/i18n/numerals_localized.ts` (+ `.spec.ts`)
- `src/i18n/shichen_localized.ts`
- `src/components/ui/LocalizedScript.vue`
- `scripts/13_localize_hexagrams.py`
- `scripts/14_localize_formulas.py`
- `scripts/15_localize_herbs.py`
- `supabase/migrations/20260430000001_create_translations.sql`

**Modified**
- `src/lib/languages.ts` (10 → 18 langs; +`romanizationStandard`, +`nativeScript`)
- `src/lib/languages.spec.ts`
- `src/data/seed_hexagrams.json` (`translations[18]` per hex; `hanzi_*` fields)
- `data/output/seed_hexagrams.json`
- `src/data/yiJing.ts` (`translations` API + `getHexagramTranslation`)
- `src/data/formulas.json` (`translations[18]` per classical formula)
- `src/data/seed_formulas.json` + `data/output/` mirror
- `src/data/seed_herbs.json` + `data/output/` mirror
- `src/data/schema_formulas.ts` (`FormulaTranslation` type)
- `src/stores/alchemyStore.ts` (`HerbTranslationCell` type)
- `src/components/ui/PronunciationText.vue` (10 → 18 props)
- `src/components/AstrologyCrawlBackdrop.vue` (RubyProps shape)
- `src/views/HomeView.vue` (8 hex-name + 8 ruby + 8 ganzhi + shichen sites)
- `src/views/HexagramCenterView.vue` (numeral cell)
- `src/components/HexagramModal.vue` (header script + roman)
- `src/components/alchemy/FormulaLibrary.vue`
- `src/components/alchemy/HerbInventoryManager.vue`
- `src/components/alchemy/FormulaHierarchy.vue`
- `scripts/08_build_graph.py` (+:Translation ingestion)
- `docs/architecture/phase_3/Task12.4_LanguageEngine.md` (mark superseded)
