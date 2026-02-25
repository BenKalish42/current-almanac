/**
 * Tai Yi Shen Shu (太乙神数) engine.
 * Uses Accumulation Year, 72-year Ji cycle, 3-year residency, and 8-Palace skip-5 sequence.
 * For hidden AI context only — not rendered in UI.
 */

/** 8-Palace indices (0–7) mapped to palace numbers. */
const YANG_DUN_PALACES = [1, 8, 3, 4, 9, 2, 7, 6] as const;
const YIN_DUN_PALACES = [9, 2, 7, 6, 1, 8, 3, 4] as const;

export type TaiYiResult = {
  year: number;
  accumulationYear: number;
  configurationNumber: number;
  palaceIndex: number;
  palaceNumber: number;
  dun: "Yang" | "Yin";
};

/**
 * Compute the Tai Yi current palace for a given date.
 * - Accumulation Year: A = Y + 10,155,341
 * - Configuration: n = A % 360 (if 0 then 360)
 * - 3-year residency, 24-year circuit: palace index from ((n % 72) || 72) % 24 / 3
 * - Skip-5 maps to 8-Palace sequence by Yang/Yin Dun.
 * - Dun: Yang after Winter Solstice, Yin after Summer Solstice.
 */
export function computeTaiYi(date: Date): TaiYiResult {
  const year = date.getFullYear();
  const A = year + 10_155_341;
  let n = A % 360;
  if (n === 0) n = 360;

  const raw = (n % 72) || 72;
  const cyclePos = raw % 24;
  const idx = Math.ceil(cyclePos / 3) - 1;
  const palaceIndex = Math.max(0, Math.min(7, idx));

  const winterSolstice = new Date(year, 11, 21);
  const summerSolstice = new Date(year, 5, 21);
  const dun: "Yang" | "Yin" =
    date >= winterSolstice || date < summerSolstice ? "Yang" : "Yin";

  const palaces = dun === "Yang" ? YANG_DUN_PALACES : YIN_DUN_PALACES;
  const palaceNumber = palaces[palaceIndex] ?? 1;

  return {
    year,
    accumulationYear: A,
    configurationNumber: n,
    palaceIndex,
    palaceNumber,
    dun,
  };
}
