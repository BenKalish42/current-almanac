# Astrology Architecture Audit

**Role:** Lead Frontend Engineer → AI CTO  
**Scope:** Legacy Astrology components on the `/astrology` route (HomeView)  
**Date:** Generated for handoff

---

## 1. Component Tree

### Exact Filenames Rendering Astrology UI

| Feature | Component(s) | Location |
|--------|--------------|----------|
| **Four Pillars (Present Moment)** | `FourPillarsCard.vue` | `src/components/astrology/FourPillarsCard.vue` |
| **Four Pillars (Birth) + Hexagrams (Past)** | Inline in HomeView | `src/views/HomeView.vue` — `section.panel` (Past/Birth), `.pillarGrid` with `.pillarBox` × 4 |
| **Four Pillars (Present) + Hexagrams (Present)** | Inline in HomeView | `src/views/HomeView.vue` — `section.panel` (Present/Moment), `.pillarGrid` with `.pillarBox` × 4 |
| **Hexagram lines (binary bars)** | `HexagramLines.vue` | `src/components/HexagramLines.vue` |
| **Hexagram modal (detail view)** | `HexagramModal.vue` | `src/components/HexagramModal.vue` |
| **User Intent form** | Inline in HomeView | `src/views/HomeView.vue` — "User Intent" section, `<label class="lbl">` with Domain + Goal Constraint inputs |
| **User State form** | Inline in HomeView | `src/views/HomeView.vue` — "User State (Optional)" section, Capacity / Load / Sleep Quality / Cognitive Noise / Social Load / Emotional Tone inputs |
| **Organ Hour (Shichen)** | `OrganHourCard.vue` | `src/components/astrology/OrganHourCard.vue` |
| **Past/Present datetime selectors** | Inline in HomeView | `section.panel` headers — birth `datetime-local`, present `datetime-local`, Auto On/Off, ◀ ▶ shift buttons |
| **CosmicBoard (Qimen)** | `CosmicBoard.vue` | `src/components/CosmicBoard.vue` — inside "Advanced" accordion |

### Child Dependencies

- **HexagramLines** — receives `binary` and `size` props; used inside each `.pillarHex` tile in Past and Present grids.
- **HexagramModal** — receives `open`, `hex-num`, `hex-name`, `summaries`; emits `close`. Opened when user clicks a pillar hex tile.

---

## 2. State & Props

### Data Sources by Component

| Component / Feature | Data Source | Type |
|---------------------|-------------|------|
| **FourPillarsCard** | `useAstrologyStore().fourPillars` | Pinia store (computed) |
| **OrganHourCard** | `useAppStore().presentDatetimeLocal` | Pinia store (computed) |
| **Past pillar grid + hexagrams** | `store.birthTemporalHex` | Pinia (appStore, computed) |
| **Present pillar grid + hexagrams** | `store.temporalHex` | Pinia (appStore, computed) |
| **HexagramModal** | Props: `hex-num`, `hex-name`, `summaries` | Props from HomeView local state |
| **User Intent** | `store.intentDomain`, `store.intentGoalConstraint` | Pinia (appStore refs), `v-model` |
| **User State** | `store.userCapacity`, `store.userLoad`, `store.userSleepQuality`, `store.userCognitiveNoise`, `store.userSocialLoad`, `store.userEmotionalTone` | Pinia (appStore refs), `v-model.number` / `v-model` |
| **Birth datetime, sect** | `store.birthDatetimeLocal`, `store.birthSect` | Pinia (appStore refs), `v-model` |
| **Present datetime** | `store.presentDatetimeLocal` | Pinia (appStore computed getter/setter) |
| **CosmicBoard** | Props: `qimen-chart-hour`, `qimen-chart-day`, `selected-date` | Props from `store.qimenChartHour`, `store.qimenChartDay`, `store.selectedDate` |

### Local State (HomeView)

- `advancedExpanded` — Advanced accordion (CosmicBoard) open/closed
- `advancedSettingsExpanded` — Advanced Settings accordion (location override) open/closed
- `isHexModalOpen` — Hexagram modal visibility
- `selectedHexNum`, `selectedHexNameCn` — Which hexagram is shown in modal
- `selectedHexSummary` — Computed from `hexSummaryMap` and `selectedHexNum`
- `hexSummaryMap` — Built from `seedHexagrams.json` at module init (static)

**No hardcoded props** for the main BaZi/hexagram display; all values come from stores or local refs.

---

## 3. The Lunar Math — Time Source

### Is BaZi Using Reactive Geolocation Time?

**Yes.** All BaZi-related components use the reactive present moment from `appStore`.

| Component / Computed | Time Source | Reactive? |
|---------------------|-------------|-----------|
| **astrologyStore.fourPillars** | `appStore.selectedDate` | ✅ Yes |
| **OrganHourCard** | `store.presentDatetimeLocal` → parses hour | ✅ Yes |
| **temporalHex** (Present pillars + hexagrams) | `getTemporalXkdg(selectedDate.value)` | ✅ Yes |
| **birthTemporalHex** (Past pillars + hexagrams) | `getTemporalXkdg(birthInputToDate(birthProfile.input))` | ✅ Yes (from birth datetime) |
| **presentOrgan** | `selectedDate.value.getHours()` | ✅ Yes |
| **qimenChartHour / qimenChartDay** | `selectedDate.value` | ✅ Yes |

### Where `selectedDate` Comes From

```
selectedDate = computed(() => new Date(`${dateISO.value}T${timeHHMM.value}:00`))
```

- `dateISO` and `timeHHMM` are refs updated by:
  - **syncLocalTimeNow()** — Uses `new Date()` and sets `dateISO` / `timeHHMM` (runs on mount and every 60s).
  - **presentDatetimeLocal** setter — When the user edits the datetime input.
  - **shiftPresentHours()** — When the user clicks ◀ or ▶.

### Isolated `new Date()` Usage

- **OrganHourCard** — Uses `new Date().getHours()` only as a fallback when `presentDatetimeLocal` cannot be parsed.
- **syncLocalTimeNow** — Uses `new Date()` to refresh `dateISO` and `timeHHMM`; this is the intended source of “current time” for BaZi.

**Conclusion:** BaZi and temporal hexagrams use reactive store state driven by `dateISO` + `timeHHMM`. Geolocation sets `geoCoords` and `location` for display and API; it does not set the clock. The clock comes from the device (`new Date()`) via `syncLocalTimeNow`. Time is not derived from coordinates; timezone is from `Intl` or ipapi fallback.

---

## 4. User Intent Form — Where Data Is Saved

### Fields

- **User Intent:** `intentDomain`, `intentGoalConstraint`
- **User State:** `userCapacity`, `userLoad`, `userSleepQuality`, `userCognitiveNoise`, `userSocialLoad`, `userEmotionalTone`

### Persistence

| Action | Mechanism |
|--------|-----------|
| **Save** | `persistUserState()` writes to `localStorage` under key `current_almanac_user_state_v1` |
| **Trigger** | `watch([intentDomain, intentGoalConstraint, userCapacity, userLoad, userSleepQuality, userCognitiveNoise, userSocialLoad, userEmotionalTone], () => persistUserState())` |
| **Load** | `loadFromStorage()` in `onMounted` reads `current_almanac_user_state_v1` and hydrates the refs |

### Payload Shape

```json
{
  "intentDomain": "...",
  "intentGoalConstraint": "...",
  "userCapacity": 6,
  "userLoad": 4,
  "userSleepQuality": 6,
  "userCognitiveNoise": 3,
  "userSocialLoad": 4,
  "userEmotionalTone": "..."
}
```

**Summary:** Capacity, Sleep Quality, Cognitive Noise, and other User State fields are stored in Pinia refs and persisted to `localStorage` on change via the watcher.

---

## 5. Data Flow Summary

```
appStore.selectedDate (dateISO + timeHHMM)
    ├── astrologyStore.fourPillars (lunar-javascript) → FourPillarsCard
    ├── temporalHex (lunar-typescript, hexagramsXKDG) → Present pillar grid + hexagrams
    ├── presentOrgan → Organ line in Present panel
    ├── qimenChartHour/Day → CosmicBoard
    └── presentDatetimeLocal → OrganHourCard (hour extraction)

appStore.birthProfile (birthDatetimeLocal + birthSect)
    └── birthTemporalHex → Past pillar grid + hexagrams

appStore (refs)
    └── User Intent + User State → persistUserState() → localStorage
```

---

## 6. Dual Lunar Libraries

| Library | Usage |
|---------|-------|
| **lunar-javascript** | `astrologyStore` (FourPillarsCard), `hexagramsTemporal` |
| **lunar-typescript** | `appStore` (advancedAstro, serializeForApi), `hexagramsXKDG`, `qimen`, `baziNineStar`, `daliuren` |

Present-moment BaZi pillars use **lunar-javascript** in `astrologyStore`. Past/Present hexagram pillars use **lunar-typescript** via `hexagramsXKDG` and `getTemporalXkdg`.
