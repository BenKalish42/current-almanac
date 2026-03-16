# Phase 1.9 — Task 8: Linguistic Architecture

**Domain:** Linguistic Architecture (Frontend Schema)  
**Purpose:** Handoff summary for Gemini AI CTO

---

## What Was Built

Herb schema extended to support dialectal variations, aliases, and LLM linguistic enrichment. Search upgraded to match aliases; UI updated to show tonal pinyin and alias-match indicators.

### 1. `src/stores/alchemyStore.ts`

**Interface updates:**
- `aliases?: string[]` — alternate names for search (e.g. `["Gui Zhi"]` for pinyin `"Guizi"`)
- `linguistics?: { tonal_pinyin?, jyutping?, hokkien? }` — LLM enrichment

**searchHerbs:** Now matches query against `pinyin_name`, `common_name`, `english_name`, OR any `aliases[]` entry. Uses optional chaining; degrades gracefully when fields absent.

### 2. `src/components/alchemy/HerbInventoryManager.vue`

**UI updates:**
- **Primary name:** If `herb.linguistics?.tonal_pinyin` exists, display that; else `pinyin_name`
- **Alias match:** When search hits an alias, show `(Alias match: Gui Zhi)` in muted text under the main name
- **Active list:** Uses `displayPinyin(herb)` for consistency

---

## Files Touched

| File | Change |
|------|--------|
| `src/stores/alchemyStore.ts` | Herb interface, HerbLinguistics type, searchHerbs getter |
| `src/components/alchemy/HerbInventoryManager.vue` | displayPinyin, getMatchedAlias, template updates |
| `docs/architecture/phase_1/Task8_LinguisticSchema.md` | Created |
| `docs/handoff/Phase1-Task8.md` | Created |

---

## Usage

Herb JSON can now include (optional):

```json
{
  "id": "herb_sym_001",
  "pinyin_name": "Guizi",
  "common_name": "Cinnamon Twig",
  "aliases": ["Gui Zhi"],
  "linguistics": {
    "tonal_pinyin": "Guì Zhī",
    "jyutping": "gwai3 zi1",
    "hokkien": ""
  },
  ...
}
```

Search for `"Gui Zhi"` → matches via alias → shows `(Alias match: Gui Zhi)` in dropdown.
