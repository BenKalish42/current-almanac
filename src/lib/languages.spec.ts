import { describe, expect, it } from "vitest";
import {
  DEFAULT_LANGUAGE,
  LANGUAGES,
  LANGUAGE_BY_CODE,
  getGroupedLanguages,
  isLanguageCode,
  migrateLegacyLanguage,
  romanizeCharForLanguage,
  type LanguageCode,
} from "./languages";

describe("language registry", () => {
  it("exposes exactly 8 languages", () => {
    expect(LANGUAGES).toHaveLength(8);
    expect(LANGUAGE_BY_CODE.size).toBe(8);
  });

  it("includes the original 4 Chinese languages", () => {
    for (const code of ["pinyin", "jyutping", "zhuyin", "taigi"] as LanguageCode[]) {
      expect(LANGUAGE_BY_CODE.has(code)).toBe(true);
    }
  });

  it("includes the 4 newly added languages", () => {
    for (const code of ["japanese", "korean", "tibetan", "hindi"] as LanguageCode[]) {
      expect(LANGUAGE_BY_CODE.has(code)).toBe(true);
    }
  });

  it("default language is pinyin", () => {
    expect(DEFAULT_LANGUAGE).toBe("pinyin");
  });

  it("each language defines hexagram field keys", () => {
    for (const def of LANGUAGES) {
      expect(def.hexagramFieldKey).toMatch(/_name$/);
      expect(def.hexagramTsField).toMatch(/Name$/);
      expect(def.label.length).toBeGreaterThan(0);
      expect(def.group.length).toBeGreaterThan(0);
    }
  });
});

describe("isLanguageCode", () => {
  it("accepts every registered code", () => {
    for (const def of LANGUAGES) expect(isLanguageCode(def.code)).toBe(true);
  });

  it("rejects unknown / non-string input", () => {
    expect(isLanguageCode("mandarin")).toBe(false);
    expect(isLanguageCode("klingon")).toBe(false);
    expect(isLanguageCode(undefined)).toBe(false);
    expect(isLanguageCode(null)).toBe(false);
    expect(isLanguageCode(42)).toBe(false);
  });
});

describe("migrateLegacyLanguage", () => {
  it("passes through valid codes", () => {
    for (const def of LANGUAGES) {
      expect(migrateLegacyLanguage(def.code)).toBe(def.code);
    }
  });

  it("maps legacy 'mandarin' → pinyin", () => {
    expect(migrateLegacyLanguage("mandarin")).toBe("pinyin");
  });

  it("maps legacy 'cantonese' → jyutping", () => {
    expect(migrateLegacyLanguage("cantonese")).toBe("jyutping");
  });

  it("falls back to default for unknown / nullish input", () => {
    expect(migrateLegacyLanguage("klingon")).toBe(DEFAULT_LANGUAGE);
    expect(migrateLegacyLanguage(undefined)).toBe(DEFAULT_LANGUAGE);
    expect(migrateLegacyLanguage(null)).toBe(DEFAULT_LANGUAGE);
    expect(migrateLegacyLanguage(123)).toBe(DEFAULT_LANGUAGE);
  });
});

describe("getGroupedLanguages", () => {
  it("returns at least two groups (Chinese + Other Asian)", () => {
    const groups = getGroupedLanguages();
    const labels = groups.map((g) => g.label);
    expect(labels).toContain("Chinese");
    expect(labels).toContain("Other Asian");
  });

  it("groups in registry order with non-empty items", () => {
    for (const group of getGroupedLanguages()) {
      expect(group.items.length).toBeGreaterThan(0);
    }
  });

  it("Chinese group contains the original 4", () => {
    const chinese = getGroupedLanguages().find((g) => g.label === "Chinese");
    expect(chinese).toBeDefined();
    const codes = chinese!.items.map((i) => i.code).sort();
    expect(codes).toEqual(["jyutping", "pinyin", "taigi", "zhuyin"]);
  });

  it("Other Asian group contains the new 4", () => {
    const asian = getGroupedLanguages().find((g) => g.label === "Other Asian");
    expect(asian).toBeDefined();
    const codes = asian!.items.map((i) => i.code).sort();
    expect(codes).toEqual(["hindi", "japanese", "korean", "tibetan"]);
  });
});

describe("romanizeCharForLanguage", () => {
  it("returns empty string for non-CJK characters", () => {
    expect(romanizeCharForLanguage("a", "pinyin")).toBe("");
    expect(romanizeCharForLanguage("?", "japanese")).toBe("");
  });

  it("returns a non-empty pinyin for a CJK char", () => {
    expect(romanizeCharForLanguage("人", "pinyin").length).toBeGreaterThan(0);
  });

  it("falls back to pinyin for languages without a bundled romanizer", () => {
    // taigi/japanese/korean/tibetan/hindi all share the pinyin fallback
    const py = romanizeCharForLanguage("人", "pinyin");
    expect(romanizeCharForLanguage("人", "taigi")).toBe(py);
    expect(romanizeCharForLanguage("人", "japanese")).toBe(py);
    expect(romanizeCharForLanguage("人", "korean")).toBe(py);
    expect(romanizeCharForLanguage("人", "tibetan")).toBe(py);
    expect(romanizeCharForLanguage("人", "hindi")).toBe(py);
  });
});
