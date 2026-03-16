# Task 11.6 - Exploded Hexagram Architecture

## Scope

Refactored the active Yi Jing modal (`src/components/HexagramModal.vue`) to support an interactive "exploded" hexagram architecture diagram with:

- upper/lower trigram split animation,
- structural bracket annotations,
- Wu Xing color-coded trigram labels,
- clickable Yao lines (1-6),
- line-analysis scaffolding with philosophy tabs.

## State Added

- `isExploded: boolean` (default `false`)
  - desktop: toggled by diagram `mouseenter` / `mouseleave`
  - mobile: toggled by `Analyze Architecture` button
- `activeLine: number | null`
  - set by clicking any individual Yao line (1-6)
- `activeLinePhilosophy: 'daoism' | 'confucianism' | 'buddhism' | 'psychology' | 'humandesign' | 'genekeys'`
  - drives line-analysis tab selection

## SVG Group Animation

- The 6-line structure is split into two animated `<g>` groups:
  - **Upper Trigram**: lines 4-6
  - **Lower Trigram**: lines 1-3
- Animation classes:
  - upper group: `translate-y-[-16px]` when exploded
  - lower group: `translate-y-[16px]` when exploded
  - both include `transition-transform duration-500 ease-out`

## Left Flank Structural Brackets

- Two left-side bracket glyphs (`[`) are rendered via SVG paths.
- Brackets fade in with `transition-opacity duration-500` when `isExploded`.
- Trigram labels appear next to each bracket as:
  - `<Trigram Name> (<Element>)`

## Wu Xing Color Mapping

Trigram name to Tailwind color class:

- `Li` -> `text-red-500` (Fire)
- `Sun` -> `text-emerald-500` (Wood/Wind)
- `Zhen` -> `text-emerald-500` (Wood)
- `Kan` -> `text-blue-500` (Water)
- `Kun` -> `text-amber-500` (Earth)
- `Gen` -> `text-amber-500` (Earth)
- `Qian` -> `text-slate-300` (Metal)
- `Dui` -> `text-slate-300` (Metal)
- fallback -> `text-gray-400`

## Right Flank Interactive Lines

- Every Yao line is wrapped in an interactive `<g>`:
  - `cursor-pointer hover:opacity-75`
  - click sets `activeLine` to that line's number
- Line labels appear on the right in exploded mode with fade-in opacity:
  - `Line 6 (Top)` down to `Line 1 (Bottom)`

## Line Analysis Modal Scaffolding

- Conditional block below diagram: `v-if="activeLine"`.
- Contains tabbed philosophy selector using `PhilosophyIcon` for:
  - Daoism, Confucianism, Buddhism, Psychology, Human Design, Gene Keys.
- Placeholder analysis text is rendered from current `activeLine` and selected `activeLinePhilosophy`.
