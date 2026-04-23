# Task 12.8 — Vedic Engine and South Indian Chart (Phase 4)

## Purpose

Offline Vedic (sidereal) chart support for the Temple: Lahiri ayaṅaṁśa applied to tropical longitudes, plus a CSS/Tailwind South Indian (D1-style) house grid and a plain-text placement list. Output is **strictly typed JSON** for downstream **DeepSeek** synthesis prompts.

## Dependency

- **`astronomia` (MIT)** — Jean Meeus / VSOP87 style ephemeris in JavaScript, no network. The project uses:
  - `astronomia/julian` for JD / JDE (UT ↔ TT via ΔT for ephemeris time);
  - `astronomia/moonposition` and `astronomia/planetposition` with `astronomia/data` VSOP87B series;
  - `astronomia/sidereal` (IAU 1982 apparent sidereal time) and `astronomia/nutation` for the ascendant ecliptic longitude;
  - Local type shims: `src/astronomia.d.ts` (the package is JS-only without published `.d.ts` for subpath exports).

`vedic-astro` on npm was evaluated: its published ephemeris used a **fixed 24°** placeholder for Lahiri, so it was **not** used for production math.

## Ayanamsa model

- **Lahiri (Chitra-paksha)**, **linear** baseline: **~23.85° at J2000.0 (JD 2451545)**, with **~50.29″ per year** of solar/tropical precession (implemented as a constant deg/day term). This tracks common annual tables to roughly **0.1°** over recent decades. For sub–arc-minute agreement with Jagaṇnātha Hora / Swiss Ephemeris, swap the ayaṅaṁśa function for a table or WASM Swiss implementation later.

Tropical ecliptic longitudes minus this ayaṅaṁśa yield **sidereal** (Nirāyana) longitudes for grahas and Lagna.

## Ascendant (Lagaṇa)

Tropical ascendant from **Meeus-style** east-point / ecliptic-hizon intersection, using **apparent** sidereal time at Greenwich, true obliquity (mean + nutation in obliquity), and the standard `atan2` form (conventional Western/Vedic ecliptic asc), then **siderealized** with the same Lahiri offset as the planets.

## Code map

| Path | Role |
| --- | --- |
| `src/utils/vedicMath.ts` | `getVedicChart(date, latitude, longitude)` → `VedicChartSnapshot` |
| `src/components/astrology/VedicChart.vue` | Props: `chart` — 4×4 static sign grid + placement list (no SVG) |
| `src/astronomia.d.ts` | Minimal `declare module` for `astronomia/*` subpaths |

## `VedicChartSnapshot` (LLM-oriented)

Stable **`version: 1`**; extend with new optional fields for future engines.

- **`inputUtc`**: ISO string for the `Date` used.
- **`input`**: WGS-84 `latitude` / `longitude` (↔ LST / Lagna).
- **`ephemeris`**: `library: "astronomia"`, `model: "VSOP87"`, moon description.
- **`ayanamsa`**: `system: "Lahiri"`, `degrees`, `model` (implementation tag).
- **`bodies`**: ordered **Lagṇa, Su, Mo, Ma, Me, Ju, Ve, Sa, Ra, Ke**.

Per body (`VedicGrahaPlacement`):

- **`id`**, **`abbr`**, **`siderealLongitudeDeg`**, **`degreeInRasi`**, **`tropicalLongitudeDeg`**
- **`rasi`**: `index0` (0 = Meṣa … 11 = Mīna), `sanskrit`, `en`
- **`nakshatra`**: 27-folds `name`, `index0`, `pada` 1–4, `padaLord`, `spanStartDegSidereal` / `spanEndDegSidereal`
- **`isRetrograde`**

Serialize with `JSON.stringify(snapshot)` (or a minimal subset) into synthesis prompts. Do not depend on field ordering beyond the documented `bodies` list.

## UI notes

`VedicChart.vue` uses a **4×4** CSS grid: **12 perimeter cells** hold the fixed rāśi band (Aries through Pisces, clockwise from top-left, English abbreviations in cells), the **inner 2×2** is an empty/dashed void. Graha abbreviations are grouped by `rasi.index0`. A **list** under the grid repeats rāśi, degree-in-sign, and naṭkṣatra + pada (R for retro where relevant), with the Moon line emphasized.

## See also

- `docs/architecture/` Phase 3 synthesis / Temple pipeline docs for how JSON is ingested by the LLM layer.
