# Task 11.7 - Exploded Hexagram Polish & Line Schema

## Scope

Polish the Exploded Hexagram SVG geometry (bracket orientation, text spacing) and introduce the TypeScript schema for the Line Analysis data payload.

## SVG Geometry Fixes (HexagramModal.vue)

### Left-Flank Brackets

- **Before**: Paths `M22 22h6v40h-6` drew outward-facing brackets `]` (vertical on right, opening left).
- **After**: Paths reversed to draw inward-facing brackets `[`:
  - Upper: `M 22 22 v 40 M 22 22 h 5 M 22 62 h 5` — vertical on left, serifs extending right.
  - Lower: `M 22 72 v 40 M 22 72 h 5 M 22 112 h 5`.

### Trigram Text (Left Flank)

- **Before**: `x="2"` — text could overlap bracket when long (e.g. "Sun (Wind/Wood)").
- **After**: `x="18"` with `text-anchor="end"` so text ends before the bracket at x=22, avoiding collision.

### Line Labels (Right Flank)

- **Before**: `x="170"` — sat close to hexagram rects (ending ~156).
- **After**: `x="188"` so labels sit cleanly away from the hexagram lines.

## Line Analysis Schema (schema_yijing.ts)

```ts
export interface YaoLineAnalysis {
  hexagramId: number;   // 1–64
  lineNumber: number;   // 1–6
  daoism: string;
  confucianism: string;
  buddhism: string;
  psychology: string;
  humandesign: string;
  genekeys: string;
}
```

- Prepares the structure for 64 × 6 = 384 Yao entries.
- Each entry holds six philosophy-specific analysis strings.
- Modal will consume this schema when the Line Analysis data payload is wired.

## Modal Integration Prep

- `activeLinePhilosophy` defaults to `'daoism'`.
- Line Analysis tabs bind `tab.key` (daoism, confucianism, etc.) to `PhilosophyIcon` `system` prop.
- Placeholder text: "Select a philosophy to view analysis for Line X."
