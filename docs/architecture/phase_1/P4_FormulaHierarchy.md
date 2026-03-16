# P4: Formula Hierarchy Component

**Phase:** 1 — Alchemy Pillar (Educational Scaffolding)  
**Prompt:** 4

---

## 1. Files Created / Modified

| Action | Path |
|--------|------|
| Created | `src/components/alchemy/FormulaHierarchy.vue` |
| Modified | `src/stores/alchemyStore.ts` |
| Created | `docs/architecture/phase_1/P4_FormulaHierarchy.md` |

**alchemyStore changes:**
- Added `herbRoles: ref<Record<string, string>>({})` — maps herbId → role (e.g. `"King (Jun)"`)
- Added `setHerbRole(herbId, role | null)` — set or clear role
- `removeHerbFromFormula` and `clearFormula` now also clear role data for affected herbs

---

## 2. State Variables Accessed

| Store | Variable | Usage |
|-------|----------|-------|
| alchemy | `activeFormula` | Source herbs for hierarchy |
| alchemy | `herbRoles` | Role assignment per herb (herbId → role string) |

**Actions called:**
- `setHerbRole(herbId, role)` — when user assigns/reassigns a tier via the select dropdown

---

## 3. One-Sentence Summary for AI CTO

FormulaHierarchy displays `activeFormula` grouped by Jun–Chen–Zuo–Shi role (King, Minister, Assistant, Envoy) with tier-specific styling, info tooltips, and role-assignment selects; it uses `herbRoles` in the alchemy store for custom formula role mapping.

---

## 4. Core Logic / Math

- Groups herbs by role from `herbRoles` (King, Minister, Assistant, Envoy); unassigned herbs go to "Unassigned"
- Tier order: King → Minister → Assistant → Envoy → Unassigned
- Role-based styling: King (bold, amber), Minister (amber), Assistant (neutral), Envoy (muted), Unassigned (dashed, italic)
- Role dropdown maps herbId → canonical role string via `setHerbRole()`
