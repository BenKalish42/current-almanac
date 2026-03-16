# Phase 1 — Prompt 5: Heuristic Formula Rater

**Domain:** Alchemy Pillar (Clinical Diagnostics)  
**Purpose:** Handoff summary for Gemini AI CTO

---

## What Was Built

A mathematical utility and Pinia integration for assigning an aggregate **Jing–Qi–Shen** cultivation rating to a user's actively built formula based on herb properties and role hierarchy.

### 1. `src/utils/heuristicRater.ts`

**Export:** `calculateFormulaRating(activeFormula: Herb[], herbRoles: Record<string, string>)`

**Returns:**
```ts
{
  jingScore: number;   // 0–100
  qiScore: number;     // 0–100
  shenScore: number;  // 0–100
  primaryEffect: string; // e.g. "Primary Qi Tonic", "Balanced Cultivation"
}
```

**Heuristic logic:**
- Loops through herbs, scores each on Jing / Qi / Shen using keywords in `actions`, `properties.flavor`, `properties.meridians`, `properties.temperature`
- **Qi:** "Qi", "Tonifies Primal Qi", Spleen/Lung/Stomach, Sweet + Warm
- **Shen:** "Shen", "Spirit", "Heart", "calms"
- **Jing:** "Jing", "Essence", "Blood", "Kidney", "Marrow", "nourishes"
- **Role multipliers:** King (Jun) 2.0, Minister (Chen) 1.5, Assistant (Zuo) 1.0, Envoy (Shi) 0.5, Unassigned 1.0
- Final scores normalized/capped to 0–100; `primaryEffect` derived from the highest score (or "Balanced Cultivation" if tied, "No Clear Signature" if all 0)

### 2. `src/stores/alchemyStore.ts`

**New computed:** `formulaCultivationRating`
- Runs `activeFormula` and `herbRoles` through `calculateFormulaRating`
- Reactive — updates when herbs or roles change

---

## Files Touched

| File | Change |
|------|--------|
| `src/utils/heuristicRater.ts` | Created |
| `src/stores/alchemyStore.ts` | Added import, `formulaCultivationRating` computed, export in return |
| `docs/architecture/phase_1/P5_HeuristicRater.md` | Created |
| `docs/handoff/Phase1-Prompt5.md` | Created |

---

## Usage

```ts
const alchemy = useAlchemyStore();

// Reactive rating based on active formula + roles
const rating = alchemy.formulaCultivationRating;
// rating.jingScore, rating.qiScore, rating.shenScore, rating.primaryEffect
```
