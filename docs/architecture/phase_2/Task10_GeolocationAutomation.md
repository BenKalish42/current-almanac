# Task 10: Geolocation Automation (Phase 2 - Astrology Pillar)

**Phase:** 2 — Astrology Pillar (Temporal Mechanics)  
**Task:** 1

---

## 1. Files Modified

| Action | Path |
|--------|------|
| Modified | `package.json` — added @capacitor/geolocation@7 dependency |
| Modified | `src/stores/appStore.ts` — Capacitor Geolocation, geoStatus, geoSource, manual-override actions |
| Modified | `src/views/HomeView.vue` — Location Sync indicator, Advanced Settings accordion |
| Created | `docs/architecture/phase_2/Task10_GeolocationAutomation.md` |

---

## 2. State Variables Mutated / Accessed

| Store | Variable | Usage |
|-------|----------|-------|
| app | `geoCoords` | Write — set from Geolocation.getCurrentPosition or ipapi fallback |
| app | `location` | Write — reverse-geocoded city or from ipapi |
| app | `timezoneLabel` | Write — from Intl or ipapi |
| app | `geoStatus` | Write — idle, loading, resolved, denied, error |
| app | `geoSource` | Write — auto (geolocation) or manual (user override) |

**New actions:** `setManualLocation`, `setManualTimezone`, `setManualGeoCoords`

---

## 3. One-Sentence Summary for AI CTO

Geolocation is now automated via @capacitor/geolocation for native mobile precision; the primary UX shows a minimalist "Location Sync" indicator; manual overrides live in a collapsible Advanced Settings accordion; ipapi fallback handles permission denial.

---

## 4. Core Logic

- **hydrateFromGeolocation:** Calls `Geolocation.getCurrentPosition()` (Capacitor); maps lat/lon to `geoCoords`; reverse-geocodes via Open-Meteo for `location`; sets `timezoneLabel` from `Intl`; on failure, falls back to ipapi.co for coords, city, timezone
- **geoStatus:** `loading` during fetch; `resolved` on success (Capacitor or ipapi); `error` on total failure
- **Manual override:** `setManualLocation`, `setManualTimezone`, `setManualGeoCoords` set `geoSource` to `manual`
- **UI:** Primary flow shows "📍 Aligning with the Cosmos…" → "📍 [City or Lat,Lon] (Auto)" when resolved; Advanced Settings accordion contains Location, Timezone, Lat/Lon inputs and "Use current location" button
