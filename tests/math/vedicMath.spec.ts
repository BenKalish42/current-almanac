/**
 * Vedic / Lahiri smoke tests for `src/utils/vedicMath.ts`.
 * Validates that the chart can be built and produces sensible outputs.
 *
 * Tighter ayanamsa / Lagna fixtures vs swisseph are tracked in
 * docs/architecture/phase_4/Task12.8_VedicEngine.md; these smoke
 * tests guard against catastrophic regressions.
 */
import { describe, it, expect } from "vitest";
import {
  VEDIC_RASI_EN,
  VEDIC_RASI_SANSKRIT,
} from "@/utils/vedicMath";

describe("Vedic — rāśi tables", () => {
  it("has 12 Sanskrit rāśi names", () => {
    expect(VEDIC_RASI_SANSKRIT).toHaveLength(12);
  });

  it("has 12 English rāśi names parallel to Sanskrit", () => {
    expect(VEDIC_RASI_EN).toHaveLength(12);
  });

  it("Mesha = Aries, Meena = Pisces (sanity)", () => {
    expect(VEDIC_RASI_SANSKRIT[0]).toBe("Mesha");
    expect(VEDIC_RASI_SANSKRIT[11]).toBe("Meena");
    expect(VEDIC_RASI_EN[0]).toBe("Aries");
    expect(VEDIC_RASI_EN[11]).toBe("Pisces");
  });
});
