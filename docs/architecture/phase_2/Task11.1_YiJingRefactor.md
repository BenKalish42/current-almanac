# Task 11.1 - Yi Jing Modal Refactor

## Scope

Refactor the hexagram modal UI and logic for:

- typographic clarity (remove em-dash ambiguity),
- dialect-driven pronunciation rendering,
- pure SVG hexagram drawing from binary state.

Primary implementation lives in `src/components/HexagramModal.vue`, with dialect preference state in `src/stores/appStore.ts` and a selector in `src/views/HomeView.vue`.

## Typography Changes

- Replaced dash-separated title formatting with a structural separator:
  - `Hexagram #<num> • <traditional-name>`
- Removed em-dashes from the title area to avoid visual confusion with the horizontal line shape associated with Yi Jing line notation and the character `一`.

## Linguistic Mapping

## Dialect Source

- `useAppStore()` now provides `preferredDialect` with values:
  - `mandarin`
  - `cantonese`
  - `taiwanese`
- Value persists through existing user-state local storage serialization.

## Modal Linguistic Resolver

`getHexagramLinguistics(hexagram)` resolves pronunciation based on `preferredDialect`:

- `mandarin`: uses `seed_hexagrams.json` `pinyin_name`.
- `cantonese`: transliterates the Traditional hexagram name via per-character Jyutping map.
- `taiwanese`: transliterates the Traditional hexagram name via per-character Hokkien map.
- Fallback behavior for missing data: use Mandarin pinyin if available, otherwise `"Pronunciation pending"`.

## Traditional Character Canon

- Added an internal Traditional-name list (`HEX_NAME_TRAD`) indexed by King Wen number (1-64).
- This ensures the modal always displays a Traditional Chinese form independent of upstream short-name simplifications.

## SVG Hexagram Drawer

## Data Flow

1. Modal receives `hexNum`.
2. `getHexBinary(hexNum)` returns a 6-bit string in **top -> bottom** order.
3. Logic reverses this into **bottom -> top** for correct line ordering in Yi Jing drawing order.
4. `hexagramLines` computed property outputs six line definitions:
   - `isYang: true` for bit `1` (solid),
   - `isYang: false` for bit `0` (broken),
   - `y` coordinate for each line.

## SVG Rendering Rules

- `viewBox="0 0 100 120"`, with utility sizing classes (`w-16 h-20 mx-auto`).
- Yang (`1`): one continuous `<rect>` across width.
- Yin (`0`): two `<rect>` segments with a center gap.
- Lines are drawn using `fill-current` and host color utilities:
  - `text-slate-800`
  - `dark:text-slate-200`

This keeps output crisp and theme-compatible without raster assets.

## Why This Structure

- Keeps line geometry deterministic and portable.
- Separates semantic state (`hexNum` -> binary -> line model) from presentation (SVG).
- Enables future moving-line overlays (e.g., changing lines) by extending the same line model.
