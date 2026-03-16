import { describe, it, expect } from "vitest";
import {
  calculateFormulaRating,
  type HerbForRating,
} from "./heuristicRater";

describe("calculateFormulaRating", () => {
  it("scores Warm/Sweet Qi herb and Cold/Bitter Jing herb with expected mathematical logic", () => {
    const warmSweetHerb: HerbForRating = {
      id: "herb_qi_001",
      properties: {
        temperature: "Warm",
        flavor: ["Sweet"],
        meridians: ["Spleen", "Stomach"],
      },
      actions: ["Tonifies Qi and strengthens Spleen"],
    };

    const coldBitterHerb: HerbForRating = {
      id: "herb_jing_001",
      properties: {
        temperature: "Cold",
        flavor: ["Bitter"],
        meridians: ["Liver", "Kidney"],
      },
      actions: ["Nourishes Blood and clears Heat"],
    };

    const result = calculateFormulaRating([warmSweetHerb, coldBitterHerb], {});

    // Warm/Sweet herb: Qi points from \bqi\b (+3), Spleen/Stomach (+2), Sweet+Warm (+1) = 6 raw
    // Cold/Bitter herb: Jing from nourishes (+2), kidney (+1) = 3 raw
    // Total raw: jing=3, qi=6, shen=0
    // Scale: maxRaw=6, scale=100/6 -> jingScore=50, qiScore=100, shenScore=0
    expect(result.jingScore).toBe(50);
    expect(result.qiScore).toBe(100);
    expect(result.shenScore).toBe(0);
    expect(result.primaryEffect).toBe("Primary Qi Tonic");
  });
});
