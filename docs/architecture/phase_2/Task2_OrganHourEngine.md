# Task 2: Organ Hour Engine (TCM Shichen)

**Phase:** 2 — Astrology Pillar (Temporal Diagnostics)  
**Task:** 2

---

## 1. Files Created / Modified

| Action | Path |
|--------|------|
| Created | `src/data/organClock.ts` — 12 Shichen mappings, getCurrentOrganHour utility |
| Created | `src/components/astrology/OrganHourCard.vue` — TCM Organ Hour display card |
| Modified | `src/views/HomeView.vue` — mounted OrganHourCard below Location Sync indicator |
| Created | `docs/architecture/phase_2/Task2_OrganHourEngine.md` |

---

## 2. State Variables Accessed

| Store | Variable | Usage |
|-------|----------|-------|
| app | `presentDatetimeLocal` | Read — extracts hour for getCurrentOrganHour |

**No mutations** — component is read-only.

---

## 3. One-Sentence Summary for AI CTO

OrganHourCard visualizes the active TCM organ for the current Shichen (two-hour block) using appStore time, displaying physiological and Neidan/spirit descriptions with Wu Xing–themed styling.

---

## 4. Core Logic

- **organClock.ts:** 12 entries (Zi 子 → Hai 亥) mapping branch, start/end hour, organ, physiological text, neidanSpirit, wuXing; `getCurrentOrganHour(hour24)` returns the active entry (handles Zi 23–01 wrap)
- **OrganHourCard.vue:** Derives hour from `presentDatetimeLocal`; header shows branch (Hanzi + pinyin), time block (e.g. 11:00–13:00), organ name; body has two-column layout (Physiological State, Neidan/Spirit); gradient/border themed by Wu Xing (Wood=emerald, Fire=orange/red, Earth=amber, Metal=slate, Water=blue)
- **HomeView:** OrganHourCard mounted in side panel below Location Sync, before Advanced Settings
