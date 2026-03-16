# P6: Meridian Visualizer

**Phase:** 1 — Alchemy Pillar (Advanced UI)  
**Prompt:** 6

---

## 1. Files Created / Modified

| Action | Path |
|--------|------|
| Created | `src/components/alchemy/MeridianVisualizer.vue` |
| Created | `docs/architecture/phase_1/P6_MeridianVisualizer.md` |

---

## 2. Architecture: Pure SVG

The visualizer uses a **100% pure SVG** container. No HTML `<div>` elements are used for nodes—eliminating DOM vs. SVG coordinate drift and ensuring mathematically precise, responsive layout.

- **Container:** Single `<svg viewBox="0 0 100 100" class="w-full h-full">`
- **Pentagon outline:** `<polygon>` with `stroke="currentColor"` and low opacity
- **Element nodes:** Each of the Five Elements is rendered as an SVG `<g>` group at its calculated vertex, containing:
  - `<circle r="12">` with element-specific fill (Tailwind `fill-*` utilities)
  - `<text>` with `text-anchor="middle"` and `dominant-baseline="central"` for centered labels
  - `<title>` for meridian tooltip on hover

---

## 3. State Variables Accessed

| Store | Variable | Usage |
|-------|----------|-------|
| alchemy | `activeFormula` | Read — source herbs for meridian extraction |

**No mutations** — component is read-only.

---

## 4. One-Sentence Summary for AI CTO

MeridianVisualizer displays a pure-SVG pentagonal Wu Xing (Five Elements) network that deduplicates meridians from the active formula, maps them to Wood/Fire/Earth/Metal/Water, and highlights elements with targeted meridians (opacity + glow) while providing meridian names via tooltip.

---

## 5. Core Logic / Math

- **Meridian extraction:** Parse `properties.meridians`; split on comma/semicolon; strip "principally"; skip "All 12 Meridians"; deduplicate
- **Element mapping:** Wood (Liver, Gallbladder), Fire (Heart, SI, Pericardium, San Jiao, Triple Burner), Earth (Spleen, Stomach), Metal (Lung, LI), Water (Kidney, Bladder)
- **Reactivity:** `activeMeridians` → `meridiansByElement`; element is "lit" if any of its meridians appear in `activeMeridians`; active nodes get `opacity-100` + glow, inactive get `opacity-40`
- **Pentagon geometry:** Center (50, 50), radius 38, start angle -90° (top), step 72°. Vertices: `(cx + r·cos(θ), cy + r·sin(θ))` for θ = -90°, -18°, 54°, 126°, 198°
