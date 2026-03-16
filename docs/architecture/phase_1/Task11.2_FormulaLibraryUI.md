# Task 11.2 - Formula Library UI (Phase 1.5 Alchemy Pillar)

## Objective

Create a Formula Library UI that:

- browses classical formula blueprints,
- compares market-brand variants under each blueprint,
- enforces strict shadow node masking for legally sensitive ingredients.

## Store Creation

File: `src/stores/formulaStore.ts`

### Data source

- Imports `src/data/formulas.json`.
- Types are enforced using `src/data/schema_formulas.ts`.

### Exposed state/getters

- `classicalFormulas`
- `marketVariants`
- `formulaIngredients`

### Helper methods

- `getVariantsForFormula(formulaId)`  
  Returns all market variants linked to the selected classical formula.
- `getIngredientsForFormula(formulaId)`  
  Returns canonical ingredient edges for the selected classical formula.

## UI Component

File: `src/components/alchemy/FormulaLibrary.vue`

### Structure

- Search input (Hanzi, Pinyin, source text, description).
- Accordion-style list (`details/summary`) per classical formula.
- Top-level node display includes:
  - Hanzi
  - Pinyin
  - source text
  - Cantonese/Taiwanese linguistics
- Expanded view includes:
  - Classical ingredient ratio list (role + canonical ratio)
  - Market variants section (brand-level physical products and dosages)

### Integration

File: `src/views/AlchemyView.vue`

- Added tab switch between:
  - `Cauldron` (existing builder tools)
  - `Formula Library` (new browse/compare UI)
- Mounts `<FormulaLibrary />` when `Formula Library` tab is active.

## Shadow Node Rendering Protocol

The shadow node protocol is enforced directly in variant rendering:

1. For each `MarketVariant`, check `has_shadow_nodes`.
2. If true, show badge text:
   - `Contains Proprietary/Restricted Blend.`
3. Render ingredient list with explicit filtering:
   - include only ingredients where `herb_id` does **not** contain `"shadow"`.
4. Do not display hidden node names or dosages in UI.
5. Non-shadow ingredients remain fully visible so users can compare brand deviations.

This preserves legal/safety constraints while keeping dosage-comparison utility for visible ingredients.
