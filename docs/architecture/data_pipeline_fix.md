# Data Pipeline: Herb Bridge (Frontend Hydration)

**Script:** `scripts/07b_bridge_herbs_to_frontend.py`  
**Purpose:** Bridge 500+ scraped herbs from `data/output/seed_herbs.json` to the Alchemy UI schema at `src/data/seed_herbs.json`.

---

## Summary

The frontend was previously restricted to an orphaned 18-herb seed file. This script loads the scraped herb corpus (SymMap/TCMSP schema), maps it to the Alchemy UI schema, and overwrites `src/data/seed_herbs.json` so the HerbInventoryManager, FormulaHierarchy, and other components have access to the full herb database.

---

## Schema Mapping

| UI Field | Source | Notes |
|----------|--------|-------|
| `id` | `id` | Keep as is |
| `pinyin_name` | `pinyin_name` | Keep as is |
| `common_name` | `english_name` or fallback `chinese_name` | |
| `safety_tier` | `safety_tier` | Default 1 if missing |
| `properties.temperature` | Extracted from `properties[]` | Keywords: Cold, Warm, Hot, Cool, Calm, Neutral (and Slightly/Very variants) |
| `properties.flavor` | Remainder of `properties[]` | Non-temperature terms (Pungent, Bitter, Sweet, etc.) |
| `properties.meridians` | Top-level `meridians[]` | Direct mapping |
| `actions` | — | Default `["Harmonizes systemic function"]` (LLM enrichment planned) |
| `contraindications` | — | Default `""` |

---

## Usage

```bash
python scripts/07b_bridge_herbs_to_frontend.py
```

**Output:** Overwrites `src/data/seed_herbs.json` with the mapped herb array.

---

## Future Enrichment

- **Actions:** SymMap may not have detailed actions; placeholder used. Plan to enrich with LLMs.
- **Contraindications:** Not present in source; could be added from external data or LLM.
