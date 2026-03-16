# Task 12.1 — Alpha Gatekeeper & Mobile Layout Refactor

**Domain:** Phase 3.0 — Alpha Web Prototype (Gatekeeper & UI Refactor)  
**Date:** 2026-03-16  
**Status:** Implemented

---

## Overview

Task 12.1 deploys a human-viewable alpha prototype behind a simple global password gatekeeper and fixes the mobile layout. The dense user settings (Intent, Location) that previously stacked on top of the main BaZi UI have been reorganized: the Active Meridian is extracted to the top, the rest of the settings are hidden behind an "Advanced" toggle, and user defaults are reset to standard values.

---

## Requirements Summary

| Requirement | Implementation |
|-------------|----------------|
| **Gatekeeper** | Full-screen opaque overlay with password input and Unlock button |
| **Password** | Hardcoded check (`dao2026`) |
| **Persistence** | `localStorage.alpha_unlocked: true` when unlocked |
| **Conditional mount** | Rest of app only mounts when unlocked |
| **Sane defaults** | Birth: 1990-01-01 12:00, Location: null, Intent: General Wellness |
| **Mobile layout** | Active Meridian at top; BaZi charts first; Advanced Settings collapsed |
| **Advanced toggle** | `<details>` titled "⚙️ Advanced Settings & Under the Hood" |

---

## Implementation Details

### 1. Gatekeeper (App.vue)

- **Location:** `src/App.vue`
- **Overlay:** `gatekeeper-overlay` — fixed, full-screen, `z-index: 9999`, uses `var(--color-daoist-bg)`
- **Password:** `ALPHA_PASSWORD = "dao2026"`
- **Storage key:** `alpha_unlocked`
- **Flow:** On mount, checks `localStorage.getItem("alpha_unlocked") === "true"`. If not unlocked, renders only the overlay. On correct password, sets `localStorage.setItem("alpha_unlocked", "true")` and reveals the app.

### 2. Sane Defaults (appStore.ts)

- **Birth datetime:** `1990-01-01T12:00` (via `normalizeDatetimeLocal` fallback and `LS_KEY_BIRTH_DT`)
- **Location:** `""` (empty)
- **Intent domain:** `"General Wellness"`
- **Intent goal constraint:** `"General wellness and balance."`

### 3. Mobile Layout Refactor (HomeView.vue)

- **Active Meridian:** Moved from sidebar to top of content as `activeMeridianSection`, rendered immediately below the header
- **Sidebar:** Primary actions (Generate Reading, Clear Log) and Recent readings remain visible
- **Advanced Settings:** Location, Timezone, Lat/Lon, Preferred Dialect, User Intent, User State moved into `<details>` titled "⚙️ Advanced Settings & Under the Hood"
- **Mobile order:** At `max-width: 980px`, `.main` has `order: 1` and `.side` has `order: 2` so BaZi charts appear before the sidebar

### 4. Files Modified

| File | Changes |
|------|---------|
| `src/App.vue` | Gatekeeper overlay, conditional render, gatekeeper styles |
| `src/stores/appStore.ts` | Defaults for `intentDomain`, `intentGoalConstraint` |
| `src/views/HomeView.vue` | Active Meridian section, Advanced Settings details, mobile order |

---

## UX Notes

- **First load:** User sees full-screen gatekeeper; enters password; unlocks; app loads with no re-prompt on refresh
- **Mobile:** Header → Active Meridian (Organ Hour) → BaZi charts (Past, Present) → Sidebar (Generate, Clear, Recent, Advanced collapsed)
- **Desktop:** Layout preserved; Advanced Settings in sidebar collapsed by default

---

## Future Considerations

- Replace hardcoded password with env variable or server-side check for production
- Optional "Lock" button to clear `alpha_unlocked` and return to gatekeeper
