# Phase 1 — Prompt 1: Alchemy Pillar (State Management)

**Handoff for Gemini AI CTO**

---

## Summary

Centralized state for the Alchemy formula builder in a new Pinia store using Vue 3 Composition API setup syntax.

## Deliverable

- **File:** `src/stores/alchemyStore.ts`

## Implementation

### Data Ingestion

- Imports `seedHerbs` from `@/data/seed_herbs.json`
- Imports `seedFormulas` from `@/data/seed_formulas.json`

### State Variables

| Variable        | Type      | Description                                                |
|----------------|-----------|------------------------------------------------------------|
| `herbs`        | `Herb[]`  | All herbs (from seed)                                      |
| `formulas`     | `Formula[]` | All formulas (from seed)                                 |
| `activeFormula`| `Herb[]`  | Herbs currently selected for custom formula building       |
| `npdiWarnings` | `NPDIWarning[]` | Safety alerts for 18 Incompatibilities (Populated in Prompt 2) |

### TypeScript Interfaces

- `Herb` — id, pinyin_name, common_name, english_name?, safety_tier, properties, actions, contraindications
- `HerbProperties` — temperature, flavor, meridians
- `Formula` — id, pinyin_name, common_name, primary_pattern, actions, architecture, safety_note
- `FormulaArchitectureItem` — role, herb_id, pinyin_name, purpose, dosage_percentage

### Getters (Computed)

- `getHerbById(herbId)` — returns `Herb | null`
- `searchHerbs(query)` — filters herbs by pinyin_name, common_name, or english_name (case-insensitive)

### Actions

- `addHerbToFormula(herb)` — adds herb if not already in `activeFormula`
- `removeHerbFromFormula(herbId)` — removes herb by id
- `clearFormula()` — resets `activeFormula` to empty array

## Usage

```ts
const alchemy = useAlchemyStore();
alchemy.addHerbToFormula(herb);
alchemy.removeHerbFromFormula("herb_001");
alchemy.clearFormula();
const herb = alchemy.getHerbById("herb_001");
const matches = alchemy.searchHerbs("ginseng");
```
