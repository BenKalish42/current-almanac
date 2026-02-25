# QMDJ Verification Report (qimen.ts)

**Reference:** `src/core/qimen.ts` — Zhi Run (置润) rotating-plate Qi Men Dun Jia implementation.

---

## Rule 1: The Center Trap (中宮寄宮)

**Strict rule:** In Zhuan Pan QMDJ, any spirit landing in Palace 5 must be re-routed to Palace 2 (Kun).

**Current implementation:**
- `PALACE_RING = PALACE_ORDER.filter((p) => p !== 5)` → [4, 9, 2, 3, 7, 8, 1, 6]
- Spirits and Doors use `PALACE_RING` only — they are never assigned to Palace 5.
- Center is skipped by construction; nothing is explicitly “re-routed” to Kun.

**Status:** Compatible. We avoid Palace 5 for spirits/doors instead of assigning then re-routing; outcome is the same (no spirit in 5).

---

## Rule 2: Movement Paths

### 2a) Nine Stars — “Flying” logic (Luo Shu: 1→2→3→4→5→6→7→8→9)

**Current implementation:**
- Stars use `PALACE_ORDER = [4, 9, 2, 3, 5, 7, 8, 1, 6]` (Luo Shu layout).
- Stars are rotated over `PALACE_ORDER` via `rotateAssignments(PALACE_ORDER, starsSeq, hourStemPalace, dun)`.
- Flying direction follows `dun` (Yang forward, Yin backward).

**Status:** Aligned.

### 2b) Eight Gates — “Rotation” logic (1→8→3→4→9→2→7→6)

**Strict rule:** Gates use peripheral rotation order: 1→8→3→4→9→2→7→6.

**Current implementation:**
- Gates use `PALACE_RING = [4, 9, 2, 3, 7, 8, 1, 6]`.
- This is Luo Shu row-by-row reading order with center removed (4,9,2 | 3,_,7 | 8,1,6).

**Conflict:** The specified rotation order is **1→8→3→4→9→2→7→6** (Kan→Gen→Zhen→Xun→Li→Kun→Dui→Qian). Our order is **4→9→2→3→7→8→1→6**. These differ.

**Proposed fix:** Introduce a dedicated gate-rotation sequence, e.g.:
```ts
const GATE_ROTATION_ORDER: PalaceId[] = [1, 8, 3, 4, 9, 2, 7, 6];
```
and use it for doors (and possibly spirits) instead of `PALACE_RING`.

---

## Rule 3: Ju Calculation / Chai Bu / Run (置润) Logic

**Strict rule:** Chai Bu (Split-and-Patch) method is used for 15-day solar term ingress. When Fu Tou leads the term by ≥9 days at 芒种 or 大雪, an intercalary (闰局) adjustment is made: an extra Upper/Middle/Lower cycle is inserted before the next solstice.

**Current implementation:**
- `findNearestJiaJiToTerm()` correctly classifies chao_shen / jie_qi / zheng_shou.
- `zhiRunIntercalary = (termName === "芒种" || termName === "大雪") && status === "chao_shen" && leadDays >= 9`.
- `zhiRun.intercalary` is stored on the chart but never used to alter Ju or insert the Run cycle.

**Conflict:** Run logic is detected but not applied. When `zhiRunIntercalary` is true, the Ju selection and calendar alignment should be adjusted (extra Upper/Middle/Lower block inserted). We currently do not model this.

**Proposed fix:** When `zhiRunIntercalary` is true, adjust the effective term/Yuan/Ju to account for the inserted cycle (or extend the current term’s charts by one full 15-day block before switching Dun).

---

## Summary

| Rule                    | Status   | Notes                                                           |
|-------------------------|----------|-----------------------------------------------------------------|
| Center Trap (5 → 2)     | ✓ OK     | Implemented by excluding 5 from spirits/doors.                  |
| Stars — Flying (Luo Shu)| ✓ OK     | Uses Luo Shu `PALACE_ORDER` with dun direction.                 |
| Gates — Rotation order  | ⚠ Conflict | Our order 4,9,2,3,7,8,1,6 differs from 1→8→3→4→9→2→7→6.        |
| Ju / Chai Bu / Run      | ⚠ Conflict | Run condition computed but not applied to Ju/calendar logic.    |

---

## Recommendation

**STOP before Task 2.** Two items require clarification:

1. **Gate rotation sequence** — Confirm whether the 1→8→3→4→9→2→7→6 order should replace our current `PALACE_RING` for doors (and spirits).
2. **Run logic** — Confirm the exact rules for inserting the intercalary block (which Ju to reuse, how many days to extend, etc.) and how to wire `zhiRun.intercalary` into the Ju selection and date logic.

Once these are decided, the implementation can be updated and Tasks 2–4 can proceed.
