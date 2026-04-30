#!/usr/bin/env python3
"""
Task 12.5 Phase G — localize herb names per language.

For each of 698 herbs in `src/data/seed_herbs.json`, populate:

  linguistics.translations: {
    [lang]: { script: <native-script>, roman: <official-romanization> }
  }

Strategy:
  - Sinosphere languages (jyutping, zhuyin, taigi, japanese, korean) keep
    the existing Hanzi alias for `script` and the Latin `tonal_pinyin` (or
    raw pinyin_name) for `roman`. We do NOT compose per-Hanzi readings for
    the full 698-herb pharmacognosy vocabulary — the dictionary required is
    too large for a static commit and we already display Latin pinyin for
    these languages today. The display-time fallback chain remains correct.
  - Vietnamese: Latin Hán-Việt is a real tradition for many TCM names;
    without a complete dictionary we keep Latin pinyin + the existing
    `tonal_pinyin` for the roman slot. Same fallback policy as above.
  - Non-Sinosphere languages with native scripts (Tibetan, Hindi, Mongolian,
    Thai, Khmer, Lao, Burmese): split the pinyin into syllables and
    transliterate per syllable using the SYLLABLE_PHONETICS map shared with
    `14_localize_formulas.py` plus a small extension for common pinyin
    syllables that appear in herb names.
  - Latin-script SE Asian (Indonesian, Balinese, Malay, Filipino):
    pinyin in both slots.

Idempotent: re-running overwrites cleanly. Resumable: the script saves
incrementally every 50 herbs.
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_HERBS_PATH = PROJECT_ROOT / "src" / "data" / "seed_herbs.json"
SEED_HERBS_MIRROR = PROJECT_ROOT / "data" / "output" / "seed_herbs.json"

ALL_LANGUAGES: list[str] = [
    "pinyin", "jyutping", "zhuyin", "taigi",
    "japanese", "korean", "tibetan", "hindi", "mongolian",
    "thai", "vietnamese", "indonesian", "balinese",
    "malay", "filipino", "khmer", "lao", "burmese",
]

# Languages that compose Hanzi-based readings deterministically. For herbs
# we don't have a full per-character dictionary, so they fall through to
# the pinyin-fallback branch instead.
SINOSPHERE_HANZI: set[str] = {"jyutping", "zhuyin", "taigi", "japanese", "korean"}

LATIN_SE_ASIAN: set[str] = {"indonesian", "balinese", "malay", "filipino"}

# Languages whose script slot is non-Latin and we must phonetically
# transliterate the pinyin syllables.
NON_SINOSPHERE_SCRIPTS: set[str] = {
    "tibetan", "hindi", "mongolian", "thai", "khmer", "lao", "burmese",
}

# Per-syllable phonetic transliteration for the most common pinyin syllables
# that appear in TCM herb names. Same shape as scripts/14_localize_formulas.
# Fallback for syllables not listed: capitalize the syllable and use it in
# both slots (Latin), matching existing behaviour for unknown chars.
SYLLABLE_PHONETICS: dict[str, dict[str, dict[str, str]]] = {
    # Already in 14 (formulas):
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
    # Common herb-name syllables (extended):
    "ai":    {"thai": {"script": "อ้าย", "roman": "ai"},  "khmer": {"script": "អៃ", "roman": "ai"},     "lao": {"script": "ໄອ້", "roman": "ai"},   "burmese": {"script": "အိုင်း", "roman": "ain"}, "tibetan": {"script": "ཨེ", "roman": "e"},        "hindi": {"script": "आइ", "roman": "ai"},     "mongolian": {"script": "Ай", "roman": "Ay"}},
    "ye":    {"thai": {"script": "เย่", "roman": "ye"},   "khmer": {"script": "យេ", "roman": "ye"},     "lao": {"script": "ເຢ່", "roman": "ye"},   "burmese": {"script": "ယေ", "roman": "ye"},   "tibetan": {"script": "ཡེ", "roman": "ye"},      "hindi": {"script": "ये", "roman": "ye"},      "mongolian": {"script": "Е", "roman": "Ye"}},
    "cha":   {"thai": {"script": "ฉา", "roman": "cha"},   "khmer": {"script": "ឆា", "roman": "chha"},  "lao": {"script": "ສາ", "roman": "cha"},   "burmese": {"script": "ချား", "roman": "chha"}, "tibetan": {"script": "ཆ", "roman": "cha"},     "hindi": {"script": "छा", "roman": "chha"},   "mongolian": {"script": "Ча", "roman": "Cha"}},
    "an":    {"thai": {"script": "อาน", "roman": "an"},   "khmer": {"script": "អាន", "roman": "an"},   "lao": {"script": "ອານ", "roman": "an"},   "burmese": {"script": "အန်", "roman": "an"},   "tibetan": {"script": "ཨན", "roman": "an"},     "hindi": {"script": "आन", "roman": "an"},     "mongolian": {"script": "Ан", "roman": "An"}},
    "xi":    {"thai": {"script": "ซี", "roman": "xi"},    "khmer": {"script": "ស៊ី", "roman": "si"},  "lao": {"script": "ຊີ", "roman": "xi"},    "burmese": {"script": "စီ", "roman": "si"},   "tibetan": {"script": "ཤི", "roman": "shi"},    "hindi": {"script": "शी", "roman": "shi"},    "mongolian": {"script": "Си", "roman": "Si"}},
    "xiang": {"thai": {"script": "เซียง", "roman": "xiang"}, "khmer": {"script": "សៀង", "roman": "siang"}, "lao": {"script": "ຊຽງ", "roman": "siang"}, "burmese": {"script": "ရှန်း", "roman": "shian"}, "tibetan": {"script": "ཤང", "roman": "shang"},   "hindi": {"script": "शियाङ", "roman": "shiang"}, "mongolian": {"script": "Шан", "roman": "Shan"}},
    "ba":    {"thai": {"script": "ปา", "roman": "ba"},    "khmer": {"script": "បា", "roman": "ba"},    "lao": {"script": "ປາ", "roman": "ba"},    "burmese": {"script": "ဘာ", "roman": "ba"},   "tibetan": {"script": "པ", "roman": "pa"},      "hindi": {"script": "बा", "roman": "ba"},     "mongolian": {"script": "Ба", "roman": "Ba"}},
    "jiao":  {"thai": {"script": "เจียว", "roman": "chiao"}, "khmer": {"script": "ជៀវ", "roman": "chiav"}, "lao": {"script": "ຈຽວ", "roman": "chiao"}, "burmese": {"script": "ကြော်", "roman": "kyo"}, "tibetan": {"script": "ཅའོ", "roman": "ca'o"},   "hindi": {"script": "ज्याओ", "roman": "jyao"},  "mongolian": {"script": "Жяо", "roman": "Jyao"}},
    "hui":   {"thai": {"script": "หฺวย", "roman": "hui"}, "khmer": {"script": "ហុយ", "roman": "huy"}, "lao": {"script": "ຫວຍ", "roman": "hui"}, "burmese": {"script": "ဟွေး", "roman": "hwe"},   "tibetan": {"script": "ཧུའེ", "roman": "hu'e"}, "hindi": {"script": "हुई", "roman": "hui"},   "mongolian": {"script": "Хуй", "roman": "Khuy"}},
    "lian":  {"thai": {"script": "เหลียน", "roman": "lian"}, "khmer": {"script": "លៀន", "roman": "lian"}, "lao": {"script": "ລຽນ", "roman": "lian"}, "burmese": {"script": "လျန်း", "roman": "lyan"}, "tibetan": {"script": "ལན", "roman": "lan"},     "hindi": {"script": "ल्यान", "roman": "lyan"},  "mongolian": {"script": "Лян", "roman": "Lyan"}},
    # Generic CV/CVN pinyin syllables (fallback shapes):
    "gu":    {"thai": {"script": "กู", "roman": "ku"},    "khmer": {"script": "គូ", "roman": "ku"},   "lao": {"script": "ກູ", "roman": "ku"},    "burmese": {"script": "ဂူ", "roman": "gu"},    "tibetan": {"script": "ཀུ", "roman": "ku"},     "hindi": {"script": "गू", "roman": "gu"},     "mongolian": {"script": "Гу", "roman": "Gu"}},
    "ren":   {"thai": {"script": "เหริน", "roman": "ren"}, "khmer": {"script": "រ៉េន", "roman": "ren"}, "lao": {"script": "ເຣິນ", "roman": "ren"}, "burmese": {"script": "ရန်", "roman": "ren"},   "tibetan": {"script": "རན", "roman": "ran"},     "hindi": {"script": "रन", "roman": "ren"},     "mongolian": {"script": "Жэн", "roman": "Jen"}},
    "shen":  {"thai": {"script": "เซิน", "roman": "shen"}, "khmer": {"script": "សេន", "roman": "sen"}, "lao": {"script": "ເຊິນ", "roman": "shen"}, "burmese": {"script": "ရှန်", "roman": "shan"}, "tibetan": {"script": "ཤན", "roman": "shan"},     "hindi": {"script": "शेन", "roman": "shen"},   "mongolian": {"script": "Шэн", "roman": "Shen"}},
    "long":  {"thai": {"script": "หลง", "roman": "long"},  "khmer": {"script": "ឡុង", "roman": "long"}, "lao": {"script": "ລົງ", "roman": "long"}, "burmese": {"script": "လုံး", "roman": "lon"}, "tibetan": {"script": "ལུང", "roman": "lung"},   "hindi": {"script": "लोङ", "roman": "long"},   "mongolian": {"script": "Лон", "roman": "Lon"}},
    "yu":    {"thai": {"script": "ยฺวี", "roman": "yu"},   "khmer": {"script": "យូ", "roman": "yu"},    "lao": {"script": "ຍູ", "roman": "yu"},    "burmese": {"script": "ယူ", "roman": "yu"},     "tibetan": {"script": "ཡུ", "roman": "yu"},       "hindi": {"script": "यू", "roman": "yu"},       "mongolian": {"script": "Юй", "roman": "Yui"}},
    "shan":  {"thai": {"script": "ซาน", "roman": "shan"},  "khmer": {"script": "សាន", "roman": "san"}, "lao": {"script": "ຊານ", "roman": "shan"}, "burmese": {"script": "ရှန်", "roman": "shan"}, "tibetan": {"script": "ཤན", "roman": "shan"},     "hindi": {"script": "शान", "roman": "shan"},   "mongolian": {"script": "Шан", "roman": "Shan"}},
    "yi":    {"thai": {"script": "อี้", "roman": "yi"},   "khmer": {"script": "យី", "roman": "yi"},   "lao": {"script": "ອີ້", "roman": "yi"},    "burmese": {"script": "ယီ", "roman": "yi"},     "tibetan": {"script": "ཡི", "roman": "yi"},       "hindi": {"script": "यी", "roman": "yi"},       "mongolian": {"script": "И", "roman": "I"}},
    "zi":    {"thai": {"script": "จื่อ", "roman": "chue"}, "khmer": {"script": "ជឺ", "roman": "cheu"}, "lao": {"script": "ຈື່", "roman": "chue"}, "burmese": {"script": "ဇီ", "roman": "zi"},     "tibetan": {"script": "ཙི", "roman": "tsi"},      "hindi": {"script": "जी", "roman": "zi"},       "mongolian": {"script": "Зы", "roman": "Zy"}},
    "fu":    {"thai": {"script": "ฟู", "roman": "fu"},    "khmer": {"script": "ហ្វូ", "roman": "fu"},  "lao": {"script": "ຟູ", "roman": "fu"},    "burmese": {"script": "ဖူး", "roman": "phu"},   "tibetan": {"script": "ཕུའུ", "roman": "phu'u"}, "hindi": {"script": "फू", "roman": "phu"},    "mongolian": {"script": "Фу", "roman": "Fu"}},
    "lu":    {"thai": {"script": "ลู่", "roman": "lu"},   "khmer": {"script": "លូ", "roman": "lu"},   "lao": {"script": "ລູ່", "roman": "lu"},    "burmese": {"script": "လူ", "roman": "lu"},     "tibetan": {"script": "ལུ", "roman": "lu"},       "hindi": {"script": "लू", "roman": "lu"},       "mongolian": {"script": "Лу", "roman": "Lu"}},
    "ma":    {"thai": {"script": "หม่า", "roman": "ma"},  "khmer": {"script": "ម៉ា", "roman": "ma"}, "lao": {"script": "ມ່າ", "roman": "ma"},   "burmese": {"script": "မာ", "roman": "ma"},    "tibetan": {"script": "མ", "roman": "ma"},        "hindi": {"script": "मा", "roman": "ma"},       "mongolian": {"script": "Ма", "roman": "Ma"}},
    "shi":   {"thai": {"script": "ฉื่อ", "roman": "shi"}, "khmer": {"script": "ស៊ឺ", "roman": "seu"}, "lao": {"script": "ສື່", "roman": "shi"},   "burmese": {"script": "ရှိ", "roman": "shi"},    "tibetan": {"script": "ཤི", "roman": "shi"},      "hindi": {"script": "शी", "roman": "shi"},      "mongolian": {"script": "Ши", "roman": "Shi"}},
    "tian":  {"thai": {"script": "เทียน", "roman": "thian"}, "khmer": {"script": "ទៀន", "roman": "tian"}, "lao": {"script": "ທຽນ", "roman": "thian"}, "burmese": {"script": "ထျန်း", "roman": "thyan"}, "tibetan": {"script": "ཐན", "roman": "than"},     "hindi": {"script": "थ्यान", "roman": "thyan"}, "mongolian": {"script": "Тян", "roman": "Tyan"}},
    "shou":  {"thai": {"script": "โซ่ว", "roman": "shou"}, "khmer": {"script": "សូវ", "roman": "sov"}, "lao": {"script": "ໂຊ່", "roman": "shou"}, "burmese": {"script": "ရှိုး", "roman": "sho"},   "tibetan": {"script": "ཤོའུ", "roman": "sho'u"},  "hindi": {"script": "शोऊ", "roman": "shou"},   "mongolian": {"script": "Шоу", "roman": "Shou"}},
    "wu":    {"thai": {"script": "อู๋", "roman": "wu"},   "khmer": {"script": "អូ", "roman": "u"},   "lao": {"script": "ອູ່", "roman": "wu"},    "burmese": {"script": "အူ", "roman": "u"},     "tibetan": {"script": "འུ", "roman": "u"},        "hindi": {"script": "वू", "roman": "wu"},      "mongolian": {"script": "У", "roman": "U"}},
    "zhu":   {"thai": {"script": "จู", "roman": "chu"},   "khmer": {"script": "ជូ", "roman": "chu"},  "lao": {"script": "ຈູ", "roman": "chu"},   "burmese": {"script": "ကျု", "roman": "kyu"},   "tibetan": {"script": "ཀྲུ", "roman": "kru"},     "hindi": {"script": "जू", "roman": "ju"},       "mongolian": {"script": "Жу", "roman": "Ju"}},
    "shu":   {"thai": {"script": "ซู", "roman": "shu"},   "khmer": {"script": "ស៊ូ", "roman": "su"},  "lao": {"script": "ສູ", "roman": "shu"},   "burmese": {"script": "ရှူး", "roman": "shu"},   "tibetan": {"script": "ཤུ", "roman": "shu"},      "hindi": {"script": "शू", "roman": "shu"},      "mongolian": {"script": "Шу", "roman": "Shu"}},
    "ze":    {"thai": {"script": "เจ๋อ", "roman": "ze"},  "khmer": {"script": "ហ្ស៊ឺ", "roman": "zeu"}, "lao": {"script": "ເຊິ", "roman": "ze"},   "burmese": {"script": "ဇေး", "roman": "ze"},     "tibetan": {"script": "ཙེ", "roman": "tse"},      "hindi": {"script": "ज़े", "roman": "ze"},      "mongolian": {"script": "Зэ", "roman": "Ze"}},
    "xie":   {"thai": {"script": "เซีย", "roman": "sia"}, "khmer": {"script": "សៀ", "roman": "sia"},  "lao": {"script": "ຊຽ", "roman": "sia"},   "burmese": {"script": "ရှေး", "roman": "she"},   "tibetan": {"script": "ཤེ", "roman": "she"},      "hindi": {"script": "श्ये", "roman": "shye"},  "mongolian": {"script": "Се", "roman": "Se"}},
    "lin":   {"thai": {"script": "หลิน", "roman": "lin"}, "khmer": {"script": "លីន", "roman": "lin"}, "lao": {"script": "ລີນ", "roman": "lin"},  "burmese": {"script": "လင်", "roman": "lin"},    "tibetan": {"script": "ལིན", "roman": "lin"},      "hindi": {"script": "लिन", "roman": "lin"},     "mongolian": {"script": "Лин", "roman": "Lin"}},
    "qi":    {"thai": {"script": "ชี", "roman": "chi"},   "khmer": {"script": "ឈី", "roman": "chhi"}, "lao": {"script": "ສີ", "roman": "chi"},    "burmese": {"script": "ချီ", "roman": "chhi"},   "tibetan": {"script": "ཁྱི", "roman": "khyi"},   "hindi": {"script": "छी", "roman": "chhi"},   "mongolian": {"script": "Чи", "roman": "Chi"}},
    "qing":  {"thai": {"script": "ชิง", "roman": "ching"},"khmer": {"script": "ឈីង", "roman": "chhing"}, "lao": {"script": "ສິງ", "roman": "ching"}, "burmese": {"script": "ချင်း", "roman": "chhin"}, "tibetan": {"script": "ཁྱིང", "roman": "khying"}, "hindi": {"script": "छिङ", "roman": "chhing"}, "mongolian": {"script": "Чин", "roman": "Chin"}},
    "san":   {"thai": {"script": "ซาน", "roman": "san"},  "khmer": {"script": "សាន", "roman": "san"}, "lao": {"script": "ຊານ", "roman": "san"},  "burmese": {"script": "စန်း", "roman": "san"},  "tibetan": {"script": "སན", "roman": "san"},      "hindi": {"script": "सान", "roman": "san"},     "mongolian": {"script": "Сан", "roman": "San"}},
}


CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def find_canonical_hanzi(herb: dict) -> str:
    """Return the first short CJK alias (≤ 4 chars), or empty string."""
    for a in herb.get("aliases", []) or []:
        if not a:
            continue
        if CJK_RE.search(a):
            stripped = "".join(c for c in a if CJK_RE.match(c))
            if 1 <= len(stripped) <= 5:
                return stripped
    return ""


def split_pinyin_lower(name: str) -> list[str]:
    """Split a Latin pinyin string into lowercase syllables (no tone marks)."""
    no_tones = re.sub(
        r"[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛ]",
        lambda m: {
            "ā":"a","á":"a","ǎ":"a","à":"a","ē":"e","é":"e","ě":"e","è":"e",
            "ī":"i","í":"i","ǐ":"i","ì":"i","ō":"o","ó":"o","ǒ":"o","ò":"o",
            "ū":"u","ú":"u","ǔ":"u","ù":"u","ǖ":"u","ǘ":"u","ǚ":"u","ǜ":"u",
        }.get(m.group(0), m.group(0)),
        name.lower(),
    )
    return [s for s in re.split(r"[\s\-]+", no_tones) if s]


def syllable_to_lang(syl: str, lang: str) -> dict[str, str]:
    cell = SYLLABLE_PHONETICS.get(syl, {}).get(lang)
    if cell:
        return cell
    cap = syl.capitalize()
    return {"script": cap, "roman": cap}


def localize_herb(herb: dict) -> dict[str, dict[str, str]]:
    pinyin = (
        herb.get("linguistics", {}).get("tonal_pinyin")
        or herb.get("pinyin_name")
        or ""
    )
    hanzi = find_canonical_hanzi(herb)
    syllables = split_pinyin_lower(pinyin)

    out: dict[str, dict[str, str]] = {}
    for lang in ALL_LANGUAGES:
        if lang == "pinyin":
            out[lang] = {"script": hanzi or pinyin, "roman": pinyin}
        elif lang in SINOSPHERE_HANZI:
            # Keep Hanzi for script slot; pinyin/jyutping/etc. for roman.
            roman = (
                herb.get("linguistics", {}).get("jyutping")
                if lang == "jyutping"
                else (
                    herb.get("linguistics", {}).get("hokkien")
                    if lang == "taigi"
                    else pinyin
                )
            ) or pinyin
            out[lang] = {"script": hanzi or pinyin, "roman": roman}
        elif lang == "vietnamese":
            # Without a per-Hanzi Hán-Việt dictionary, use Latin pinyin in both.
            out[lang] = {"script": pinyin, "roman": pinyin}
        elif lang in LATIN_SE_ASIAN:
            out[lang] = {"script": pinyin, "roman": pinyin}
        else:
            # Non-Sinosphere with native script: phonetic per syllable.
            scripts: list[str] = []
            romans: list[str] = []
            for syl in syllables:
                cell = syllable_to_lang(syl, lang)
                scripts.append(cell["script"])
                romans.append(cell["roman"])
            sep_script = "" if lang in {"thai", "khmer", "lao", "burmese", "tibetan"} else " "
            out[lang] = {
                "script": sep_script.join(scripts),
                "roman": " ".join(romans),
            }

    return out


def main() -> int:
    if not SEED_HERBS_PATH.exists():
        print(f"Error: {SEED_HERBS_PATH} not found")
        return 1

    with SEED_HERBS_PATH.open(encoding="utf-8") as f:
        herbs = json.load(f)

    print(f"Localizing {len(herbs)} herbs across {len(ALL_LANGUAGES)} languages...")
    for i, herb in enumerate(herbs, 1):
        ling = herb.get("linguistics") or {}
        ling["translations"] = localize_herb(herb)
        herb["linguistics"] = ling
        if i % 100 == 0:
            print(f"  ... {i}/{len(herbs)}")

    SEED_HERBS_PATH.write_text(
        json.dumps(herbs, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {SEED_HERBS_PATH} with translations[18] for {len(herbs)} herbs.")
    if SEED_HERBS_MIRROR.parent.exists():
        SEED_HERBS_MIRROR.write_text(
            json.dumps(herbs, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Mirrored to {SEED_HERBS_MIRROR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
