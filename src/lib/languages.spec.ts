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
  it("exposes exactly 18 languages", () => {
    expect(LANGUAGES).toHaveLength(18);
    expect(LANGUAGE_BY_CODE.size).toBe(18);
  });

  it("includes the 4 Chinese languages", () => {
    for (const code of ["pinyin", "jyutping", "zhuyin", "taigi"] as LanguageCode[]) {
      expect(LANGUAGE_BY_CODE.has(code)).toBe(true);
    }
  });

  it("includes the 5 'Other Asian' languages", () => {
    for (const code of [
      "japanese",
      "korean",
      "tibetan",
      "hindi",
      "mongolian",
    ] as LanguageCode[]) {
      expect(LANGUAGE_BY_CODE.has(code)).toBe(true);
    }
  });

  it("includes the 9 Southeast Asian languages", () => {
    for (const code of [
      "thai",
      "vietnamese",
      "indonesian",
      "balinese",
      "malay",
      "filipino",
      "khmer",
      "lao",
      "burmese",
    ] as LanguageCode[]) {
      expect(LANGUAGE_BY_CODE.has(code)).toBe(true);
    }
  });

  it("default language is pinyin", () => {
    expect(DEFAULT_LANGUAGE).toBe("pinyin");
  });

  it("each language defines hexagram field keys, romanization standard, and native script", () => {
    for (const def of LANGUAGES) {
      expect(def.hexagramFieldKey).toMatch(/_name$/);
      expect(def.hexagramTsField).toMatch(/Name$/);
      expect(def.label.length).toBeGreaterThan(0);
      expect(def.group.length).toBeGreaterThan(0);
      expect(def.romanizationStandard.length).toBeGreaterThan(0);
      expect(def.nativeScript.length).toBeGreaterThan(0);
    }
  });

  it("uses the official romanization standards for Sinosphere languages", () => {
    expect(LANGUAGE_BY_CODE.get("japanese")!.romanizationStandard).toBe("Hepburn");
    expect(LANGUAGE_BY_CODE.get("korean")!.romanizationStandard).toBe(
      "Revised Romanization"
    );
    expect(LANGUAGE_BY_CODE.get("tibetan")!.romanizationStandard).toBe("Wylie");
    expect(LANGUAGE_BY_CODE.get("hindi")!.romanizationStandard).toBe("Hunterian");
    expect(LANGUAGE_BY_CODE.get("thai")!.romanizationStandard).toBe("RTGS");
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
  it("returns three groups (Chinese, Other Asian, Southeast Asian)", () => {
    const groups = getGroupedLanguages();
    const labels = groups.map((g) => g.label);
    expect(labels).toContain("Chinese");
    expect(labels).toContain("Other Asian");
    expect(labels).toContain("Southeast Asian");
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

  it("Other Asian group contains 5 langs (incl. Mongolian)", () => {
    const asian = getGroupedLanguages().find((g) => g.label === "Other Asian");
    expect(asian).toBeDefined();
    const codes = asian!.items.map((i) => i.code).sort();
    expect(codes).toEqual([
      "hindi",
      "japanese",
      "korean",
      "mongolian",
      "tibetan",
    ]);
  });

  it("Southeast Asian group contains 9 langs", () => {
    const sea = getGroupedLanguages().find((g) => g.label === "Southeast Asian");
    expect(sea).toBeDefined();
    const codes = sea!.items.map((i) => i.code).sort();
    expect(codes).toEqual([
      "balinese",
      "burmese",
      "filipino",
      "indonesian",
      "khmer",
      "lao",
      "malay",
      "thai",
      "vietnamese",
    ]);
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

  it("falls back to pinyin for all languages without a bundled romanizer", () => {
    const py = romanizeCharForLanguage("人", "pinyin");
    for (const code of [
      "taigi",
      "japanese",
      "korean",
      "tibetan",
      "hindi",
      "thai",
      "vietnamese",
      "indonesian",
      "balinese",
      "malay",
      "filipino",
      "khmer",
      "lao",
      "burmese",
      "mongolian",
    ] as LanguageCode[]) {
      expect(romanizeCharForLanguage("人", code)).toBe(py);
    }
  });
});
