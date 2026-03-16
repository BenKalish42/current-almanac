# Phase 1 — JingBattery Component

**Purpose:** Handoff to Gemini AI CTO for architecture continuity.

---

## Summary

Created a new Vue 3 component for visualizing Yin Jing and Yang Jing reserves—a gamified, dual-bar indicator for systemic depletion in the Alchemy pillar.

## Deliverables

| Item | Location |
|------|----------|
| JingBattery component | `src/components/alchemy/JingBattery.vue` |

## Implementation Details

### Props
- `yinLevel` (0–100, default 50)
- `yangLevel` (0–100, default 50)

### UI
- **Layout:** Side-by-side dual horizontal bars
- **Yin:** Cool gradient (teal → cyan)
- **Yang:** Warm gradient (amber)
- Uses design tokens: `daoist-surface`, `daoist-charcoal`, `daoist-muted`

### Reactive Behavior
- Computed `width` styles from prop percentages
- **Critical state:** Bars pulse (`animate-pulse`) when level < 20%
- Labels: "Yin Jing" / "Yang Jing" plus percentage display

### Usage
```vue
<JingBattery :yin-level="65" :yang-level="42" />
```

---

## Notes for CTO
- Component is standalone (no store dependency)
- Ready for integration into AlchemyView or related screens
- Future: consider wiring to real Jing/state data when available
