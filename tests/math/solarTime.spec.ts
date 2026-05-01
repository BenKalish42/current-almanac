import { describe, it, expect } from "vitest";
import { getEquationOfTime, getTrueSolarTime } from "@/utils/solarTime";

/**
 * NOAA Solar Position Calculator — sampled and rounded.
 * https://gml.noaa.gov/grad/solcalc/
 *
 * EoT in minutes. Tolerance ±2.5 min — `solarTime.ts` uses the simplified
 * 2-term sine approximation (Heliocentric: -7.655·sin(d) + 9.873·sin(2d+3.588)),
 * which deviates from NOAA's full ephemeris by up to ~2 min around the
 * autumn-equinox local extremum. For BaZi pillars at 2-hour granularity
 * this is well below the resolution that matters; this test guards
 * against regression to a *broken* implementation.
 *
 * A future upgrade to a full ephemeris (e.g. via astronomia) can tighten
 * to ±0.5 min — that's tracked in docs/architecture/phase_4 once Vedic
 * lands fully.
 */
const NOAA_FIXTURES: { date: string; expectedMinutes: number }[] = [
  { date: "2024-01-15T12:00:00Z", expectedMinutes: -9.2 },
  { date: "2024-02-15T12:00:00Z", expectedMinutes: -14.0 },
  { date: "2024-04-15T12:00:00Z", expectedMinutes: -0.1 },
  { date: "2024-06-15T12:00:00Z", expectedMinutes: -0.4 },
  { date: "2024-09-15T12:00:00Z", expectedMinutes: 4.6 },
  { date: "2024-11-03T12:00:00Z", expectedMinutes: 16.5 },
];

const EOT_TOLERANCE_MIN = 2.5;

describe("solarTime — Equation of Time", () => {
  for (const fx of NOAA_FIXTURES) {
    it(`${fx.date} ≈ ${fx.expectedMinutes}m (±${EOT_TOLERANCE_MIN})`, () => {
      const d = new Date(fx.date);
      const eot = getEquationOfTime(d);
      expect(eot).toBeGreaterThanOrEqual(fx.expectedMinutes - EOT_TOLERANCE_MIN);
      expect(eot).toBeLessThanOrEqual(fx.expectedMinutes + EOT_TOLERANCE_MIN);
    });
  }
});

describe("solarTime — getTrueSolarTime", () => {
  it("is identity at central meridian on equinox-like EoT zero", () => {
    // ~April 15: EoT ≈ 0 min. Central meridian for the test runner's tz.
    const tz = new Date("2024-04-15T12:00:00Z");
    const offsetMin = -tz.getTimezoneOffset();
    const centralMeridian = (offsetMin / 60) * 15;
    const out = getTrueSolarTime(tz, centralMeridian);
    const drift = Math.abs(out.getTime() - tz.getTime()) / 1000 / 60;
    expect(drift).toBeLessThan(2); // < 2 minutes drift
  });

  it("shifts forward when longitude is east of central meridian", () => {
    const tz = new Date("2024-06-15T12:00:00Z");
    const offsetMin = -tz.getTimezoneOffset();
    const centralMeridian = (offsetMin / 60) * 15;
    // 5° east → +20 min, EoT June ~ -0.4 → +19.6 min
    const out = getTrueSolarTime(tz, centralMeridian + 5);
    const driftMin = (out.getTime() - tz.getTime()) / 1000 / 60;
    expect(driftMin).toBeGreaterThan(15);
    expect(driftMin).toBeLessThan(25);
  });

  it("shifts backward when longitude is west of central meridian", () => {
    const tz = new Date("2024-06-15T12:00:00Z");
    const offsetMin = -tz.getTimezoneOffset();
    const centralMeridian = (offsetMin / 60) * 15;
    const out = getTrueSolarTime(tz, centralMeridian - 5);
    const driftMin = (out.getTime() - tz.getTime()) / 1000 / 60;
    expect(driftMin).toBeLessThan(-15);
    expect(driftMin).toBeGreaterThan(-25);
  });
});
