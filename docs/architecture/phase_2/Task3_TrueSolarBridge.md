# Task 3 — True Solar Time Bridge

**Domain:** Phase 2 — Astrology Pillar (True Solar Bridge & Consolidation)  
**Date:** 2026-03-11  
**Status:** Implemented

---

## Overview

BaZi and I-Ching hexagram calculations depend on the user's **True Solar Time** at their location, not just standard clock time. Standard time uses fixed timezone meridians; True Solar Time uses the actual longitude of the user. This document describes how geolocated longitude is applied to lunar-typescript calculations.

---

## Mathematical Basis

### Longitude–Time Relationship

The Earth rotates 360° in 24 hours:

- **1° longitude ≈ 4 minutes** of solar time
- Formula: `longitudeOffsetMinutes = longitude × 4`

### Direction Convention

- **Positive longitude (East):** Sun crosses the meridian earlier → add minutes to UTC to align with local solar time.
- **Negative longitude (West):** Sun crosses the meridian later → subtract (add a negative offset).

### UTC Adjustment

To convert a UTC moment to the equivalent True Solar Time at longitude `L`:

```
adjustedUTC = originalUTC + (longitude × 4) minutes
```

The adjusted `Date` is then passed to the lunar library.

---

## Implementation

### Location

All True Solar Time logic lives in **`src/stores/appStore.ts`**.

### Helper: `solarAdjustedSelectedDate`

A computed property applies the longitude offset when `geoCoords` are available:

```typescript
const solarAdjustedSelectedDate = computed(() => {
  const date = selectedDate.value;
  const coords = geoCoords.value;
  if (!coords || !Number.isFinite(coords.lon)) return date;
  const longitudeOffsetMinutes = coords.lon * 4;
  return new Date(date.getTime() + longitudeOffsetMinutes * 60 * 1000);
});
```

### Graceful Degradation

- **When `geoCoords` is null or `lon` is not finite:** Fall back to `selectedDate` (standard system time).
- **When geolocation resolves:** All present-moment BaZi/hexagram computations automatically use True Solar Time.

### Consumers of Solar-Adjusted Time

| Computed Property    | Uses Solar-Adjusted? | Notes                                                  |
|----------------------|----------------------|--------------------------------------------------------|
| `temporalHex`        | Yes                  | Present-moment pillars + XKDG hexagrams              |
| `advancedAstroMoment`| Yes                  | Full BaZi serialization for AI context                |
| `birthTemporalHex`  | No                   | Birth location longitude not available                |
| `advancedAstroBirth`| No                   | Birth location longitude not available                |
| `qimenChartHour/Day` | No                   | Uses `selectedDate`; could be upgraded later          |
| `presentOrgan`       | No                   | Uses `selectedDate.getHours()`; could be upgraded     |

---

## Lunar-Typescript Integration

The **lunar-typescript** library does not expose a direct `.setExactTime(true)` or longitude parameter for True Solar Time. The approach is:

1. **Pre-adjust the `Date`** in appStore before passing it to the library.
2. Pass the adjusted `Date` into:
   - `getTemporalXkdg(d)` (hexagramsXKDG)
   - `Solar.fromDate(d)` (advancedAstroMoment)
3. The library receives a UTC instant that already encodes the solar correction; it interprets it using its internal Solar/Lunar conversion.

### hexagramsXKDG Flow

```text
selectedDate → solarAdjustedSelectedDate → getTemporalXkdg(d)
                                              ↓
                                    toSolarFromLocalDate(d)
                                              ↓
                                    Solar.fromYmdHms(d.getFullYear(), ...)
                                              ↓
                                    Lunar.fromSolar(solar) → GanZhi + XKDG hex
```

### advancedAstro Flow

```text
solarAdjustedSelectedDate → Solar.fromDate(date) → Lunar.fromSolar(solar)
                                                         ↓
                                              getEightChar() → serializeAdvancedAstro()
```

---

## Consolidation: FourPillarsCard Removed

The standalone `FourPillarsCard` component was removed from `HomeView.vue` to eliminate redundancy. The legacy **PAST (BIRTH)** and **PRESENT (MOMENT)** sections in HomeView are the canonical BaZi + Hexagram UI. They:

- Use `store.birthTemporalHex` and `store.temporalHex`
- Include Hexagram integrations (HexagramLines, HexagramModal)
- Are structurally superior (pillar grids with hex tiles)

---

## Future Considerations

1. **Birth longitude:** If birth location coordinates become available, apply the same offset for `birthTemporalHex` and `advancedAstroBirth`.
2. **Qimen & Organ Hour:** Consider using `solarAdjustedSelectedDate` for `qimenChartHour`, `qimenChartDay`, and `presentOrgan` for consistency.
3. **Equation of Time:** The current implementation uses mean solar time (4 min/degree). A more precise model could incorporate the Equation of Time for apparent solar time.
