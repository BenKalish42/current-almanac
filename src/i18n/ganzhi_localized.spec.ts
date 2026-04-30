import { describe, expect, it } from "vitest";
import {
  formatGanZhiScript,
  formatGanZhiRoman,
  getStemCell,
  getBranchCell,
} from "./ganzhi_localized";

describe("ganzhi getStemCell", () => {
  it("returns Hanzi + reading for stem 甲 across Sinosphere langs", () => {
    expect(getStemCell("甲", "japanese")?.script).toBe("甲");
    expect(getStemCell("甲", "japanese")?.roman).toBe("Kō");
    expect(getStemCell("甲", "korean")?.script).toBe("갑");
    expect(getStemCell("甲", "korean")?.roman).toBe("gap");
    expect(getStemCell("甲", "vietnamese")?.script).toBe("Giáp");
  });

  it("returns native script for non-Sinosphere langs", () => {
    expect(getStemCell("甲", "thai")?.script).toBe("เจี่ย");
    expect(getStemCell("甲", "hindi")?.script).toBe("ज्या");
    expect(getStemCell("甲", "tibetan")?.script).toBe("ཅཱ");
  });

  it("returns undefined for unknown stem char", () => {
    expect(getStemCell("X", "pinyin")).toBeUndefined();
  });
});

describe("ganzhi getBranchCell", () => {
  it("returns Hanzi readings for 子", () => {
    expect(getBranchCell("子", "korean")?.script).toBe("자");
    expect(getBranchCell("子", "korean")?.roman).toBe("ja");
    expect(getBranchCell("子", "vietnamese")?.script).toBe("Tý");
  });

  it("Thai script for 子", () => {
    expect(getBranchCell("子", "thai")?.script).toBe("จื่อ");
  });
});

describe("formatGanZhiScript", () => {
  it("composes 甲子 in Korean as 갑자", () => {
    expect(formatGanZhiScript("甲子", "korean")).toBe("갑자");
  });

  it("composes 甲子 in Japanese as 甲子 (Kanji preserved)", () => {
    expect(formatGanZhiScript("甲子", "japanese")).toBe("甲子");
  });

  it("composes 甲子 in Thai as เจี่ยจื่อ", () => {
    expect(formatGanZhiScript("甲子", "thai")).toBe("เจี่ยจื่อ");
  });

  it("falls back to original when char unknown", () => {
    expect(formatGanZhiScript("XY", "korean")).toBe("XY");
  });

  it("returns input for short / nullish", () => {
    expect(formatGanZhiScript(null, "korean")).toBe("");
    expect(formatGanZhiScript("", "korean")).toBe("");
    expect(formatGanZhiScript("甲", "korean")).toBe("甲");
  });
});

describe("formatGanZhiRoman", () => {
  it("composes 甲子 in Korean RR as 'gap ja'", () => {
    expect(formatGanZhiRoman("甲子", "korean")).toBe("gap ja");
  });

  it("composes 甲子 in Hepburn as 'Kō Shi'", () => {
    expect(formatGanZhiRoman("甲子", "japanese")).toBe("Kō Shi");
  });

  it("returns empty if no romanization available", () => {
    expect(formatGanZhiRoman("XY", "korean")).toBe("");
    expect(formatGanZhiRoman(null, "korean")).toBe("");
  });
});
