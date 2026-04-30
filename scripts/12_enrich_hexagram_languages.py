#!/usr/bin/env python3
"""
Task 12.4: Inject per-hexagram language readings into seed_hexagrams.json.

Adds four new fields to each of the 64 hexagrams:
  - japanese_name : Sino-Japanese on'yomi (Romaji)        e.g. "Ken"
  - korean_name   : Sino-Korean Hangul + Revised Roman.   e.g. "건 (geon)"
  - tibetan_name  : Phonetic transliteration of pinyin    e.g. "ཁྱན"
  - hindi_name    : Phonetic transliteration of pinyin    e.g. "छ्येन"

Japanese & Korean are deterministic well-documented mappings of the hex
characters' classical readings. Tibetan & Hindi are best-effort phonetic
spellings of the Mandarin pinyin in the target script — we have no classical
Yi-Jing transliteration tradition for those languages and we make this clear
in the architecture doc (Task12.4_LanguageEngine.md).

Idempotent: re-running on already-enriched data overwrites cleanly.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = PROJECT_ROOT / "src" / "data" / "seed_hexagrams.json"
MIRROR_PATH = PROJECT_ROOT / "data" / "output" / "seed_hexagrams.json"


# ---------------------------------------------------------------------------
# Per-hexagram readings
# ---------------------------------------------------------------------------
#
# Authoritative sources:
#   - Japanese: standard Sino-Japanese on'yomi for the hex's hanzi as used in
#     Japanese Yi-Jing scholarship (易経 Ekikyō). Two-char names render as a
#     single Romaji compound.
#   - Korean : standard Sino-Korean Hangul + Revised Romanization (RR).
#   - Tibetan/Hindi: phonetic transliteration of the Mandarin pinyin syllable
#     into the target script (best-effort; not classically attested).
#
# Each tuple is (japanese_romaji, korean_hangul_rr, tibetan, hindi)
HEX_READINGS: dict[int, tuple[str, str, str, str]] = {
    1:  ("Ken",       "건 (geon)",     "ཁྱན",         "छ्येन"),
    2:  ("Kon",       "곤 (gon)",      "ཁུན",          "खुन"),
    3:  ("Chun",      "준 (jun)",      "ཀྲུན",         "जुन"),
    4:  ("Mō",        "몽 (mong)",     "མུང",          "मेङ"),
    5:  ("Ju",        "수 (su)",       "ཤུའུ",         "श्यू"),
    6:  ("Shō",       "송 (song)",     "སུང",          "सोङ"),
    7:  ("Shi",       "사 (sa)",       "ཤི",           "शी"),
    8:  ("Hi",        "비 (bi)",       "པི",           "पी"),
    9:  ("Shōchiku",  "소축 (sochuk)", "ཤའོ་ཁྲུ",      "श्याओ छू"),
    10: ("Ri",        "리 (ri)",       "ལུའུ",         "ल्यू"),
    11: ("Tai",       "태 (tae)",      "ཐའེ",          "ताई"),
    12: ("Hi",        "비 (bi)",       "ཕི",           "पी"),
    13: ("Dōjin",     "동인 (dongin)", "ཐུང་རན",      "थोङ रन"),
    14: ("Daiyū",     "대유 (daeyu)",  "ཏ་ཡའོ",       "ता योऊ"),
    15: ("Ken",       "겸 (gyeom)",    "ཆཱན",         "छ्येन"),
    16: ("Yo",        "예 (ye)",       "ཡུའུ",         "यू"),
    17: ("Zui",       "수 (su)",       "སུའེ",         "सुई"),
    18: ("Ko",        "고 (go)",       "ཀུའུ",         "गू"),
    19: ("Rin",       "림 (rim)",      "ལིན",          "लिन"),
    20: ("Kan",       "관 (gwan)",     "ཀུཨན",        "गुआन"),
    21: ("Zegō",      "서합 (seohap)", "ཤི་ཧུའེ",      "श्र हे"),
    22: ("Hi",        "비 (bi)",       "པི",           "पी"),
    23: ("Haku",      "박 (bak)",      "པོ",           "पो"),
    24: ("Fuku",      "복 (bok)",      "ཕུའུ",         "फू"),
    25: ("Mubō",      "무망 (mumang)", "འུ་ཝང",       "वू वाङ"),
    26: ("Daichiku",  "대축 (daechuk)","ཏ་ཁྲུ",        "ता छू"),
    27: ("I",         "이 (i)",        "ཡི",           "यी"),
    28: ("Daika",     "대과 (daegwa)", "ཏ་ཀོ",         "ता क्वो"),
    29: ("Kan",       "감 (gam)",      "ཁན",          "खान"),
    30: ("Ri",        "리 (ri)",       "ལི",           "ली"),
    31: ("Kan",       "함 (ham)",      "ཤན",          "श्येन"),
    32: ("Kō",        "항 (hang)",     "ཧང",          "हङ"),
    33: ("Ton",       "둔 (dun)",      "ཏུན",          "तुन"),
    34: ("Daisō",     "대장 (daejang)","ཏ་ཀྲུཨང",     "ता च्वाङ"),
    35: ("Shin",      "진 (jin)",      "ཅིན",          "जिन"),
    36: ("Meii",      "명이 (myeongi)","མིང་ཡི",      "मिङ यी"),
    37: ("Kajin",     "가인 (gain)",   "ཅཱ་རན",       "ज्या रन"),
    38: ("Kei",       "규 (gyu)",      "ཁུའེ",         "खुई"),
    39: ("Ken",       "건 (geon)",     "ཅཱན",         "ज्येन"),
    40: ("Kai",       "해 (hae)",      "ཤེ",           "श्ये"),
    41: ("Son",       "손 (son)",      "སུན",          "सुन"),
    42: ("Eki",       "익 (ik)",       "ཡི",           "यी"),
    43: ("Kai",       "쾌 (kwae)",     "ཀུཨའེ",       "गुआई"),
    44: ("Kō",        "구 (gu)",       "ཀོའུ",         "गोऊ"),
    45: ("Sui",       "췌 (chwe)",     "ཚུའེ",         "छुई"),
    46: ("Shō",       "승 (seung)",    "ཤང",          "शेङ"),
    47: ("Kon",       "곤 (gon)",      "ཁུན",          "खुन"),
    48: ("Sei",       "정 (jeong)",    "ཅིང",          "जिङ"),
    49: ("Kaku",      "혁 (hyeok)",    "ཀེ",           "गे"),
    50: ("Tei",       "정 (jeong)",    "ཏིང",          "तिङ"),
    51: ("Shin",      "진 (jin)",      "ཀྲན",          "जन"),
    52: ("Gon",       "간 (gan)",      "ཀན",          "गन"),
    53: ("Zen",       "점 (jeom)",     "ཅཱན",         "ज्येन"),
    54: ("Kimai",     "귀매 (gwimae)", "ཀུའེ་མེའེ",   "गुई मे"),
    55: ("Hō",        "풍 (pung)",     "ཕིང",          "फेङ"),
    56: ("Ryo",       "려 (ryeo)",     "ལུའུ",         "ल्यू"),
    57: ("Son",       "손 (son)",      "ཤུན",          "श्युन"),
    58: ("Da",        "태 (tae)",      "ཏུའེ",         "तुई"),
    59: ("Kan",       "환 (hwan)",     "ཧུཨན",        "हुआन"),
    60: ("Setsu",     "절 (jeol)",     "ཅཱ",           "ज्ये"),
    61: ("Chūfu",     "중부 (jungbu)", "ཀྲུང་ཕུའུ",   "जोङ फू"),
    62: ("Shōka",     "소과 (sogwa)",  "ཤའོ་ཀོ",      "श्याओ क्वो"),
    63: ("Kisei",     "기제 (gije)",   "ཅི་ཅི",        "जी जी"),
    64: ("Misei",     "미제 (mije)",   "ཝེའེ་ཅི",      "वे जी"),
}


def main() -> int:
    if len(HEX_READINGS) != 64:
        raise SystemExit(f"Expected 64 readings, got {len(HEX_READINGS)}")

    with SEED_PATH.open(encoding="utf-8") as f:
        hexes = json.load(f)

    if len(hexes) != 64:
        raise SystemExit(f"Expected 64 hexagrams in {SEED_PATH}, got {len(hexes)}")

    for h in hexes:
        hex_id = int(h["id"])
        readings = HEX_READINGS.get(hex_id)
        if not readings:
            raise SystemExit(f"No readings for hexagram {hex_id}")
        jp, ko, ti, hi = readings
        h["japanese_name"] = jp
        h["korean_name"] = ko
        h["tibetan_name"] = ti
        h["hindi_name"] = hi

    SEED_PATH.write_text(
        json.dumps(hexes, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {SEED_PATH} with japanese/korean/tibetan/hindi names for all 64 hexagrams.")

    if MIRROR_PATH.exists():
        MIRROR_PATH.write_text(
            json.dumps(hexes, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Mirrored to {MIRROR_PATH}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
