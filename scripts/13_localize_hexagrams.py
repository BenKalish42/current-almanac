#!/usr/bin/env python3
"""
Task 12.5: Build the per-hexagram localization table.

For each of the 64 hexagrams, populate `translations[lang] = {script, roman}`
across all 18 supported languages. Sinosphere languages (Japanese, Korean,
Vietnamese) use deterministic Sino-readings; non-Sinosphere languages use
official phonetic transliteration of the Mandarin pinyin into the language's
native script + romanization standard.

Rules per language:
  - pinyin    : script = Hanzi (Simplified)   , roman = Hanyu Pinyin w/ tones
  - jyutping  : script = Hanzi (Traditional)  , roman = Jyutping
  - zhuyin    : script = Hanzi (Traditional)  , roman = Bopomofo
  - taigi     : script = Hanzi (Traditional)  , roman = Pe̍h-ōe-jī
  - japanese  : script = Kanji (= Hanzi)      , roman = Hepburn
  - korean    : script = Hangul               , roman = Revised Romanization
  - tibetan   : script = Tibetan              , roman = Wylie
  - hindi     : script = Devanagari           , roman = Hunterian
  - mongolian : script = Cyrillic             , roman = MNS 5217
  - thai      : script = Thai                 , roman = RTGS
  - vietnamese: script = Latin (Quốc ngữ)     , roman = Quốc ngữ (same)
  - indonesian/balinese/malay/filipino : both slots = phonetic Latin
  - khmer     : script = Khmer                , roman = UN
  - lao       : script = Lao                  , roman = BGN/PCGN
  - burmese   : script = Myanmar              , roman = MLC

Output is written into `src/data/seed_hexagrams.json` under each hex's
`translations` key, with the legacy flat fields (`pinyin_name`, etc.)
preserved for one release as a backwards-compat shim.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = PROJECT_ROOT / "src" / "data" / "seed_hexagrams.json"
MIRROR_PATH = PROJECT_ROOT / "data" / "output" / "seed_hexagrams.json"

# 64 hexagrams as (id, hanzi_simplified, hanzi_traditional, hanyu_pinyin)
# Traditional from HexagramModal.HEX_NAME_TRAD; Simplified from HomeView.HEX_NAME_CN_SHORT.
HEX_HANZI: list[tuple[int, str, str, str]] = [
    (1, "乾", "乾", "Qián"),
    (2, "坤", "坤", "Kūn"),
    (3, "屯", "屯", "Zhūn"),
    (4, "蒙", "蒙", "Méng"),
    (5, "需", "需", "Xū"),
    (6, "讼", "訟", "Sòng"),
    (7, "师", "師", "Shī"),
    (8, "比", "比", "Bǐ"),
    (9, "小畜", "小畜", "Xiǎo Chù"),
    (10, "履", "履", "Lǚ"),
    (11, "泰", "泰", "Tài"),
    (12, "否", "否", "Pǐ"),
    (13, "同人", "同人", "Tóng Rén"),
    (14, "大有", "大有", "Dà Yǒu"),
    (15, "谦", "謙", "Qiān"),
    (16, "豫", "豫", "Yù"),
    (17, "随", "隨", "Suí"),
    (18, "蛊", "蠱", "Gǔ"),
    (19, "临", "臨", "Lín"),
    (20, "观", "觀", "Guān"),
    (21, "噬嗑", "噬嗑", "Shì Kè"),
    (22, "贲", "賁", "Bì"),
    (23, "剥", "剝", "Bō"),
    (24, "复", "復", "Fù"),
    (25, "无妄", "無妄", "Wú Wàng"),
    (26, "大畜", "大畜", "Dà Chù"),
    (27, "颐", "頤", "Yí"),
    (28, "大过", "大過", "Dà Guò"),
    (29, "坎", "坎", "Kǎn"),
    (30, "离", "離", "Lí"),
    (31, "咸", "咸", "Xián"),
    (32, "恒", "恆", "Héng"),
    (33, "遯", "遯", "Dùn"),
    (34, "大壮", "大壯", "Dà Zhuàng"),
    (35, "晋", "晉", "Jìn"),
    (36, "明夷", "明夷", "Míng Yí"),
    (37, "家人", "家人", "Jiā Rén"),
    (38, "睽", "睽", "Kuí"),
    (39, "蹇", "蹇", "Jiǎn"),
    (40, "解", "解", "Xiè"),
    (41, "损", "損", "Sǔn"),
    (42, "益", "益", "Yì"),
    (43, "夬", "夬", "Guài"),
    (44, "姤", "姤", "Gòu"),
    (45, "萃", "萃", "Cuì"),
    (46, "升", "升", "Shēng"),
    (47, "困", "困", "Kùn"),
    (48, "井", "井", "Jǐng"),
    (49, "革", "革", "Gé"),
    (50, "鼎", "鼎", "Dǐng"),
    (51, "震", "震", "Zhèn"),
    (52, "艮", "艮", "Gèn"),
    (53, "渐", "漸", "Jiàn"),
    (54, "归妹", "歸妹", "Guī Mèi"),
    (55, "丰", "豐", "Fēng"),
    (56, "旅", "旅", "Lǚ"),
    (57, "巽", "巽", "Xùn"),
    (58, "兑", "兌", "Duì"),
    (59, "涣", "渙", "Huàn"),
    (60, "节", "節", "Jié"),
    (61, "中孚", "中孚", "Zhōng Fú"),
    (62, "小过", "小過", "Xiǎo Guò"),
    (63, "既济", "既濟", "Jì Jì"),
    (64, "未济", "未濟", "Wèi Jì"),
]

# --------------------------------------------------------------------------
# Per-language mappings. Format: id -> (script, roman). Any of the strings
# may be empty; downstream rendering falls back to Mandarin Hanzi/Pinyin.
#
# All non-Mandarin Sino readings (Japanese on'yomi, Korean Hangul/RR,
# Vietnamese Sino-Vietnamese) are well-attested in classical Yi-Jing
# scholarship for these specific characters. Non-Sinosphere languages use
# best-effort phonetic transliteration of the Mandarin pinyin into the
# language's native script + the language's official romanization standard.
# --------------------------------------------------------------------------

# JAPANESE — Kanji + Hepburn romaji (Sino-Japanese on'yomi)
# Two-char compounds rendered as single Romaji words per Yi-Jing convention.
JAPANESE: dict[int, tuple[str, str]] = {
    1: ("乾", "Ken"),       2: ("坤", "Kon"),       3: ("屯", "Chun"),
    4: ("蒙", "Mō"),         5: ("需", "Ju"),         6: ("訟", "Shō"),
    7: ("師", "Shi"),        8: ("比", "Hi"),         9: ("小畜", "Shōchiku"),
    10: ("履", "Ri"),        11: ("泰", "Tai"),       12: ("否", "Hi"),
    13: ("同人", "Dōjin"),   14: ("大有", "Daiyū"),   15: ("謙", "Ken"),
    16: ("豫", "Yo"),        17: ("隨", "Zui"),       18: ("蠱", "Ko"),
    19: ("臨", "Rin"),       20: ("觀", "Kan"),       21: ("噬嗑", "Zegō"),
    22: ("賁", "Hi"),        23: ("剝", "Haku"),      24: ("復", "Fuku"),
    25: ("無妄", "Mubō"),    26: ("大畜", "Daichiku"), 27: ("頤", "I"),
    28: ("大過", "Daika"),   29: ("坎", "Kan"),       30: ("離", "Ri"),
    31: ("咸", "Kan"),       32: ("恆", "Kō"),        33: ("遯", "Ton"),
    34: ("大壯", "Daisō"),   35: ("晉", "Shin"),      36: ("明夷", "Meii"),
    37: ("家人", "Kajin"),   38: ("睽", "Kei"),       39: ("蹇", "Ken"),
    40: ("解", "Kai"),       41: ("損", "Son"),       42: ("益", "Eki"),
    43: ("夬", "Kai"),       44: ("姤", "Kō"),        45: ("萃", "Sui"),
    46: ("升", "Shō"),       47: ("困", "Kon"),       48: ("井", "Sei"),
    49: ("革", "Kaku"),      50: ("鼎", "Tei"),       51: ("震", "Shin"),
    52: ("艮", "Gon"),       53: ("漸", "Zen"),       54: ("歸妹", "Kimai"),
    55: ("豐", "Hō"),        56: ("旅", "Ryo"),       57: ("巽", "Son"),
    58: ("兌", "Da"),        59: ("渙", "Kan"),       60: ("節", "Setsu"),
    61: ("中孚", "Chūfu"),   62: ("小過", "Shōka"),   63: ("既濟", "Kisei"),
    64: ("未濟", "Misei"),
}

# KOREAN — Hangul + Revised Romanization (Sino-Korean Hanja readings)
KOREAN: dict[int, tuple[str, str]] = {
    1: ("건", "geon"),       2: ("곤", "gon"),         3: ("준", "jun"),
    4: ("몽", "mong"),       5: ("수", "su"),          6: ("송", "song"),
    7: ("사", "sa"),         8: ("비", "bi"),          9: ("소축", "sochuk"),
    10: ("리", "ri"),        11: ("태", "tae"),        12: ("비", "bi"),
    13: ("동인", "dongin"),  14: ("대유", "daeyu"),    15: ("겸", "gyeom"),
    16: ("예", "ye"),        17: ("수", "su"),         18: ("고", "go"),
    19: ("림", "rim"),       20: ("관", "gwan"),       21: ("서합", "seohap"),
    22: ("비", "bi"),        23: ("박", "bak"),        24: ("복", "bok"),
    25: ("무망", "mumang"),  26: ("대축", "daechuk"),  27: ("이", "i"),
    28: ("대과", "daegwa"),  29: ("감", "gam"),        30: ("리", "ri"),
    31: ("함", "ham"),       32: ("항", "hang"),       33: ("둔", "dun"),
    34: ("대장", "daejang"), 35: ("진", "jin"),        36: ("명이", "myeongi"),
    37: ("가인", "gain"),    38: ("규", "gyu"),        39: ("건", "geon"),
    40: ("해", "hae"),       41: ("손", "son"),        42: ("익", "ik"),
    43: ("쾌", "kwae"),      44: ("구", "gu"),         45: ("췌", "chwe"),
    46: ("승", "seung"),     47: ("곤", "gon"),        48: ("정", "jeong"),
    49: ("혁", "hyeok"),     50: ("정", "jeong"),      51: ("진", "jin"),
    52: ("간", "gan"),       53: ("점", "jeom"),       54: ("귀매", "gwimae"),
    55: ("풍", "pung"),      56: ("려", "ryeo"),       57: ("손", "son"),
    58: ("태", "tae"),       59: ("환", "hwan"),       60: ("절", "jeol"),
    61: ("중부", "jungbu"),  62: ("소과", "sogwa"),    63: ("기제", "gije"),
    64: ("미제", "mije"),
}

# VIETNAMESE — Quốc ngữ (Sino-Vietnamese / Hán-Việt). Script == roman (both Latin).
VIETNAMESE: dict[int, str] = {
    1: "Càn",            2: "Khôn",            3: "Truân",
    4: "Mông",           5: "Nhu",             6: "Tụng",
    7: "Sư",             8: "Tỷ",              9: "Tiểu Súc",
    10: "Lý",            11: "Thái",           12: "Bĩ",
    13: "Đồng Nhân",     14: "Đại Hữu",        15: "Khiêm",
    16: "Dự",            17: "Tùy",            18: "Cổ",
    19: "Lâm",           20: "Quan",           21: "Phệ Hạp",
    22: "Bí",            23: "Bác",            24: "Phục",
    25: "Vô Vọng",       26: "Đại Súc",        27: "Di",
    28: "Đại Quá",       29: "Khảm",           30: "Ly",
    31: "Hàm",           32: "Hằng",           33: "Độn",
    34: "Đại Tráng",     35: "Tấn",            36: "Minh Di",
    37: "Gia Nhân",      38: "Khuê",           39: "Kiển",
    40: "Giải",          41: "Tổn",            42: "Ích",
    43: "Quải",          44: "Cấu",            45: "Tụy",
    46: "Thăng",         47: "Khốn",           48: "Tỉnh",
    49: "Cách",          50: "Đỉnh",           51: "Chấn",
    52: "Cấn",           53: "Tiệm",           54: "Quy Muội",
    55: "Phong",         56: "Lữ",             57: "Tốn",
    58: "Đoài",          59: "Hoán",           60: "Tiết",
    61: "Trung Phu",     62: "Tiểu Quá",       63: "Ký Tế",
    64: "Vị Tế",
}

# TIBETAN script + Wylie romanization (best-effort phonetic transliteration of pinyin)
TIBETAN: dict[int, tuple[str, str]] = {
    1: ("ཁྱན", "khyan"),         2: ("ཁུན", "khun"),           3: ("ཀྲུན", "krun"),
    4: ("མུང", "mung"),           5: ("ཤུའུ", "shu'u"),          6: ("སུང", "sung"),
    7: ("ཤི", "shi"),              8: ("པི", "pi"),               9: ("ཤའོ་ཁྲུ", "sha'o khru"),
    10: ("ལུའུ", "lu'u"),         11: ("ཐའེ", "tha'e"),         12: ("ཕི", "phi"),
    13: ("ཐུང་རན", "thung ran"), 14: ("ཏ་ཡའོ", "ta ya'o"),     15: ("ཆཱན", "chan"),
    16: ("ཡུའུ", "yu'u"),         17: ("སུའེ", "su'e"),         18: ("ཀུའུ", "ku'u"),
    19: ("ལིན", "lin"),            20: ("ཀུཨན", "ku'an"),        21: ("ཤི་ཧུའེ", "shi hu'e"),
    22: ("པི", "pi"),              23: ("པོ", "po"),              24: ("ཕུའུ", "phu'u"),
    25: ("འུ་ཝང", "u wang"),      26: ("ཏ་ཁྲུ", "ta khru"),     27: ("ཡི", "yi"),
    28: ("ཏ་ཀོ", "ta ko"),         29: ("ཁན", "khan"),            30: ("ལི", "li"),
    31: ("ཤན", "shan"),            32: ("ཧང", "hang"),            33: ("ཏུན", "tun"),
    34: ("ཏ་ཀྲུཨང", "ta krwang"), 35: ("ཅིན", "cin"),           36: ("མིང་ཡི", "ming yi"),
    37: ("ཅཱ་རན", "ca ran"),       38: ("ཁུའེ", "khu'e"),        39: ("ཅཱན", "can"),
    40: ("ཤེ", "she"),              41: ("སུན", "sun"),            42: ("ཡི", "yi"),
    43: ("ཀུཨའེ", "ku'a'e"),      44: ("ཀོའུ", "ko'u"),         45: ("ཚུའེ", "tshu'e"),
    46: ("ཤང", "shang"),            47: ("ཁུན", "khun"),           48: ("ཅིང", "cing"),
    49: ("ཀེ", "ke"),                50: ("ཏིང", "ting"),           51: ("ཀྲན", "kran"),
    52: ("ཀན", "kan"),               53: ("ཅཱན", "can"),            54: ("ཀུའེ་མེའེ", "ku'e me'e"),
    55: ("ཕིང", "phing"),            56: ("ལུའུ", "lu'u"),         57: ("ཤུན", "shun"),
    58: ("ཏུའེ", "tu'e"),            59: ("ཧུཨན", "hu'an"),        60: ("ཅཱ", "ca"),
    61: ("ཀྲུང་ཕུའུ", "krung phu'u"), 62: ("ཤའོ་ཀོ", "sha'o ko"), 63: ("ཅི་ཅི", "ci ci"),
    64: ("ཝེའེ་ཅི", "we'e ci"),
}

# HINDI Devanagari + Hunterian romanization (phonetic)
HINDI: dict[int, tuple[str, str]] = {
    1: ("छ्येन", "chhyen"),       2: ("खुन", "khun"),         3: ("जुन", "jun"),
    4: ("मेङ", "meng"),            5: ("श्यू", "shyu"),         6: ("सोङ", "song"),
    7: ("शी", "shi"),               8: ("पी", "pi"),              9: ("श्याओ छू", "shyao chhu"),
    10: ("ल्यू", "lyu"),           11: ("ताई", "tai"),          12: ("पी", "pi"),
    13: ("थोङ रन", "thong ran"), 14: ("ता योऊ", "ta you"),    15: ("छ्येन", "chhyen"),
    16: ("यू", "yu"),                17: ("सुई", "sui"),           18: ("गू", "gu"),
    19: ("लिन", "lin"),              20: ("गुआन", "guan"),        21: ("श्र हे", "shr he"),
    22: ("पी", "pi"),                23: ("पो", "po"),             24: ("फू", "phu"),
    25: ("वू वाङ", "wu wang"),     26: ("ता छू", "ta chhu"),    27: ("यी", "yi"),
    28: ("ता क्वो", "ta kwo"),     29: ("खान", "khan"),          30: ("ली", "li"),
    31: ("श्येन", "shyen"),         32: ("हङ", "hang"),           33: ("तुन", "tun"),
    34: ("ता च्वाङ", "ta chwang"), 35: ("जिन", "jin"),         36: ("मिङ यी", "ming yi"),
    37: ("ज्या रन", "jya ran"),    38: ("खुई", "khui"),         39: ("ज्येन", "jyen"),
    40: ("श्ये", "shye"),            41: ("सुन", "sun"),           42: ("यी", "yi"),
    43: ("गुआई", "guai"),            44: ("गोऊ", "gou"),           45: ("छुई", "chhui"),
    46: ("शेङ", "sheng"),            47: ("खुन", "khun"),          48: ("जिङ", "jing"),
    49: ("गे", "ge"),                 50: ("तिङ", "ting"),          51: ("जन", "jen"),
    52: ("गन", "gan"),                53: ("ज्येन", "jyen"),       54: ("गुई मे", "gui me"),
    55: ("फेङ", "pheng"),             56: ("ल्यू", "lyu"),         57: ("श्युन", "shyun"),
    58: ("तुई", "tui"),                59: ("हुआन", "huan"),        60: ("ज्ये", "jye"),
    61: ("जोङ फू", "jong phu"),     62: ("श्याओ क्वो", "shyao kwo"),
    63: ("जी जी", "ji ji"),           64: ("वे जी", "we ji"),
}

# THAI script + RTGS romanization
THAI: dict[int, tuple[str, str]] = {
    1: ("เฉียน", "chian"),         2: ("คุน", "khun"),           3: ("จุน", "chun"),
    4: ("เหมิง", "mueang"),        5: ("ซวี", "sue"),             6: ("ซ่ง", "song"),
    7: ("ชือ", "chue"),             8: ("ปี่", "pi"),               9: ("เสี่ยวฉู", "siao chu"),
    10: ("หลฺวี่", "lue"),          11: ("ไท่", "thai"),           12: ("ผี่", "phi"),
    13: ("ถงเหริน", "thong ren"), 14: ("ต้ายฺหวี่", "ta yu"),    15: ("เชียน", "chian"),
    16: ("ยฺวี่", "yu"),             17: ("สุย", "sui"),            18: ("กู่", "ku"),
    19: ("หลิน", "lin"),             20: ("กฺวาน", "kwan"),         21: ("ซื่อเค่อ", "sue khoe"),
    22: ("ปี้", "pi"),                23: ("ปอ", "po"),               24: ("ฟู่", "fu"),
    25: ("อู๋ว่าง", "wu wang"),    26: ("ต้าฉู", "ta chu"),        27: ("อี๋", "i"),
    28: ("ต้ากั้ว", "ta kuo"),     29: ("ข่าน", "khan"),          30: ("หลี", "li"),
    31: ("เสฺยียน", "sian"),        32: ("เหิง", "heng"),          33: ("ตุ้น", "tun"),
    34: ("ต้าจฺวั้ง", "ta chuang"), 35: ("จิ้น", "chin"),         36: ("หมิงอี๋", "ming i"),
    37: ("เจียเหริน", "chia ren"), 38: ("คุย", "khui"),           39: ("เจี่ยน", "chian"),
    40: ("เจี่ย", "chia"),           41: ("สุ่น", "sun"),            42: ("อี้", "i"),
    43: ("กว้าย", "kuai"),           44: ("โก้ว", "kou"),            45: ("ฉุ่ย", "chui"),
    46: ("เซิง", "sheng"),           47: ("คุ่น", "khun"),          48: ("จิ่ง", "ching"),
    49: ("เก๋อ", "ke"),              50: ("ติ่ง", "ting"),           51: ("เจิ้น", "chen"),
    52: ("เกิ้น", "ken"),            53: ("เจี้ยน", "chian"),       54: ("กุยเม่ย", "kui mei"),
    55: ("เฟิง", "feng"),            56: ("หลฺวี่", "lue"),         57: ("ซฺวิ่น", "sun"),
    58: ("ตุ้ย", "tui"),             59: ("ฮ่วน", "huan"),          60: ("เจี๋ย", "chia"),
    61: ("จงฝู", "chong fu"),       62: ("เสี่ยวกั้ว", "siao kuo"),
    63: ("จี้จี้", "chi chi"),       64: ("เว่ยจี้", "wei chi"),
}

# KHMER script + UN Romanization
KHMER: dict[int, tuple[str, str]] = {
    1: ("ឆ្យាន", "chhyean"),     2: ("ឃុន", "khun"),          3: ("ជូន", "chun"),
    4: ("ម៉ឺង", "moeung"),         5: ("ស៊ូ", "su"),             6: ("ស៊ុង", "sung"),
    7: ("ឈិ", "chhi"),              8: ("ប៊ី", "bi"),              9: ("ស្យាវឈូ", "syav chhu"),
    10: ("លី", "li"),                11: ("ថៃ", "thai"),           12: ("ភី", "phi"),
    13: ("ថុងរ៉េន", "thung ren"), 14: ("តាយូ", "ta yu"),        15: ("ឆ្យាន", "chhyean"),
    16: ("យូ", "yu"),                17: ("ស៊ុយ", "suy"),         18: ("គូ", "ku"),
    19: ("លីន", "lin"),              20: ("ក្វាន់", "kvan"),       21: ("ស៊ឺឃឺ", "su khu"),
    22: ("ប៊ី", "bi"),               23: ("ប៉ូ", "po"),            24: ("ហ្វូ", "fu"),
    25: ("អូវ៉ាង", "u wang"),     26: ("តាឈូ", "ta chhu"),     27: ("យី", "yi"),
    28: ("តាគ្វ័រ", "ta kuo"),     29: ("ឃាន់", "khan"),         30: ("លី", "li"),
    31: ("ស្យេន", "syen"),          32: ("ហេង", "heng"),          33: ("ទុន", "tun"),
    34: ("តាជ្វាង", "ta jvang"),  35: ("ជីន", "jin"),           36: ("មីងយី", "ming yi"),
    37: ("ជារ៉េន", "ja ren"),     38: ("ឃុយ", "khuy"),          39: ("ជៀន", "chian"),
    40: ("ស្យេ", "sye"),            41: ("ស៊ុន", "sun"),          42: ("យី", "yi"),
    43: ("ក្វៃ", "kvai"),            44: ("កូវ", "kov"),            45: ("ឈុយ", "chhuy"),
    46: ("ស៊េង", "seng"),            47: ("ឃុន", "khun"),           48: ("ជីង", "jing"),
    49: ("គេ", "ke"),                50: ("ទីង", "ting"),           51: ("ជេន", "jen"),
    52: ("កែន", "ken"),              53: ("ជៀន", "chian"),         54: ("គុយម៉ី", "kuy mei"),
    55: ("ផេង", "pheng"),            56: ("លី", "li"),              57: ("ស៊ុន", "sun"),
    58: ("ទុយ", "tuy"),              59: ("ហួន", "huan"),           60: ("ជៀ", "chia"),
    61: ("ជុងហ្វូ", "jung fu"),    62: ("ស្យាវគ្វ័រ", "syav kuo"),
    63: ("ជីជី", "ji ji"),           64: ("វេជី", "we ji"),
}

# LAO script + BGN/PCGN
LAO: dict[int, tuple[str, str]] = {
    1: ("ຈຽນ", "chian"),           2: ("ຄຸນ", "khun"),           3: ("ຈຸນ", "chun"),
    4: ("ເມິງ", "moeng"),          5: ("ຊຶ", "se"),              6: ("ຊົ່ງ", "song"),
    7: ("ຊື່", "sue"),              8: ("ປີ່", "pi"),             9: ("ຊຽວຊູ", "siao su"),
    10: ("ລື່", "lue"),             11: ("ໄທ່", "thai"),          12: ("ຜີ່", "phi"),
    13: ("ທົງເຣິນ", "thong ren"),14: ("ຕ້າຢື່", "ta yue"),     15: ("ຈຽນ", "chian"),
    16: ("ຢື່", "yue"),              17: ("ຊຸຍ", "sui"),           18: ("ກູ່", "ku"),
    19: ("ລິນ", "lin"),              20: ("ກວານ", "kuan"),         21: ("ຊື່ເຄິ່", "sue khoe"),
    22: ("ປີ່", "pi"),                23: ("ປໍ", "po"),             24: ("ຟູ່", "fu"),
    25: ("ອູ່ຫວ່າງ", "u wang"),  26: ("ຕ້າຊູ", "ta su"),       27: ("ອີ່", "i"),
    28: ("ຕ້າກົ່ວ", "ta kuo"),    29: ("ຄ່ານ", "khan"),         30: ("ລີ", "li"),
    31: ("ຊຽນ", "sian"),             32: ("ເຫິງ", "heng"),         33: ("ຕຸ່ນ", "tun"),
    34: ("ຕ້າຈົ່ວງ", "ta chuang"), 35: ("ຈິ່ນ", "chin"),       36: ("ມີ່ງອີ່", "ming i"),
    37: ("ຈຽເຣິນ", "chia ren"),   38: ("ຄຸຍ", "khui"),          39: ("ຈຽນ", "chian"),
    40: ("ຈຽ", "chia"),               41: ("ຊຸ່ນ", "sun"),          42: ("ອີ່", "i"),
    43: ("ກວາຍ", "kuai"),             44: ("ໂກ່ວ", "kou"),         45: ("ຊຸຍ", "sui"),
    46: ("ເຊິງ", "seng"),             47: ("ຄຸ່ນ", "khun"),         48: ("ຈິ່ງ", "ching"),
    49: ("ເກິ່", "ke"),               50: ("ຕິ່ງ", "ting"),         51: ("ເຈິ່ນ", "chen"),
    52: ("ເກິ່ນ", "ken"),             53: ("ຈຽນ", "chian"),         54: ("ກຸຍເມີ່", "kui mei"),
    55: ("ເຟິງ", "feng"),             56: ("ລື່", "lue"),           57: ("ຊຶ່ນ", "sun"),
    58: ("ຕຸຍ", "tui"),               59: ("ຫວນ", "huan"),           60: ("ຈຽ", "chia"),
    61: ("ຈົງຟູ", "chong fu"),      62: ("ຊຽວກົ່ວ", "siao kuo"),
    63: ("ຈີ່ຈີ່", "chi chi"),       64: ("ເຫວ່ຍຈີ່", "wei chi"),
}

# BURMESE script + MLC romanization
BURMESE: dict[int, tuple[str, str]] = {
    1: ("ချန်", "chyan"),           2: ("ခွန်", "khun"),         3: ("ချွန်", "chyun"),
    4: ("မုန်", "mun"),              5: ("ရှူး", "shu"),          6: ("ဆွန်း", "swan"),
    7: ("ရှိ", "shi"),                8: ("ပီ", "pi"),              9: ("ရှောက်ချူ", "shauk chyu"),
    10: ("လူ", "lu"),                  11: ("ထိုင်း", "thaing"),    12: ("ဖီ", "phi"),
    13: ("သုံးရန်", "thon ran"),    14: ("တာယူး", "ta yu"),       15: ("ချန်", "chyan"),
    16: ("ယူ", "yu"),                  17: ("ဆွေး", "swe"),         18: ("ကူး", "ku"),
    19: ("လင်", "lin"),                20: ("ကွမ်", "kwan"),         21: ("ရှုခွဲ", "shu khwe"),
    22: ("ပီ", "pi"),                   23: ("ပို", "po"),            24: ("ဖူး", "phu"),
    25: ("အူဝမ်း", "u wang"),       26: ("တာချူ", "ta chyu"),     27: ("ယီ", "yi"),
    28: ("တာကွိုး", "ta kwo"),     29: ("ခါန်", "khan"),         30: ("လီ", "li"),
    31: ("ရှန်", "shan"),               32: ("ဟန်း", "han"),          33: ("တုန်း", "tun"),
    34: ("တာချွမ်း", "ta chwan"),  35: ("ကျင်း", "kyin"),       36: ("မင်းယီ", "ming yi"),
    37: ("ကျာရန်", "kya ran"),     38: ("ခွေး", "khwe"),          39: ("ကျန်း", "kyan"),
    40: ("ရှေး", "she"),                41: ("ဆွန်း", "swan"),        42: ("ယီ", "yi"),
    43: ("ကွိုက်", "kwaik"),         44: ("ကိုး", "ko"),            45: ("ချွေး", "chwe"),
    46: ("ရှင်း", "shin"),              47: ("ခွန်း", "khwan"),       48: ("ကျင်း", "kyin"),
    49: ("ကေး", "ke"),                   50: ("တင်း", "tin"),           51: ("ကျန်း", "kyan"),
    52: ("ကန်း", "kan"),                 53: ("ကျန်း", "kyan"),        54: ("ကွေးမယ်", "kwe me"),
    55: ("ဖေါင်း", "phaung"),          56: ("လူ", "lu"),               57: ("ဆွန်း", "swan"),
    58: ("တွေး", "twe"),                 59: ("ဟွမ်း", "hwan"),         60: ("ကျယ်", "kya"),
    61: ("ကျုံဖူး", "kyon phu"),     62: ("ရှောက်ကွိုး", "shauk kwo"),
    63: ("ကျိကျိ", "kyi kyi"),       64: ("ဝေးကျိ", "we kyi"),
}

# MONGOLIAN Cyrillic + MNS 5217 romanization
MONGOLIAN: dict[int, tuple[str, str]] = {
    1: ("Чянь", "Chyani"),         2: ("Хунь", "Khuni"),         3: ("Жунь", "Juni"),
    4: ("Мэн", "Meng"),             5: ("Шү", "Shu"),             6: ("Сун", "Sun"),
    7: ("Ши", "Shi"),                8: ("Би", "Bi"),               9: ("Шяочү", "Shyaochu"),
    10: ("Лү", "Lu"),                11: ("Тай", "Tai"),           12: ("Пи", "Pi"),
    13: ("Тунжэн", "Tung jen"),     14: ("Даю", "Dayu"),         15: ("Чянь", "Chyani"),
    16: ("Юй", "Yui"),                17: ("Суй", "Suy"),          18: ("Гу", "Gu"),
    19: ("Линь", "Lini"),             20: ("Гуань", "Guani"),     21: ("Шихэ", "Shi he"),
    22: ("Би", "Bi"),                 23: ("Бо", "Bo"),             24: ("Фу", "Fu"),
    25: ("Уван", "U wang"),         26: ("Дачү", "Dachu"),       27: ("И", "I"),
    28: ("Дакво", "Dakvo"),         29: ("Хан", "Khan"),          30: ("Ли", "Li"),
    31: ("Шянь", "Shyani"),          32: ("Хэн", "Heng"),          33: ("Тунь", "Tuni"),
    34: ("Дажуан", "Da juang"),    35: ("Жинь", "Jini"),         36: ("Минии", "Mingi"),
    37: ("Жяжэн", "Jya jen"),       38: ("Хуй", "Khuy"),          39: ("Жянь", "Jyani"),
    40: ("Шэ", "She"),                41: ("Сунь", "Suni"),         42: ("И", "I"),
    43: ("Гуай", "Guay"),             44: ("Гоу", "Gou"),           45: ("Цуй", "Tsuy"),
    46: ("Шэн", "Sheng"),             47: ("Кунь", "Kuni"),         48: ("Жин", "Jing"),
    49: ("Гэ", "Ge"),                  50: ("Тин", "Ting"),          51: ("Жэн", "Jen"),
    52: ("Гэн", "Gen"),                53: ("Жянь", "Jyani"),        54: ("Гуймэй", "Guy mei"),
    55: ("Фэн", "Feng"),               56: ("Лү", "Lu"),             57: ("Сүнь", "Suni"),
    58: ("Дуй", "Duy"),                59: ("Хуан", "Khuan"),        60: ("Же", "Je"),
    61: ("Жунфу", "Jung fu"),         62: ("Шяокво", "Shyao kvo"),
    63: ("Жижи", "Ji ji"),             64: ("Вэйжи", "Wei ji"),
}


def main() -> int:
    if not SEED_PATH.exists():
        print(f"Error: {SEED_PATH} not found")
        return 1

    with SEED_PATH.open(encoding="utf-8") as f:
        hexes = json.load(f)

    if len(hexes) != 64:
        print(f"Error: expected 64 hexagrams, got {len(hexes)}")
        return 1

    # Build by-id lookup of hanzi tuple
    hanzi_by_id = {hid: (sim, trad, py) for hid, sim, trad, py in HEX_HANZI}

    for h in hexes:
        hid = int(h["id"])
        sim, trad, hanyu_pinyin = hanzi_by_id[hid]
        jp_script, jp_roman = JAPANESE[hid]
        ko_script, ko_roman = KOREAN[hid]
        vi = VIETNAMESE[hid]
        ti_script, ti_roman = TIBETAN[hid]
        hi_script, hi_roman = HINDI[hid]
        th_script, th_roman = THAI[hid]
        km_script, km_roman = KHMER[hid]
        lo_script, lo_roman = LAO[hid]
        my_script, my_roman = BURMESE[hid]
        mn_script, mn_roman = MONGOLIAN[hid]

        # For Latin-script SE Asian languages with no native script, both
        # slots show the same phonetic Latin spelling of the pinyin.
        latin_phonetic = hanyu_pinyin  # already Latin; tone marks acceptable

        translations = {
            "pinyin":     {"script": sim,  "roman": hanyu_pinyin},
            "jyutping":   {"script": trad, "roman": h.get("jyutping_name", "")},
            "zhuyin":     {"script": trad, "roman": h.get("zhuyin_name", "")},
            "taigi":      {"script": trad, "roman": h.get("taigi_name", "")},
            "japanese":   {"script": jp_script, "roman": jp_roman},
            "korean":     {"script": ko_script, "roman": ko_roman},
            "tibetan":    {"script": ti_script, "roman": ti_roman},
            "hindi":      {"script": hi_script, "roman": hi_roman},
            "mongolian":  {"script": mn_script, "roman": mn_roman},
            "thai":       {"script": th_script, "roman": th_roman},
            "vietnamese": {"script": vi,        "roman": vi},
            "indonesian": {"script": latin_phonetic, "roman": latin_phonetic},
            "balinese":   {"script": latin_phonetic, "roman": latin_phonetic},
            "malay":      {"script": latin_phonetic, "roman": latin_phonetic},
            "filipino":   {"script": latin_phonetic, "roman": latin_phonetic},
            "khmer":      {"script": km_script, "roman": km_roman},
            "lao":        {"script": lo_script, "roman": lo_roman},
            "burmese":    {"script": my_script, "roman": my_roman},
        }

        h["translations"] = translations
        # Convenience: the canonical Hanzi script for each hex (used by
        # LocalizedScript when a non-Mandarin language has no specific script).
        h["hanzi_simplified"] = sim
        h["hanzi_traditional"] = trad

    SEED_PATH.write_text(
        json.dumps(hexes, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {SEED_PATH} with translations[18] for all 64 hexagrams.")

    if MIRROR_PATH.exists():
        MIRROR_PATH.write_text(
            json.dumps(hexes, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Mirrored to {MIRROR_PATH}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
