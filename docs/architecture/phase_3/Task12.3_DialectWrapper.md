# Task 12.3 — Dialect Wrapper Component & Hexagram Mapping

**Domain:** Phase 3.0 — UI & Internationalization
**Date:** 2026-03-16
**Status:** Superseded — see [Task 12.4 — Language Engine](./Task12.4_LanguageEngine.md)

---

## Overview

Task 12.3 introduces support for multiple Chinese romanizations (Mandarin Pinyin and Cantonese Jyutping) via a global dialect state and a reusable `PronunciationText` wrapper component. The feature is implemented on the Astrology/Hexagram UI as the initial test surface.

---

## Requirements Summary

| Requirement | Implementation |
|-------------|----------------|
| **Global state** | `preferredDialect` in `appStore.ts`, default `'pinyin'`, options `'pinyin'` \| `'jyutping'` |
| **Wrapper component** | `PronunciationText.vue` — props: `pinyin` (required), `jyutping` (optional) |
| **Display logic** | If dialect is `'jyutping'` and `jyutping` prop exists → show jyutping; else pinyin |
| **Transition** | Subtle CSS crossfade when dialect toggles |
| **Hexagram data** | All 64 hexagrams enriched with `jyutping_name` in `seed_hexagrams.json` |
| **UI integration** | HomeView pillar hexes + HexagramModal use `PronunciationText` |

---

## Implementation Details

### 1. Global State (`src/stores/appStore.ts`)

- `preferredDialect: "pinyin" | "jyutping"` — default `"pinyin"`
- Persisted via `loadFromStorage` / `persistToStorage`
- Migration: legacy `mandarin` → `pinyin`, `cantonese` → `jyutping`

### 2. Wrapper Component (`src/components/ui/PronunciationText.vue`)

- **Props:** `pinyin` (required string), `jyutping` (optional string)
- **Computed:** `displayText` — returns jyutping when `preferredDialect === 'jyutping'` and jyutping exists; otherwise pinyin
- **Template:** Single `<span>` with CSS transition for opacity on dialect change

### 3. Hexagram Data Enrichment

- **File:** `src/data/seed_hexagrams.json`
- **Field:** `jyutping_name` added to all 64 hexagrams with standard Cantonese Jyutping
- **Script:** `scripts/add_hexagram_jyutping.py` (used to inject jyutping)

### 4. Data Flow

- `seed_hexagrams.json` → `yiJing.ts` maps `jyutping_name` → `jyutpingName` on `YiJingHexagram`
- `HomeView.vue` builds `hexLabelMap` from seed data including `jyutping_name` for pillar hexes

### 5. UI Integration

- **HomeView.vue:** All 8 pillar hex pronunciations (Birth + Present Year/Month/Day/Hour) use:
  ```vue
  <PronunciationText
    :pinyin="hexLabel(...)?.pinyin_name || ''"
    :jyutping="hexLabel(...)?.jyutping_name"
  />
  ```
- **HexagramModal.vue:** Header pronunciation uses:
  ```vue
  <PronunciationText :pinyin="selectedHexagram?.pinyinName ?? ''" :jyutping="selectedHexagram?.jyutpingName" />
  ```

---

## Files Touched

| File | Change |
|------|--------|
| `src/stores/appStore.ts` | `preferredDialect` state, migration |
| `src/components/ui/PronunciationText.vue` | New component |
| `src/data/seed_hexagrams.json` | `jyutping_name` for 64 hexagrams |
| `src/data/yiJing.ts` | `jyutpingName` on `YiJingHexagram` |
| `src/views/HomeView.vue` | Dialect picker (Pinyin/Jyutping), pillar hexes use `PronunciationText` |
| `src/components/HexagramModal.vue` | Uses `PronunciationText`; removed legacy char maps and dialect logic |

---

## Future Work

- Extend `PronunciationText` to other Chinese text surfaces (e.g., herbs, formulas)
- Add more dialects (e.g., Taiwanese Hokkien) if required
