#!/usr/bin/env python3
"""
Task 12.5 Phase F — localize classical formula names per language.

Updates `src/data/formulas.json` (used by FormulaLibrary) and
`src/data/seed_formulas.json` (used by alchemy seeds) to add a
`translations` field per formula:

  translations: {
    [lang]: { script: <native-script>, roman: <official-romanization> }
  }

Sinosphere languages compose `script` and `roman` from a per-character
Hanzi reading table (Sino-Japanese on'yomi, Sino-Korean Hangul/RR,
Sino-Vietnamese Hán-Việt). Non-Sinosphere languages do phonetic
transliteration of the Mandarin pinyin syllables into the language's
native script + the language's official romanization standard.

Idempotent: re-running overwrites cleanly.
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FORMULAS_PATH = PROJECT_ROOT / "src" / "data" / "formulas.json"
SEED_FORMULAS_PATH = PROJECT_ROOT / "src" / "data" / "seed_formulas.json"
SEED_FORMULAS_MIRROR = PROJECT_ROOT / "data" / "output" / "seed_formulas.json"

# --------------------------------------------------------------------------
# Per-Hanzi reading dictionary for the chars that appear in our formulas.
# The set is small in practice (formulas.json: 7 chars; seed_formulas.json
# has no CJK directly but we synthesize from the romanized name).
#
# Entries cover the core TCM-formula vocabulary and are easily extensible.
# --------------------------------------------------------------------------

# Format: hanzi -> dict of fields per language. We only fill what's needed;
# missing chars fall back to the canonical Hanzi.
HANZI_READINGS: dict[str, dict[str, dict[str, str]]] = {
    "六": {
        "pinyin": {"script": "六", "roman": "Liù"},
        "japanese": {"script": "六", "roman": "Roku"},
        "korean": {"script": "육", "roman": "yuk"},
        "vietnamese": {"script": "Lục", "roman": "Lục"},
    },
    "味": {
        "pinyin": {"script": "味", "roman": "Wèi"},
        "japanese": {"script": "味", "roman": "Mi"},
        "korean": {"script": "미", "roman": "mi"},
        "vietnamese": {"script": "Vị", "roman": "Vị"},
    },
    "地": {
        "pinyin": {"script": "地", "roman": "Dì"},
        "japanese": {"script": "地", "roman": "Ji"},
        "korean": {"script": "지", "roman": "ji"},
        "vietnamese": {"script": "Địa", "roman": "Địa"},
    },
    "黄": {
        "pinyin": {"script": "黄", "roman": "Huáng"},
        "japanese": {"script": "黄", "roman": "Ō"},
        "korean": {"script": "황", "roman": "hwang"},
        "vietnamese": {"script": "Hoàng", "roman": "Hoàng"},
    },
    "丸": {
        "pinyin": {"script": "丸", "roman": "Wán"},
        "japanese": {"script": "丸", "roman": "Gan"},
        "korean": {"script": "환", "roman": "hwan"},
        "vietnamese": {"script": "Hoàn", "roman": "Hoàn"},
    },
    "保": {
        "pinyin": {"script": "保", "roman": "Bǎo"},
        "japanese": {"script": "保", "roman": "Ho"},
        "korean": {"script": "보", "roman": "bo"},
        "vietnamese": {"script": "Bảo", "roman": "Bảo"},
    },
    "和": {
        "pinyin": {"script": "和", "roman": "Hé"},
        "japanese": {"script": "和", "roman": "Wa"},
        "korean": {"script": "화", "roman": "hwa"},
        "vietnamese": {"script": "Hòa", "roman": "Hòa"},
    },
}

# All registry languages.
ALL_LANGUAGES: list[str] = [
    "pinyin", "jyutping", "zhuyin", "taigi",
    "japanese", "korean", "tibetan", "hindi", "mongolian",
    "thai", "vietnamese", "indonesian", "balinese",
    "malay", "filipino", "khmer", "lao", "burmese",
]

# Languages where each Hanzi has a deterministic Sino reading; we compose
# multi-char names by concatenating per-char readings.
SINOSPHERE_COMPOSE: set[str] = {"japanese", "korean", "vietnamese"}

# --------------------------------------------------------------------------
# Pinyin syllable -> per-language phonetic transliteration.
# Used for non-Sinosphere languages and as the fallback for missing chars.
# Keyed by lowercase pinyin syllable (no tone marks).
# --------------------------------------------------------------------------

# Each entry: syllable -> dict of language -> { script, roman }.
SYLLABLE_PHONETICS: dict[str, dict[str, dict[str, str]]] = {
    # Common TCM/formula syllables. Each entry maps the no-tone pinyin
    # syllable (e.g. "gui") to per-language script + roman.
    # Languages absent from a syllable fall back to phonetic Latin (the
    # syllable itself, capitalized).
    "liu":   {"thai": {"script": "หลิว", "roman": "liu"},  "khmer": {"script": "លីវ", "roman": "liv"},  "lao": {"script": "ລິວ", "roman": "liu"},  "burmese": {"script": "လျု", "roman": "lyu"},  "tibetan": {"script": "ལིའུ", "roman": "li'u"},  "hindi": {"script": "ल्यू", "roman": "lyu"},  "mongolian": {"script": "Лю", "roman": "Lyu"}},
    "wei":   {"thai": {"script": "เว่ย", "roman": "wei"},  "khmer": {"script": "វេ", "roman": "ve"},     "lao": {"script": "ເວ່ຍ", "roman": "wei"}, "burmese": {"script": "ဝေး", "roman": "we"},  "tibetan": {"script": "ཝེའེ", "roman": "we'e"},   "hindi": {"script": "वे", "roman": "we"},     "mongolian": {"script": "Вэй", "roman": "Wei"}},
    "di":    {"thai": {"script": "ตี้", "roman": "ti"},   "khmer": {"script": "ទី", "roman": "ti"},    "lao": {"script": "ຕີ້", "roman": "ti"},   "burmese": {"script": "တီ", "roman": "ti"},   "tibetan": {"script": "ཏི", "roman": "ti"},     "hindi": {"script": "ती", "roman": "ti"},      "mongolian": {"script": "Ди", "roman": "Di"}},
    "huang": {"thai": {"script": "หฺวง", "roman": "huang"}, "khmer": {"script": "ហួង", "roman": "huong"}, "lao": {"script": "ຫວງ", "roman": "huang"}, "burmese": {"script": "ဟွမ်း", "roman": "hwan"}, "tibetan": {"script": "ཧུཨང", "roman": "hu'ang"}, "hindi": {"script": "हुआङ", "roman": "huang"}, "mongolian": {"script": "Хуан", "roman": "Khuan"}},
    "wan":   {"thai": {"script": "หฺวาน", "roman": "wan"}, "khmer": {"script": "វាន", "roman": "vean"}, "lao": {"script": "ຫວານ", "roman": "wan"}, "burmese": {"script": "ဝမ်း", "roman": "wan"}, "tibetan": {"script": "ཝན", "roman": "wan"},      "hindi": {"script": "वान", "roman": "wan"},    "mongolian": {"script": "Ван", "roman": "Wan"}},
    "bao":   {"thai": {"script": "เป่า", "roman": "bao"}, "khmer": {"script": "បាវ", "roman": "bav"}, "lao": {"script": "ເປົ່າ", "roman": "bao"}, "burmese": {"script": "ဘောင်း", "roman": "baung"}, "tibetan": {"script": "པའོ", "roman": "pa'o"},  "hindi": {"script": "बाओ", "roman": "bao"},    "mongolian": {"script": "Бао", "roman": "Bao"}},
    "he":    {"thai": {"script": "เหอ", "roman": "he"},   "khmer": {"script": "ហឺ", "roman": "heu"},  "lao": {"script": "ເຫິ", "roman": "he"},   "burmese": {"script": "ဟေး", "roman": "he"},   "tibetan": {"script": "ཧེ", "roman": "he"},      "hindi": {"script": "हे", "roman": "he"},      "mongolian": {"script": "Хэ", "roman": "Khe"}},
    "gui":   {"thai": {"script": "กุ้ย", "roman": "kui"}, "khmer": {"script": "គុយ", "roman": "kuy"}, "lao": {"script": "ກຸ່ຍ", "roman": "kuy"}, "burmese": {"script": "ဂွေး", "roman": "gwe"}, "tibetan": {"script": "ཀུའེ", "roman": "ku'e"},  "hindi": {"script": "गुई", "roman": "gui"},    "mongolian": {"script": "Гуй", "roman": "Guy"}},
    "zhi":   {"thai": {"script": "จื๋อ", "roman": "chue"}, "khmer": {"script": "ជឺ", "roman": "cheu"}, "lao": {"script": "ຈື່", "roman": "chue"}, "burmese": {"script": "ကြိ", "roman": "kyi"}, "tibetan": {"script": "ཀྲིི", "roman": "kri"},   "hindi": {"script": "श्र", "roman": "shr"},   "mongolian": {"script": "Жи", "roman": "Ji"}},
    "tang":  {"thai": {"script": "ทัง", "roman": "thang"}, "khmer": {"script": "ថាង", "roman": "thang"}, "lao": {"script": "ທັງ", "roman": "thang"}, "burmese": {"script": "ထန်း", "roman": "than"}, "tibetan": {"script": "ཐང", "roman": "thang"},   "hindi": {"script": "थाङ", "roman": "thang"},  "mongolian": {"script": "Тан", "roman": "Tan"}},
}


def split_pinyin(name: str) -> list[str]:
    """Split a Latin pinyin string like 'Liu Wei Di Huang Wan' into syllables."""
    # Strip tone marks and split on whitespace; lowercase.
    no_tones = re.sub(
        r"[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛ]",
        lambda m: {
            "ā":"a","á":"a","ǎ":"a","à":"a","ē":"e","é":"e","ě":"e","è":"e",
            "ī":"i","í":"i","ǐ":"i","ì":"i","ō":"o","ó":"o","ǒ":"o","ò":"o",
            "ū":"u","ú":"u","ǔ":"u","ù":"u","ǖ":"u","ǘ":"u","ǚ":"u","ǜ":"u",
        }.get(m.group(0), m.group(0)),
        name.lower(),
    )
    return [s for s in no_tones.split() if s]


def syllable_to_lang(syl: str, lang: str) -> dict[str, str]:
    """Per-syllable script/roman lookup for non-Sinosphere languages.
    Falls back to the syllable itself in Latin for everything missing."""
    cell = SYLLABLE_PHONETICS.get(syl, {}).get(lang)
    if cell:
        return cell
    cap = syl.capitalize()
    return {"script": cap, "roman": cap}


def localize_formula_name(hanzi: str, pinyin: str) -> dict[str, dict[str, str]]:
    """Build translations[lang] = {script, roman} for one formula."""
    out: dict[str, dict[str, str]] = {}

    # Sinosphere langs compose per-Hanzi readings if hanzi is provided.
    syllables = split_pinyin(pinyin)

    for lang in ALL_LANGUAGES:
        if lang == "pinyin":
            out[lang] = {"script": hanzi, "roman": pinyin}
            continue
        if lang in {"jyutping", "zhuyin", "taigi"}:
            # Keep traditional Hanzi for script slot; use pinyin for roman until
            # a per-character romanization library is available. (Same fallback
            # convention as the existing pronunciation system.)
            out[lang] = {"script": hanzi, "roman": pinyin}
            continue

        if lang in SINOSPHERE_COMPOSE and hanzi:
            scripts: list[str] = []
            romans: list[str] = []
            ok = True
            for ch in hanzi:
                cell = HANZI_READINGS.get(ch, {}).get(lang)
                if not cell:
                    ok = False
                    break
                scripts.append(cell["script"])
                romans.append(cell["roman"])
            if ok:
                # Korean: join with no separator (e.g. 育味地黃丸 -> 육미지황환)
                # Japanese: same — single compound (Rokumijiōgan)
                # Vietnamese: space between syllables (Lục Vị Địa Hoàng Hoàn)
                if lang == "vietnamese":
                    out[lang] = {
                        "script": " ".join(scripts),
                        "roman": " ".join(romans),
                    }
                else:
                    out[lang] = {
                        "script": "".join(scripts),
                        "roman": "".join(romans).lower().capitalize(),
                    }
                continue

        # Latin-script SE Asian: phonetic Latin (= pinyin)
        if lang in {"indonesian", "balinese", "malay", "filipino"}:
            out[lang] = {"script": pinyin, "roman": pinyin}
            continue

        # Non-Sinosphere with native script: compose from syllable phonetics
        scripts = []
        romans = []
        for syl in syllables:
            cell = syllable_to_lang(syl, lang)
            scripts.append(cell["script"])
            romans.append(cell["roman"])
        sep_script = "" if lang in {"thai", "khmer", "lao", "burmese", "tibetan"} else " "
        sep_roman = " "
        out[lang] = {
            "script": sep_script.join(scripts),
            "roman": sep_roman.join(romans),
        }

    return out


def main() -> int:
    # 1. formulas.json (FormulaLibrary)
    if FORMULAS_PATH.exists():
        with FORMULAS_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        for formula in data.get("classical_formulas", []):
            hanzi = formula.get("name_hanzi", "") or ""
            pinyin = formula.get("name_pinyin", "") or ""
            formula["translations"] = localize_formula_name(hanzi, pinyin)
        FORMULAS_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Updated {FORMULAS_PATH} ({len(data['classical_formulas'])} formulas)")

    # 2. seed_formulas.json (alchemy seeds)
    if SEED_FORMULAS_PATH.exists():
        with SEED_FORMULAS_PATH.open(encoding="utf-8") as f:
            seeds = json.load(f)
        # seed_formulas has no name_hanzi; use the pinyin_name (Latin) as
        # both source for syllable phonetics; script slot in Sinosphere
        # langs falls back to pinyin (no canonical Hanzi available here).
        for f in seeds:
            pinyin = f.get("pinyin_name", "") or ""
            # No hanzi = pure phonetic transliteration for everything.
            f["translations"] = localize_formula_name("", pinyin)
        SEED_FORMULAS_PATH.write_text(
            json.dumps(seeds, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Updated {SEED_FORMULAS_PATH} ({len(seeds)} formulas)")
        if SEED_FORMULAS_MIRROR.parent.exists():
            SEED_FORMULAS_MIRROR.write_text(
                json.dumps(seeds, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"Mirrored to {SEED_FORMULAS_MIRROR}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
