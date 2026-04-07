# Task 12.4 — True Solar Time & BaZi Bounds

**Domain:** Phase 3.0 — Astrophysics & Precision Timing  
**Date:** 2026-03-17  
**Status:** Implemented

---

## Overview

Task 12.4 elevates the BaZi engine to support **True Solar Time** (Local Apparent Time) based on the user's exact longitude, moving away from political timezones. The UI displays exact **Bounds** (start and end times) for each Year, Month, Day, and Hour pillar the user examines.

---

## Requirements Summary

| Requirement | Implementation |
|-------------|----------------|
| **True Solar Time toggle** | `useTrueSolarTime` in appStore (default `false`), persisted |
| **Longitude state** | `longitude` computed from `geoCoords.lon` |
| **UI toggle** | "Enable True Solar Time (Requires Longitude)" in Advanced Settings |
| **Astrophysics math** | `src/utils/solarTime.ts` — EoT + 4 min/degree longitude offset |
| **Pillar bounds** | `PillarBounds.vue` + `src/utils/pillarBounds.ts` |
| **Year bounds** | Li Chun (立春) exact moment via lunar-typescript |
| **Hour bounds** | 2-hour Shichen blocks, EoT-adjusted when True Solar on |

---

## Implementation Details

### 1. Store State (`src/stores/appStore.ts`)

- **`useTrueSolarTime`**: `ref(false)` — toggles full True Solar Time (EoT + longitude)
- **`longitude`**: `computed(() => geoCoords?.lon ?? null)` — from geolocation
- **`solarAdjustedSelectedDate`**: When `useTrueSolarTime` and `longitude` are set, applies `getTrueSolarTime(date, lon)`. Otherwise returns raw `selectedDate`.
- Persisted via `loadFromStorage` / `persistUserState`.

### 2. True Solar Time Math (`src/utils/solarTime.ts`)

- **Equation of Time (EoT)**: Two-term sine approximation  
  `EoT ≈ -7.655·sin(d) + 9.873·sin(2d + 3.588)` where `d = 2π·(dayOfYear - 1) / 365.25`
- **Longitude offset**: 4 minutes per degree from timezone central meridian  
  `(longitude - centralMeridian) × 4`
- **`getTrueSolarTime(standardDate, longitude)`**: Returns a `Date` adjusted by EoT + longitude correction for BaZi pillar calculations.

### 3. Pillar Bounds (`src/utils/pillarBounds.ts`)

- **`getBaZiYear(date)`**: Returns the BaZi year (starts at Li Chun). Before this year's Li Chun → previous calendar year.
- **`getYearPillarBounds(year)`**: Li Chun start → next Li Chun (via lunar-typescript `getJieQiTable`).
- **`getMonthPillarBounds(date)`**: Prev Jie Qi → Next Jie Qi (current month boundaries).
- **`getDayPillarBounds(date)`**: Midnight to midnight.
- **`getHourPillarBounds(branchChar, referenceDate, useTrueSolarTime)`**: Uses `ORGAN_CLOCK` for 2-hour blocks. When True Solar on, applies EoT to displayed bounds (e.g. "11:14 AM – 1:14 PM").

### 4. UI Components

- **Toggle**: In `HomeView.vue` Advanced section — checkbox "Enable True Solar Time (Requires Longitude)". Disabled when `longitude === null`.
- **PillarBounds.vue**: Displays "Bounds: {start} – {end}" for each pillar. Used in all 8 pillar boxes (Birth + Present × 4 pillars).

### 5. Data Flow

```
selectedDate → (useTrueSolarTime && longitude) ? getTrueSolarTime(date, lon) : date
     → solarAdjustedSelectedDate
     → temporalHex, advancedAstroMoment, PillarBounds (Present)

birthDatetimeLocal → birthReferenceDate
     → PillarBounds (Birth, useTrueSolarTime=false)
```

---

## Files Touched

| File | Change |
|------|--------|
| `src/stores/appStore.ts` | `useTrueSolarTime`, `longitude`, `solarAdjustedSelectedDate`, persistence |
| `src/utils/solarTime.ts` | `getTrueSolarTime`, EoT, longitude offset |
| `src/utils/pillarBounds.ts` | `getBaZiYear`, `getYearPillarBounds`, `getMonthPillarBounds`, `getDayPillarBounds`, `getHourPillarBounds` |
| `src/components/astrology/PillarBounds.vue` | New — bounds display per pillar |
| `src/views/HomeView.vue` | True Solar toggle, PillarBounds in all 8 pillars |

---

## Ephemeris

The project uses **lunar-typescript** for Li Chun and Jie Qi (24 Solar Terms). No additional npm packages were required; lunar-typescript provides `getJieQiTable()` and `getPrevJieQi()` / `getNextJieQi()` for exact astronomical bounds.

---

## Future Work

- Birth longitude: apply True Solar correction for birth charts when birth location coords are available.
- Qimen & Organ Hour: use `solarAdjustedSelectedDate` for consistency when True Solar is on.
