import { describe, expect, it } from "vitest";
import { localizedNumeral } from "./numerals_localized";

describe("localizedNumeral", () => {
  it("renders Mandarin Chinese numerals 1..64", () => {
    expect(localizedNumeral(1, "pinyin")).toBe("一");
    expect(localizedNumeral(10, "pinyin")).toBe("十");
    expect(localizedNumeral(11, "pinyin")).toBe("十一");
    expect(localizedNumeral(20, "pinyin")).toBe("二十");
    expect(localizedNumeral(64, "pinyin")).toBe("六十四");
  });

  it("preserves Hanzi numerals for Sinosphere langs", () => {
    expect(localizedNumeral(15, "japanese")).toBe("十五");
    expect(localizedNumeral(15, "korean")).toBe("十五");
    expect(localizedNumeral(15, "taigi")).toBe("十五");
  });

  it("renders Vietnamese Sino-Vietnamese number names", () => {
    expect(localizedNumeral(1, "vietnamese")).toBe("Nhất");
    expect(localizedNumeral(10, "vietnamese")).toBe("Mười");
  });

  it("renders Devanagari digits for Hindi", () => {
    expect(localizedNumeral(1, "hindi")).toBe("१");
    expect(localizedNumeral(64, "hindi")).toBe("६४");
  });

  it("renders Thai digits", () => {
    expect(localizedNumeral(1, "thai")).toBe("๑");
    expect(localizedNumeral(64, "thai")).toBe("๖๔");
  });

  it("renders Lao digits", () => {
    expect(localizedNumeral(7, "lao")).toBe("໗");
  });

  it("renders Khmer digits", () => {
    expect(localizedNumeral(8, "khmer")).toBe("៨");
  });

  it("renders Burmese digits", () => {
    expect(localizedNumeral(9, "burmese")).toBe("၉");
  });

  it("renders Tibetan digits", () => {
    expect(localizedNumeral(3, "tibetan")).toBe("༣");
  });

  it("renders Arabic digits for Latin-script SE Asian languages", () => {
    expect(localizedNumeral(42, "indonesian")).toBe("42");
    expect(localizedNumeral(42, "balinese")).toBe("42");
    expect(localizedNumeral(42, "malay")).toBe("42");
    expect(localizedNumeral(42, "filipino")).toBe("42");
    expect(localizedNumeral(42, "mongolian")).toBe("42");
  });
});
