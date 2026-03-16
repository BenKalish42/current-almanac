# Phase 1 — Prompt 3: Alchemy Pillar (Herb Management)

**Handoff for Gemini AI CTO**

---

## Summary

Search UI for querying the local herb JSON data and managing the user’s active formula.

## Deliverable

- **File:** `src/components/alchemy/HerbInventoryManager.vue`

## Implementation

### State Integration

- Uses `useAlchemyStore` for search, active formula, and add/remove actions.

### Search Input

- Tailwind-styled input with search icon (inline SVG)
- `focus-within:border-daoist-jade/50`
- Placeholder: "Search herbs by pinyin or name..."

### Debounce (300ms)

- `searchInput` ref for raw query
- Watcher updates `debouncedQuery` after 300ms
- `searchResults` = `alchemyStore.searchHerbs(debouncedQuery)`

### Results Dropdown

- Absolutely positioned below the input
- Max height 240px with `overflow-y-auto`
- **Primary:** `pinyin_name`
- **Secondary:** `common_name` (and optional `hanzi_name` when present)
- Transition for open/close

### Actionable Items

- `@mousedown.prevent` on each result so selection runs before blur
- On select: `addHerbToFormula(herb)`, clears search, closes dropdown

### Active Formula List

- Lists `alchemyStore.activeFormula`
- Header with count
- X button per herb → `removeHerbFromFormula(herb.id)`
- Shows pinyin and common name per herb

### No-Results State

- Shows "No herbs found for ..." when the query returns no matches

## Usage

```vue
<template>
  <HerbInventoryManager />
</template>

<script setup>
import HerbInventoryManager from "@/components/alchemy/HerbInventoryManager.vue";
</script>
```

## Future Enhancement

- Optional `hanzi_name` is supported on herbs and will render when present in the data.
