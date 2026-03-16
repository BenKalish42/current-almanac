# P5: Heuristic Formula Rater

**Phase:** 1 — Alchemy Pillar (Clinical Diagnostics)  
**Prompt:** 5

---

## 1. Files Created / Modified

| Action | Path |
|--------|------|
| Created | `src/utils/heuristicRater.ts` |
| Modified | `src/stores/alchemyStore.ts` |
| Created | `docs/architecture/phase_1/P5_HeuristicRater.md` |

**alchemyStore changes:**
- Import `calculateFormulaRating` from `@/utils/heuristicRater`
- Added `formulaCultivationRating` computed property that returns `{ jingScore, qiScore, shenScore, primaryEffect }`

---

## 2. State Variables Mutated / Accessed

| Store | Variable | Usage |
|-------|----------|-------|
| alchemy | `activeFormula` | Read — source herbs for rating |
| alchemy | `herbRoles` | Read — role multipliers per herb |

**No mutations** — `formulaCultivationRating` is a pure computed; the rater only reads `activeFormula` and `herbRoles`.

---

## 3. One-Sentence Summary for AI CTO

The heuristic rater scores an active formula on Jing, Qi, and Shen (0–100) by keyword-matching herb actions/properties, applies role multipliers (King 2×, Minister 1.5×, Assistant 1×, Envoy 0.5×), and returns a `primaryEffect` label; the alchemy store exposes this as `formulaCultivationRating`.

---

## 4. Core Logic / Math

- **Qi scoring:** `/\bqi\b/` or "tonifies Primal Qi" (+3); Spleen/Lung/Stomach (+2); Sweet + Warm (+1)
- **Shen scoring:** Shen/Spirit/Heart (+3); "calms Spirit" (+2); Heart meridian (+1)
- **Jing scoring:** Jing/Essence/Marrow/Kidney Yin (+3); Blood/nourishes (+2); Kidney (+1)
- **Role multipliers:** King 2.0, Minister 1.5, Assistant 1.0, Envoy 0.5, Unassigned 1.0
- **Normalization:** Scale raw scores so max = 100; `primaryEffect` = highest-score label, or "Balanced Cultivation" if tied
