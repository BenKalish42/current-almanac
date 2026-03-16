# Phase 1 — Prompt 2: NPDI (18 Incompatibilities) Implementation

**Handoff for Gemini AI CTO**

---

## Summary

Implemented TCM 18 Incompatibilities (Shi Ba Fan) and 19 Antagonisms (Xiang Wu) checks in the alchemy store. Warnings are computed whenever the active formula changes.

## Deliverables

- **File:** `src/data/npdi.ts` — NPDI logic and data
- **Updates:** `src/stores/alchemyStore.ts` — integration and `runNPDICheck()`

## Implementation

### NPDI Data Module (`src/data/npdi.ts`)

**Canonical Groups:** Maps pinyin variants to canonical keys for matching:

- **Gan Cao (Licorice):** Gan Cao, Zhi Gan Cao, Sheng Gan Cao
- **Wu Tou (Aconite):** Fu Zi, Chuan Wu, Cao Wu
- **Ban Xia (Pinellia):** Ban Xia, Zhi Ban Xia, Sheng Ban Xia
- Plus Li Lu, Rou Gui, Chi Shi Zhi, Wu Ling Zhi, etc.

**Incompatible Pairs (18 Incompatibilities + 19 Antagonisms):**

- Gan Cao ↔ Gan Sui, Da Ji, Hai Zao, Yuan Hua
- Wu Tou ↔ Ban Xia, Bai Lian, Bai Ji, Tian Hua Fen, Gua Lou, Chuan/Zhe Bei Mu
- Li Lu ↔ Ren Shen, Bei/Nan Sha Shen, Ku Shen, Dan Shen, Xuan Shen, Bai Shao, Chi Shao, Xi Xin
- Rou Gui ↔ Chi Shi Zhi
- Ren Shen ↔ Wu Ling Zhi

**API:**

- `checkNPDI(herbs)` — returns `NPDIWarning[]` for incompatible pairs in the given herb array
- `NPDIWarning` — `{ herbA, herbB, message }`

### Alchemy Store Integration

- `npdiWarnings` typed as `NPDIWarning[]` (was `unknown[]`)
- `runNPDICheck()` — calls `checkNPDI(activeFormula)` and updates `npdiWarnings`
- `runNPDICheck()` invoked after `addHerbToFormula`, `removeHerbFromFormula`, and `clearFormula`

## Usage

```ts
const alchemy = useAlchemyStore();
alchemy.addHerbToFormula(someHerb);
if (alchemy.npdiWarnings.length > 0) {
  alchemy.npdiWarnings.forEach((w) => console.warn(w.message));
}
```

**Note:** With the current 25 seed herbs, no NPDI pairs exist; warnings will appear once herbs such as Chi Shi Zhi, Fu Zi, or Li Lu are added.
