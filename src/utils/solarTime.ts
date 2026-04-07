/**
 * Task 12.4 — True Solar Time (Local Apparent Time)
 *
 * Converts standard (clock) time to Local Apparent Time using:
 * 1. Equation of Time (EoT) — difference between mean and apparent solar time
 * 2. Longitude offset — 4 minutes per degree from the timezone's central meridian
 *
 * When useTrueSolarTime is enabled, BaZi calculations run on this adjusted date.
 */

const MINUTES_PER_DEGREE = 4;

/**
 * Equation of Time (minutes) — approximation using day-of-year.
 * EoT = apparent solar time − mean solar time.
 * Positive EoT = sun runs "ahead" of the clock (solar noon early).
 *
 * Uses the simplified two-term sine approximation:
 * EoT ≈ -7.655·sin(d) + 9.873·sin(2d + 3.588)
 * where d = 2π·(dayOfYear - 1) / 365.25
 *
 * @see https://www.celestialprogramming.com/snippets/equationoftime-simple.html
 */
function equationOfTimeMinutes(date: Date): number {
  const start = new Date(date.getFullYear(), 0, 1);
  const diff = date.getTime() - start.getTime();
  const dayOfYear = Math.floor(diff / 86400000) + 1;
  const d = (2 * Math.PI * (dayOfYear - 1)) / 365.25;
  return -7.655 * Math.sin(d) + 9.873 * Math.sin(2 * d + 3.588);
}

/**
 * Central meridian of the local timezone (degrees).
 * getTimezoneOffset() returns minutes behind UTC; positive = west of UTC.
 * 15° per hour, so meridian = -offset_minutes / 4 (since 60 min = 15°).
 */
function getTimezoneCentralMeridian(date: Date): number {
  const offsetMinutes = -date.getTimezoneOffset();
  return (offsetMinutes / 60) * 15;
}

/**
 * Converts standard (clock) time to Local Apparent Time (True Solar Time).
 *
 * Correction = EoT + (longitude - centralMeridian) × 4 minutes
 * We add this to the standard time to get the equivalent moment in true solar terms:
 * i.e., "what the sundial would show" at the user's longitude.
 *
 * For BaZi: we want the Date that, when interpreted as local apparent time,
 * corresponds to the user's selected clock time. So we SUBTRACT the correction
 * from the standard date to get the "effective" moment for BaZi (the moment
 * when the sun is at the position implied by the user's clock if using a sundial).
 *
 * Actually: The user selects "12:00" on their clock. If we use True Solar,
 * we want BaZi to reflect "solar noon at my longitude" — i.e. when the sun
 * crosses their meridian. Solar noon at longitude L happens at standard time
 * T when: T + correction = 12:00 solar. So the "effective" standard time
 * for BaZi when user picks 12:00 should be 12:00 - correction. That means
 * we ADD correction to the standard time to "shift" the moment to when
 * the sun is actually at that position? No.
 *
 * Simpler: Standard time = what the clock shows. True Solar Time at that moment
 * = standard + EoT + longitude_offset. So when it's 12:00 clock in NYC,
 * the true solar time might be 11:46 (sun hasn't reached noon yet). For BaZi,
 * we need to know: given the user picked 12:00 clock, what is the equivalent
 * in "solar" terms for pillar calculation? The BaZi system uses solar time.
 * So we need to take the user's clock time and convert TO solar time to
 * determine which pillar applies.
 *
 * Clock 12:00 → Solar time = 12:00 + EoT + long_offset. So we ADD the
 * correction to get the solar time. But we're passing a Date to getTemporalXkdg.
 * The Date is always in local timezone. So we're not changing timezone — we're
 * saying "at this instant, the solar time is X". The pillars depend on solar
 * position. So we need to ADJUST the date such that when getTemporalXkdg reads
 * it, it gets the right pillar. If the user is at 12:00 clock and solar is
 * 11:46, then for pillar purposes we want to use 11:46 — so we SUBTRACT the
 * correction (go back in time) to get the Date that yields the right pillar.
 * No — getTemporalXkdg uses the date's local H:M. So if we pass 11:46, we get
 * the pillar for 11:46. The user intended 12:00 solar = 12:00 + correction
 * clock? No. Let me think again.
 *
 * Standard: user picks 12:00. Solar noon at their longitude might occur at
 * 11:46 clock (if they're west of the meridian). So at 12:00 clock, solar time
 * is 12:14 (past noon). For BaZi hour pillar: the 午 hour is 11:00-13:00 SOLAR.
 * At 12:00 clock with correction +14 min, solar = 12:14, so we're in 午. Good.
 * So we want the Date to represent "solar 12:14" which in local terms is...
 * The pillars are based on solar time. lunar-typescript getTimeInGanZhi uses
 * the hour. So we need to pass a Date whose hour, when interpreted as SOLAR
 * hour, is correct. The library uses the Date's local hour directly. So we need
 * to pass a Date that is "shifted" so that its local clock hour corresponds
 * to solar time. Solar hour = Clock hour + (EoT + long_offset)/60. So to get
 * the right solar hour from our Date, we need Clock hour = Solar hour - corr.
 * The user picks "solar hour" effectively (they want to know "what's my BaZi
 * at solar noon"). So we treat their input as solar. Clock = Solar - corr.
 * So we SUBTRACT the correction from the date. new Date = date - correction.
 */
export function getTrueSolarTime(standardDate: Date, longitude: number): Date {
  const eot = equationOfTimeMinutes(standardDate);
  const centralMeridian = getTimezoneCentralMeridian(standardDate);
  const longitudeOffsetMinutes = (longitude - centralMeridian) * MINUTES_PER_DEGREE;
  const totalCorrectionMinutes = eot + longitudeOffsetMinutes;
  return new Date(standardDate.getTime() + totalCorrectionMinutes * 60 * 1000);
}

/**
 * Returns the Equation of Time in minutes for a given date.
 * Useful for display or debugging.
 */
export function getEquationOfTime(date: Date): number {
  return equationOfTimeMinutes(date);
}
