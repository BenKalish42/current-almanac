# Phase 1 — Prompt 4: Formula Hierarchy (Educational Scaffolding)

**Handoff for AI CTO**

---

## What Was Built

A Vue 3 component that visually breaks down the structural hierarchy of a classical TCM formula using the **Jun (King), Chen (Minister), Zuo (Assistant), and Shi (Courier)** framework.

---

## Deliverables

### 1. `src/components/alchemy/FormulaHierarchy.vue`

- **State:** Uses `useAlchemyStore`; computes `herbsByTier` by grouping `activeFormula` by role via `herbRoles`
- **UI:** Vertical hierarchy with 5 tiers: King (Jun), Minister (Chen), Assistant (Zuo), Envoy (Shi), Unassigned
- **Theming:** King = bold, gold/amber accent; each tier steps down to lighter Courier styling
- **Tooltips:** Info icon (SVG) next to each tier; tooltip explains Daoist role
- **Role assignment:** Select dropdown per herb to assign/reassign tier (or Unassigned)
- **Empty state:** Shows "No herbs in formula" when `activeFormula` is empty; shows "—" for tiers with no herbs

### 2. `src/stores/alchemyStore.ts` (modified)

- **herbRoles:** `ref<Record<string, string>>({})` — maps herbId → role
- **setHerbRole(herbId, role | null):** set or clear role
- **removeHerbFromFormula / clearFormula:** also remove affected entries from `herbRoles`

---

## State Variables Used

| Variable | Purpose |
|----------|---------|
| `activeFormula` | Herbs in the current custom formula |
| `herbRoles` | Role (King/Minister/Assistant/Envoy) per herb |

---

## Integration Notes

- Component is a presentational hierarchy; it does not add or remove herbs.
- Role assignment is via dropdown on each herb; values are stored in `herbRoles`.
- Herbs without a role appear in **Unassigned**.
- Tooltips use `group-hover` / `group-focus-within` (works for hover and keyboard focus).
