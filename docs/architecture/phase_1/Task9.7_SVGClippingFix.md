# Task 9.7: SVG Clipping Fix

**Phase:** 1 — Alchemy Pillar (UI Polish)  
**Task:** 9.7

---

## 1. Files Created / Modified

| Action | Path |
|--------|------|
| Modified | `src/components/alchemy/MeridianVisualizer.vue` |
| Created | `docs/architecture/phase_1/Task9.7_SVGClippingFix.md` |

---

## 2. Fix Summary

The drop-shadow/glow effects on the Wu Xing element nodes (especially Fire at the top) were being clipped by the SVG bounding box. The viewBox was expanded to add mathematical padding so the glow can render without clipping.

---

## 3. Changes

- **ViewBox expansion:** `viewBox="0 0 100 100"` → `viewBox="-15 -15 130 130"` — adds 15 units of padding on all sides; vertex coordinates (center 50,50, radius 38) unchanged
- **Overflow:** Added `overflow-visible` to the SVG element for browser-compatibility insurance

---

## 4. One-Sentence Summary for AI CTO

MeridianVisualizer SVG viewBox was expanded from `0 0 100 100` to `-15 -15 130 130` so drop-shadow/glow on active nodes no longer clips at the edges.
