/**
 * BaZi + Nine Star fixture suite.
 * Locks in regression behavior of computeBirthProfile() against
 * lunar-typescript outputs as of 2026-05-01.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { computeBirthProfile } from "@/lib/personal/baziNineStar";

type Fixture = {
  label: string;
  input: {
    year: number;
    month: number;
    day: number;
    hour: number;
    minute?: number;
    second?: number;
  };
  expect: {
    bazi: { year: string; month: string; day: string; hour: string };
    nineStar: { year: string; month: string };
  };
};

const fixtures: Fixture[] = JSON.parse(
  readFileSync(resolve(__dirname, "fixtures/bazi.json"), "utf-8")
);

describe("BaZi + Nine Star fixtures", () => {
  for (const fx of fixtures) {
    it(`${fx.label} — pillars match`, () => {
      const r = computeBirthProfile(fx.input, 2);
      expect(r.bazi.pillars.year.ganZhi).toBe(fx.expect.bazi.year);
      expect(r.bazi.pillars.month.ganZhi).toBe(fx.expect.bazi.month);
      expect(r.bazi.pillars.day.ganZhi).toBe(fx.expect.bazi.day);
      expect(r.bazi.pillars.hour.ganZhi).toBe(fx.expect.bazi.hour);
    });

    it(`${fx.label} — nine star year/month match`, () => {
      const r = computeBirthProfile(fx.input, 2);
      expect(r.nineStar.year.number).toBe(fx.expect.nineStar.year);
      expect(r.nineStar.month.number).toBe(fx.expect.nineStar.month);
    });
  }
});

describe("BaZi cusp behavior", () => {
  it("Lichun crossing flips year branch from 卯 to 辰", () => {
    const before = computeBirthProfile(
      { year: 2000, month: 2, day: 4, hour: 2 },
      2
    );
    const after = computeBirthProfile(
      { year: 2000, month: 2, day: 5, hour: 2 },
      2
    );
    expect(before.bazi.pillars.year.zhi).toBe("卯");
    expect(after.bazi.pillars.year.zhi).toBe("辰");
  });
});
