# Task 11.8 - Synergy & Collision Engine

## Objective

Analyze multi-formula Cauldron blends for directional coherence and internal conflicts:

- overall vector tendency (lifting/sinking, warming/cooling),
- synergy corridors (flows),
- traffic jams and collisions (vector opposition).

## Intelligence Service Update

File: `src/services/intelligenceService.ts`

### New function

- `analyzeCauldronSynergy(activeFormula, herbDosages)`

### API behavior

- Uses `VITE_LLM_API_URL` (fallback OpenAI chat completions URL).
- Sends OpenAI-compatible payload:
  - `model`
  - `messages` (`system`, `user`)
  - `max_tokens`
  - `temperature`
- Requires `VITE_LLM_API_KEY`.

### System prompt contract

The system prompt explicitly instructs the model to return strict Markdown with:

1. `OVERALL VECTOR`
2. `SYNERGIES & FLOWS`
3. `TRAFFIC JAMS & COLLISIONS`

The user payload is a JSON block containing the combined herb list, cumulative dosages, and basic properties/actions.

## Store Update

File: `src/stores/alchemyStore.ts`

### New state

- `isAnalyzingSynergy: boolean`
- `synergyReport: string`

### New action

- `analyzeCombinedVectors()`
  - guards for minimum payload (`< 2 herbs` short-circuit message),
  - toggles loading state,
  - calls `analyzeCauldronSynergy(activeFormula, herbDosages)`,
  - maps response into `synergyReport`,
  - maps API/runtime failures to a user-visible error string.

`clearFormula()` also resets `synergyReport` to avoid stale analysis after full replacement.

## Cauldron UI Update

File: `src/components/alchemy/HerbInventoryManager.vue`

### Added controls

- Primary action button: `Analyze Combined Vectors`
  - disabled when Cauldron has fewer than 2 herbs,
  - loading label: `Architecting vectors...`.

### Report rendering

- Added expandable `<details>` section:
  - title: `Synergy & Collision Report`
  - body renders markdown text output with preserved line breaks.

This keeps analysis inline with the Cauldron workflow while allowing repeated formula-stacking tests.
