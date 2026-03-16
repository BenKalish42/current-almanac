# Task 11.4 - Multi-Formula Cauldron Bridge

## Objective

Connect the Formula Library to the Cauldron so users can:

- load a classical blueprint or market variant into the Cauldron,
- replace the current Cauldron or combine with it,
- merge duplicate herbs by dosage,
- preserve shadow-node ingredients for safety calculations while masking identity in UI.

## Store Changes (`src/stores/alchemyStore.ts`)

### New action: `loadFormulaIntoCauldron(ingredientsArray, append = false)`

Behavior:

- `append = false`
  - clears current Cauldron state, then loads selected formula ingredients.
- `append = true`
  - keeps current Cauldron contents and merges incoming ingredients.

### Dosage merge logic

Added `herbDosages: Record<string, number>` to track cumulative dosage per `herb_id`.

On load:

- incoming ingredient dosage is normalized from:
  - `exact_dosage_grams`, or
  - `classical_dosage_ratio`, or
  - `dosage` fallback.
- if herb already exists in Cauldron:
  - `nextDosage = existingDosage + incomingDosage`
- if herb does not exist:
  - herb is added once to `activeFormula`
  - dosage map initialized with incoming amount.

This supports multi-formula stacking, e.g. `5g + 10g = 15g`.

## Shadow Node Handling

Shadow ingredients are kept in state for safety/collision math:

- any `herb_id` containing `"shadow"` is still loaded into `activeFormula` and `herbDosages`.
- unresolved/shadow IDs are materialized as fallback herb objects.

UI masking rules:

- display name is forced to `Proprietary Ingredient` for shadow IDs.
- specific botanical identity is not exposed in rendered herb labels.

## Formula Library UI Changes (`src/components/alchemy/FormulaLibrary.vue`)

### New load controls

- Added **Load to Cauldron** on:
  - each classical formula header,
  - each market variant row.

### Replace vs combine prompt

When Cauldron is non-empty, clicking load opens a lightweight modal:

- `Replace Cauldron` -> `append = false`
- `Combine Formulas` -> `append = true`

When Cauldron is empty, load executes immediately with replace semantics.

## Cauldron Rendering Notes

`src/components/alchemy/HerbInventoryManager.vue` now renders:

- cumulative dosage beside each active herb (`getHerbDosage(herb.id)`),
- shadow herbs as `Proprietary Ingredient`.

`src/components/alchemy/FormulaHierarchy.vue` also masks shadow herb labels to preserve legal constraints across role-assignment views.
