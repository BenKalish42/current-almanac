# Task 11.3 - Yi Jing Data Enrichment

## What was added

- Created `src/data/yiJing.ts` as the enriched Yi Jing dictionary source.
- Added two normalized fields for all 64 hexagrams:
  - `englishName`
  - `trigrams`

## englishName enrichment

- `englishName` is sourced from the existing seed dictionary and normalized with targeted consensus overrides:
  - `1 -> "The Creative / Heaven"`
  - `2 -> "The Receptive / Earth"`
  - `50 -> "The Caldron"`

## Trigram enrichment

- `trigrams` is computed from canonical hexagram binary structure (`HEX_BINARY_TOP_TO_BOTTOM` in `src/core/iching.ts`).
- Upper and lower trigrams are parsed from the first 3 and last 3 bits of each 6-line binary value.
- Output format:
  - `Upper: <Trigram> (<Element>) / Lower: <Trigram> (<Element>)`
- Trigram dictionary used:
  - `Qian (Heaven)`, `Kun (Earth)`, `Kan (Water)`, `Li (Fire)`,
    `Gen (Mountain)`, `Zhen (Thunder)`, `Sun (Wind/Wood)`, `Dui (Lake/Marsh)`.

## UI integration

- Updated `src/components/HexagramModal.vue` to consume enriched entries from `YI_JING_BY_ID`.
- Header now includes English title:
  - `HEXAGRAM #<n> • <Hanzi> (<englishName>)`
- Subtitle now includes both linguistic pronunciation and trigram structure:
  - `<Dialect label>: <Pronunciation> | <trigrams>`
