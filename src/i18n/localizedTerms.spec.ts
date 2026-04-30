import { describe, expect, it } from "vitest";
import {
  hexagramScripts,
  hexagramRomans,
  hexagramHanzi,
  hexagramHanziTraditional,
  formulaScripts,
  formulaRomans,
  herbScripts,
  herbRomans,
} from "./localizedTerms";

describe("hexagramScripts / hexagramRomans", () => {
  it("returns per-language scripts for hex 1 (乾)", () => {
    const scripts = hexagramScripts(1);
    expect(scripts.pinyin).toBe("乾");
    expect(scripts.korean).toBe("건");
    expect(scripts.hindi).toBe("छ्येन");
    expect(scripts.thai).toBe("เฉียน");
    expect(scripts.vietnamese).toBe("Càn");
  });

  it("returns per-language romanizations for hex 1", () => {
    const roman = hexagramRomans(1);
    expect(roman.pinyin).toBe("Qián");
    expect(roman.japanese).toBe("Ken");
    expect(roman.korean).toBe("geon");
    expect(roman.thai).toBe("chian");
  });

  it("returns empty maps for unknown / null hex", () => {
    expect(hexagramScripts(null)).toEqual({});
    expect(hexagramScripts(undefined)).toEqual({});
    expect(hexagramScripts(999)).toEqual({});
    expect(hexagramRomans(0)).toEqual({});
  });
});

describe("hexagramHanzi", () => {
  it("returns simplified Hanzi for known hex", () => {
    expect(hexagramHanzi(1)).toBe("乾");
    expect(hexagramHanzi(2)).toBe("坤");
  });

  it("returns traditional for traditional getter", () => {
    expect(hexagramHanziTraditional(6)).toBe("訟");
    expect(hexagramHanziTraditional(7)).toBe("師");
  });

  it("returns empty string for null / unknown", () => {
    expect(hexagramHanzi(null)).toBe("");
    expect(hexagramHanzi(999)).toBe("");
    expect(hexagramHanziTraditional(undefined)).toBe("");
  });
});

describe("formulaScripts / formulaRomans", () => {
  const formula = {
    translations: {
      pinyin: { script: "六味地黄丸", roman: "Liu Wei Di Huang Wan" },
      japanese: { script: "六味地黄丸", roman: "Rokumijiōgan" },
      korean: { script: "육미지황환", roman: "Yukmijihwanghwan" },
      thai: { script: "หลิวเว่ยตี้หฺวงหฺวาน", roman: "liu wei ti huang wan" },
    },
  };

  it("extracts per-language scripts", () => {
    expect(formulaScripts(formula).pinyin).toBe("六味地黄丸");
    expect(formulaScripts(formula).korean).toBe("육미지황환");
  });

  it("extracts per-language romans", () => {
    expect(formulaRomans(formula).japanese).toBe("Rokumijiōgan");
    expect(formulaRomans(formula).thai).toBe("liu wei ti huang wan");
  });

  it("returns empty for missing translations", () => {
    expect(formulaScripts(null)).toEqual({});
    expect(formulaScripts({})).toEqual({});
    expect(formulaRomans(undefined)).toEqual({});
  });
});

describe("herbScripts / herbRomans", () => {
  const herb = {
    linguistics: {
      translations: {
        pinyin: { script: "紫金牛", roman: "Ǎi Dì Chá" },
        thai: { script: "อ้ายตี้ฉา", roman: "ai ti cha" },
        korean: { script: "紫金牛", roman: "Ǎi Dì Chá" },
      },
    },
  };

  it("extracts per-language scripts", () => {
    expect(herbScripts(herb).pinyin).toBe("紫金牛");
    expect(herbScripts(herb).thai).toBe("อ้ายตี้ฉา");
  });

  it("extracts per-language romans", () => {
    expect(herbRomans(herb).thai).toBe("ai ti cha");
  });

  it("returns empty for missing translations", () => {
    expect(herbScripts({})).toEqual({});
    expect(herbScripts(null)).toEqual({});
    expect(herbRomans({ linguistics: {} })).toEqual({});
  });
});
