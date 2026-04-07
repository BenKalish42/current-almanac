# Task 12.5 — Birth Location & Global Date Formatting

**Domain:** Phase 3.0 — Astrophysics & Precision Timing  
**Date:** 2026-03-17  
**Status:** Implemented

---

## Overview

Task 12.5 completes True Solar Time by adding **Birth Location** inputs (city name + longitude) so the natal BaZi chart can be perfectly accurate when True Solar Time is enabled. It also adds a **Date Format** toggle (US, EU, Asian) so BaZi pillar bounds are readable for a global audience.

---

## Requirements Summary

| Requirement | Implementation |
|-------------|----------------|
| **Birth location state** | `birthLocationName`, `birthLongitude` in appStore |
| **Date format state** | `dateFormat: "US" \| "EU" \| "ASIAN"` (default `"US"`) |
| **Birth inputs** | Text input (City), number input (Longitude) in Birth panel |
| **Date format select** | Dropdown in Advanced Settings |
| **Natal True Solar** | When `useTrueSolarTime` and `birthLongitude` exist, birth date runs through `getTrueSolarTime()` before pillar calculation |
| **formatDate utility** | `src/utils/formatters.ts` — US/EU/ASIAN formats |
| **Bounds formatting** | PillarBounds uses `formatDate` for Year/Month/Day bounds |

---

## Implementation Details

### 1. Store State (`src/stores/appStore.ts`)

- **`birthLocationName`**: `ref("")` — city or place name for display
- **`birthLongitude`**: `ref<number | null>(null)` — longitude for natal True Solar Time
- **`dateFormat`**: `ref<"US" | "EU" | "ASIAN">("US")` — bounds display format
- **`birthTemporalHex`**: When `useTrueSolarTime && birthLongitude != null`, applies `getTrueSolarTime(baseDate, birthLongitude)` before `getTemporalXkdg`
- All three persisted in `loadFromStorage` / `persistUserState`

### 2. formatDate Utility (`src/utils/formatters.ts`)

```typescript
formatDate(date: Date, formatType: "US" | "EU" | "ASIAN"): string
```

- **US** → `MM/DD/YYYY HH:mm`
- **EU** → `DD/MM/YYYY HH:mm`
- **ASIAN** → `YYYY/MM/DD HH:mm`

### 3. Pillar Bounds Integration

- `getYearPillarBounds`, `getMonthPillarBounds`, `getDayPillarBounds` accept optional `dateFormat` parameter
- Hour pillar keeps time-only format (no date component)
- `PillarBounds.vue` receives `dateFormat` prop from store and passes it to the bounds functions

### 4. UI (HomeView.vue)

- **Birth panel**: Birth Location (text), Birth Longitude (number, placeholder `e.g. -73.99`) next to Birth datetime
- **Advanced section**: Date Format select (US / EU / Asian) next to True Solar Time toggle
- **birthReferenceDate**: Solar-adjusted when `useTrueSolarTime && birthLongitude`

---

## Data Flow

```
Birth inputs → birthDatetimeLocal, birthLocationName, birthLongitude
     → (useTrueSolarTime && birthLongitude) ? getTrueSolarTime(date, birthLongitude) : date
     → birthTemporalHex, birthReferenceDate
     → PillarBounds (Birth) with dateFormat

dateFormat → PillarBounds (all sections) → formatDate() for Year/Month/Day bounds
```

---

## Files Touched

| File | Change |
|------|--------|
| `src/stores/appStore.ts` | `birthLocationName`, `birthLongitude`, `dateFormat`, birth True Solar logic, persistence |
| `src/utils/formatters.ts` | `formatDate`, `DateFormatType` |
| `src/utils/pillarBounds.ts` | `dateFormat` param for Year/Month/Day bounds, `formatDate` usage |
| `src/components/astrology/PillarBounds.vue` | `dateFormat` prop, pass to bounds functions |
| `src/views/HomeView.vue` | Birth location/longitude inputs, Date Format select, birthReferenceDate solar adjustment |

---

## Future Work

- Geocoding API to populate birth longitude from city name
- Birth timezone (for users born in different timezone than current)
