# Task 3: BaZi Engine (Four Pillars Display)

**Phase:** 2 — Astrology Pillar (Temporal Diagnostics)  
**Task:** 3

---

## 1. Files Created / Modified

| Action | Path |
|--------|------|
| Created | `src/components/astrology/FourPillarsCard.vue` — 4-column BaZi pillar display with Wu Xing theming |
| Modified | `src/views/HomeView.vue` — mounted FourPillarsCard above OrganHourCard in side panel |
| Created | `docs/architecture/phase_2/Task3_BaZiEngine.md` |

---

## 2. State Variables Accessed

| Store | Variable | Usage |
|-------|----------|-------|
| astrology | `fourPillars` | Read — Year/Month/Day/Hour pillars (stem + branch hanzi, pinyin, wuXing) |
| app (via astrology) | `selectedDate` | Read — astrologyStore derives fourPillars from appStore.selectedDate |

**No mutations** — component is read-only.

---

## 3. One-Sentence Summary for AI CTO

FourPillarsCard displays the current moment’s BaZi Four Pillars (Year, Month, Day, Hour) as a 4-column grid with Heavenly Stem and Earthly Branch tiles per pillar, each themed by Wu Xing (Wood=emerald, Fire=red/orange, Earth=amber, Metal=slate, Water=blue).

---

## 4. Core Logic

- **astrologyStore.fourPillars:** Computed from `appStore.selectedDate`; uses Lunar.js to get year/month/day/hour gan-zhi; parsed via `parseGanZhi`; returns `BaZiPillar[]` with stem/branch `{ hanzi, pinyin, wuXing }`
- **FourPillarsCard.vue:** Imports `useAstrologyStore`; 4-column grid (Year, Month, Day, Hour) left-to-right; each column: label, top tile (Heavenly Stem hanzi + pinyin), bottom tile (Earthly Branch hanzi + pinyin); tiles use CSS classes keyed by `wuXing` for border/text color
- **HomeView:** FourPillarsCard mounted in side panel after controls div, before OrganHourCard, before advanced-settings
