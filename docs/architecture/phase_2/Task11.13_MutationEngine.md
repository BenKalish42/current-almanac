# Task 11.13 - Mutation Engine & Hexagram Modal Polish

## Scope

Introduce the "Mutation Engine" for Changing Lines (Moving Yao), supporting time-based hexagrams and future coin-casting. Moving lines are visually highlighted, auto-open their analysis, and provide a bridge to view the Transformed (Relating) Hexagram.

## Header & Typographic Polish

- **Removed parentheses** around the English name in the modal header.
- **English name styling**: `text-xl font-bold` to balance the Hanzi. Format: `HEXAGRAM #n • Hanzi • English Name`.
- Bullet separator: `•` (no parentheses around English).

## SVG Sacred Geometry Fix

- **BaGua labels** (e.g. "Sun (Wind/Wood)"): Standardized Y-axis alignment using `alignment-baseline="middle"`.
- **y coordinate**: Set to the vertical midpoint of each bracket:
  - Upper: `(upperBracketBounds.top - EXPLODE_OFFSET + upperBracketBounds.bottom - EXPLODE_OFFSET) / 2`
  - Lower: `(lowerBracketBounds.top + EXPLODE_OFFSET + lowerBracketBounds.bottom + EXPLODE_OFFSET) / 2`

## Mutation Engine

### State & Math

- **movingLines prop**: `number[]` (1–6). Example: `[2]` = Line 2 is mutating.
- **relatingHexagramId computed**: Uses `getRelatingHexagram(hexId, movingLines)` from `@/core/iching`.

### Bit-Flipping Math

Binary is stored **top→bottom** (Line 6 = index 0, Line 1 = index 5). For each line in `movingLines`:

- `idx = 6 - lineNum` (Line 1 → index 5, Line 6 → index 0)
- Flip bit: `arr[idx] = arr[idx] === "1" ? "0" : "1"`
- Look up new hex ID from `BINARY_TO_HEX` map.

`getRelatingHexagram(hexId, movingLines)` returns the transformed hexagram ID or `hexId` if no moving lines.

### Visual Highlight

- Lines in `movingLines` get class `lineMutating`.
- CSS: `stroke: rgb(251 191 36)`, `stroke-width: 2`, `filter: drop-shadow(0 0 6px rgba(251, 191, 36, 0.7))`.
- Applied via `.lineMutating :deep(rect)` when the parent `<g>` has the class, or directly on `<rect>` when appropriate.

### Mutation Bridge (UI)

- In the Line Analysis block, when `activeLine` is in `movingLines` and `relatingHexagramId` exists:
  - Renders button: **View Transformed Hexagram**.
  - Styling: `mutationBridgeBtn` (amber gradient, prominent).
- **Click handler**: Emits `viewHexagram` with `relatingHexagramId`.
- **Parent (HomeView)**: Handles `@view-hexagram` by setting `selectedHexNum = id` and clearing `movingLines` for the new view.

## Auto-Open and Data Flow

- Clicking a line opens its analysis (sets `activeLine`).
- When a moving line is clicked, the View Transformed Hexagram button appears.
- Future: `openHexModal` can receive `movingLines` from temporal hex data (`store.temporalHex.*.hex.movingLines`).

## Files Modified

- `src/core/iching.ts` — `getRelatingHexagram`, `getHexFromBinary`, `BINARY_TO_HEX` lookup.
- `src/components/HexagramModal.vue` — Header typography, BaGua label alignment, `movingLines` prop, `relatingHexagramId`, moving-line highlight, Mutation Bridge button.
- `src/views/HomeView.vue` — `selectedMovingLines`, `onViewHexagram`, `openHexModal` accepts `movingLines`.
