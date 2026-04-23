/**
 * Vedic (Lahiri sidereal) chart math using the MIT `astronomia` ephemeris (Meeus / VSOP87).
 * Pure client-side; no network. Ayanamsa: linear Lahiri from J2000.0, consistent with
 * common published annual tables to within a fraction of a degree (see task doc).
 */
import { DateToJDE, DateToJD } from "astronomia/julian";
import moonposition from "astronomia/moonposition";
import { Planet, toFK5 } from "astronomia/planetposition";
import nutation from "astronomia/nutation";
import sidereal from "astronomia/sidereal";
import data from "astronomia/data";

// --- Constants (Jyotish) --------------------------------------------------

/** Sanskrit rāśi names in rāśi order 0 = Mesha (Aries) … 11 = Mīna (Pisces). */
export const VEDIC_RASI_SANSKRIT = [
  "Mesha",
  "Vrishabha",
  "Mithuna",
  "Karka",
  "Simha",
  "Kanya",
  "Tula",
  "Vrishchika",
  "Dhanu",
  "Makara",
  "Kumbha",
  "Meena",
] as const;

export const VEDIC_RASI_EN = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
] as const;

const NAKSHATRA_NAMES = [
  "Ashwini",
  "Bharani",
  "Krittika",
  "Rohini",
  "Mrigashirsha",
  "Ardra",
  "Punarvasu",
  "Pushya",
  "Ashlesha",
  "Magha",
  "Purva Phalguni",
  "Uttara Phalguni",
  "Hasta",
  "Chitra",
  "Swati",
  "Vishakha",
  "Anuradha",
  "Jyeshtha",
  "Mula",
  "Purva Ashadha",
  "Uttara Ashadha",
  "Shravana",
  "Dhanishta",
  "Shatabhisha",
  "Purva Bhadrapada",
  "Uttara Bhadrapada",
  "Revati",
] as const;

/** Viṃśottari order (1 pada each), length 27. */
const NAKSHATRA_LORDS: readonly string[] = [
  "Ketu",
  "Venus",
  "Sun",
  "Moon",
  "Mars",
  "Rahu",
  "Jupiter",
  "Saturn",
  "Mercury",
  "Ketu",
  "Venus",
  "Sun",
  "Moon",
  "Mars",
  "Rahu",
  "Jupiter",
  "Saturn",
  "Mercury",
  "Ketu",
  "Venus",
  "Sun",
  "Moon",
  "Mars",
  "Rahu",
  "Jupiter",
  "Saturn",
  "Mercury",
];

const NAK_SPAN = 13 + 20 / 60;
const PADA_SPAN = 3 + 20 / 60;

// --- Public types (LLM / store friendly) ----------------------------------

export type VedicGrahaId =
  | "Lagna"
  | "Sun"
  | "Moon"
  | "Mars"
  | "Mercury"
  | "Jupiter"
  | "Venus"
  | "Saturn"
  | "Rahu"
  | "Ketu";

export type NakshatraPada = 1 | 2 | 3 | 4;

export interface VedicNakshatra {
  name: (typeof NAKSHATRA_NAMES)[number];
  index0: number;
  pada: NakshatraPada;
  padaLord: string;
  spanStartDegSidereal: number;
  spanEndDegSidereal: number;
}

export interface VedicRasi {
  index0: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11;
  sanskrit: (typeof VEDIC_RASI_SANSKRIT)[number];
  en: (typeof VEDIC_RASI_EN)[number];
}

export interface VedicGrahaPlacement {
  id: VedicGrahaId;
  abbr: "As" | "Su" | "Mo" | "Ma" | "Me" | "Ju" | "Ve" | "Sa" | "Ra" | "Ke";
  siderealLongitudeDeg: number;
  degreeInRasi: number;
  rasi: VedicRasi;
  nakshatra: VedicNakshatra;
  isRetrograde: boolean;
  tropicalLongitudeDeg: number;
}

export interface VedicChartSnapshot {
  version: 1;
  inputUtc: string;
  input: {
    latitude: number;
    longitude: number;
  };
  ephemeris: { library: "astronomia"; model: "VSOP87" | "Meeus"; moon: "Elp/series" };
  ayanamsa: {
    system: "Lahiri";
    degrees: number;
    model: "J2000_linear_50.29_apy";
  };
  bodies: VedicGrahaPlacement[];
}

// --- Ayanamsa (Lahiri) ------------------------------------------------------

/** Chitra-paksha Lahiri via J2000 baseline + ~50.29"/yr (matches common tables to ~0.1°). */
function lahiriAyanamshaDegrees(jd: number): number {
  const days = jd - 2451545.0;
  const DEG_PER_DAY = 50.29 / 3600 / 365.25;
  return 23.85 + days * DEG_PER_DAY;
}

function normalizeDeg(d: number): number {
  return ((d % 360) + 360) % 360;
}

function toSidereal(tropicalDeg: number, ayan: number): number {
  return normalizeDeg(tropicalDeg - ayan);
}

// --- Ephemeris helpers (tropical) ------------------------------------------

function sunTrueLongitudeDeg(jd: number): number {
  const T = (jd - 2451545.0) / 36525.0;
  const L0 = normalizeDeg(280.46646 + 36000.76983 * T + 0.0003032 * T * T);
  const M = normalizeDeg(357.52911 + 35999.05029 * T - 0.0001537 * T * T);
  const Mrad = (M * Math.PI) / 180;
  const C =
    (1.914602 - 0.004817 * T - 0.000014 * T * T) * Math.sin(Mrad) +
    (0.019993 - 0.000101 * T) * Math.sin(2 * Mrad) +
    0.000289 * Math.sin(3 * Mrad);
  return normalizeDeg(L0 + C);
}

function geocentricEclipticLongitudeDeg(
  jde: number,
  earth: InstanceType<typeof Planet>,
  planet: InstanceType<typeof Planet>,
): number {
  const ePos = earth.position(jde);
  const R = ePos.range;
  const eFK5 = toFK5(ePos.lon, ePos.lat, jde);
  const l0 = eFK5.lon;
  const b0 = eFK5.lat;
  const [sl0, cl0] = [Math.sin(l0), Math.cos(l0)];
  const sb0 = Math.sin(b0);
  let τ = 0.5;
  const lightDays = 173.1446327;
  let l = 0;
  let b = 0;
  let r = 0;
  let x = 0;
  let y = 0;
  let z = 0;
  for (let k = 0; k < 2; k++) {
    const pPos = planet.position(jde - τ);
    r = pPos.range;
    const pFK5 = toFK5(pPos.lon, pPos.lat, jde);
    l = pFK5.lon;
    b = pFK5.lat;
    const sb = Math.sin(b);
    const cb = Math.cos(b);
    const sl = Math.sin(l);
    const cl = Math.cos(l);
    x = r * cb * cl - R * cl0;
    y = r * cb * sl - R * sl0;
    z = r * sb - R * sb0;
    const dist = Math.sqrt(x * x + y * y + z * z);
    τ = dist / lightDays;
  }
  const λ = (Math.atan2(y, x) * 180) / Math.PI;
  return normalizeDeg(λ);
}

function meanLunarNodeTropicalDeg(jd: number): number {
  const T = (jd - 2451545.0) / 36525.0;
  let ω =
    125.04452 - 1934.136261 * T + 0.0020708 * T * T + (T * T * T) / 450000;
  return normalizeDeg(ω);
}

// --- Ascendant (Meeus / ecliptic intersection; tropical then sidereal) ------

function eastLongitudeRad(longitude: number): number {
  return (longitude * Math.PI) / 180;
}

function ascendantTropicalDeg(jd: number, jde: number, latitude: number, longitude: number): number {
  const gst = sidereal.apparent(jd);
  const ramc = normalizeDeg(gst / 240 + longitude);
  const r = (ramc * Math.PI) / 180;
  const ϕ = eastLongitudeRad(latitude);
  const ε0 = nutation.meanObliquity(jde);
  const [, dε] = nutation.nutation(jde);
  const ε = ε0 + dε;
  const y = -Math.sin(r);
  const x = Math.cos(r) * Math.cos(ε) + Math.sin(ε) * Math.tan(ϕ);
  let asc = (Math.atan2(y, x) * 180) / Math.PI;
  if (asc < 0) asc += 360;
  return normalizeDeg(asc);
}

// --- Rāśi / Nakṣatra --------------------------------------------------------

function rasiFromSidereal(sid: number): VedicRasi {
  const idx = Math.floor(sid / 30) % 12;
  if (idx < 0 || idx > 11) {
    return {
      index0: 0,
      sanskrit: VEDIC_RASI_SANSKRIT[0],
      en: VEDIC_RASI_EN[0],
    };
  }
  return {
    index0: idx as VedicRasi["index0"],
    sanskrit: VEDIC_RASI_SANSKRIT[idx]!,
    en: VEDIC_RASI_EN[idx]!,
  };
}

function nakshatraFromSidereal(sid: number): VedicNakshatra {
  const lon = normalizeDeg(sid);
  const idx = Math.min(26, Math.floor(lon / NAK_SPAN));
  const posIn = lon - idx * NAK_SPAN;
  const pada = (Math.min(3, Math.floor(posIn / PADA_SPAN)) + 1) as NakshatraPada;
  const name = NAKSHATRA_NAMES[idx]!;
  return {
    name,
    index0: idx,
    pada,
    padaLord: NAKSHATRA_LORDS[idx] ?? "—",
    spanStartDegSidereal: idx * NAK_SPAN,
    spanEndDegSidereal: (idx + 1) * NAK_SPAN,
  };
}

// --- Public API -------------------------------------------------------------

/**
 * Build a Vedic (sidereal Lahiri) snapshot: Lagna, Sun–Ketu, rāśi, degree-in-sign,
 * and nakṣatra for every body (Moon highlighted in UI separately).
 */
export function getVedicChart(date: Date, latitude: number, longitude: number): VedicChartSnapshot {
  const jd = DateToJD(date);
  const jde = DateToJDE(date);
  const ayan = lahiriAyanamshaDegrees(jd);
  const earth = new Planet(data.vsop87Bearth);
  const tropAsc = ascendantTropicalDeg(jd, jde, latitude, longitude);

  const sunT = sunTrueLongitudeDeg(jd);
  const moonP = moonposition.position(jde);
  const moonT = normalizeDeg((moonP.lon * 180) / Math.PI);

  const makeBody = (
    id: VedicGrahaId,
    abbr: VedicGrahaPlacement["abbr"],
    tropicalDeg: number,
    isRetro: boolean,
  ): VedicGrahaPlacement => {
    const sid = toSidereal(tropicalDeg, ayan);
    const dIn = ((sid % 30) + 30) % 30;
    return {
      id,
      abbr,
      siderealLongitudeDeg: Number(sid.toFixed(6)),
      degreeInRasi: Number(dIn.toFixed(6)),
      rasi: rasiFromSidereal(sid),
      nakshatra: nakshatraFromSidereal(sid),
      isRetrograde: isRetro,
      tropicalLongitudeDeg: Number(tropicalDeg.toFixed(6)),
    };
  };

  const mercury = new Planet(data.vsop87Bmercury);
  const venus = new Planet(data.vsop87Bvenus);
  const mars = new Planet(data.vsop87Bmars);
  const jupiter = new Planet(data.vsop87Bjupiter);
  const saturn = new Planet(data.vsop87Bsaturn);
  const lonPrev = (p: InstanceType<typeof Planet>) =>
    geocentricEclipticLongitudeDeg(jd - 1, earth, p);
  const lonOf = (p: InstanceType<typeof Planet>, j: number) =>
    geocentricEclipticLongitudeDeg(j, earth, p);
  const retro = (p: InstanceType<typeof Planet>, j: number) => {
    const a = lonPrev(p);
    const b = lonOf(p, j);
    let d = b - a;
    d = ((d % 360) + 360) % 360;
    if (d > 180) d -= 360;
    return d < 0;
  };

  const sun = makeBody("Sun", "Su", sunT, false);
  const moon = makeBody("Moon", "Mo", moonT, false);
  const m = makeBody("Mars", "Ma", geocentricEclipticLongitudeDeg(jde, earth, mars), retro(mars, jde));
  const me = makeBody("Mercury", "Me", geocentricEclipticLongitudeDeg(jde, earth, mercury), retro(mercury, jde));
  const j = makeBody("Jupiter", "Ju", geocentricEclipticLongitudeDeg(jde, earth, jupiter), retro(jupiter, jde));
  const v = makeBody("Venus", "Ve", geocentricEclipticLongitudeDeg(jde, earth, venus), retro(venus, jde));
  const s = makeBody("Saturn", "Sa", geocentricEclipticLongitudeDeg(jde, earth, saturn), retro(saturn, jde));
  const rahuT = meanLunarNodeTropicalDeg(jd);
  const ketuT = normalizeDeg(rahuT + 180);
  const rahu = makeBody("Rahu", "Ra", rahuT, true);
  const ketu = makeBody("Ketu", "Ke", ketuT, true);

  return {
    version: 1,
    inputUtc: date.toISOString(),
    input: { latitude, longitude },
    ephemeris: { library: "astronomia", model: "VSOP87", moon: "Elp/series" },
    ayanamsa: {
      system: "Lahiri",
      degrees: Number(ayan.toFixed(6)),
      model: "J2000_linear_50.29_apy",
    },
    bodies: [
      makeBody("Lagna", "As", tropAsc, false),
      sun,
      moon,
      m,
      me,
      j,
      v,
      s,
      rahu,
      ketu,
    ],
  };
}