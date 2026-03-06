#!/usr/bin/env python3
"""
Phase 2 ETL: Adaptive Text Chunker.
Parses raw Yi Jing texts into 64 hexagram chapters per book.
Uses book-specific regex patterns. Validates 64 chunks before saving.
"""
import re
import sys
from pathlib import Path

# --- Filename to output folder mapping ---
# Derive slug from "Yi Jing (Tradition N) - Author.txt"
FOLDER_MAP = {
    "Yi Jing (Buddhist 1) - Thomas Cleary.txt": "buddhist_1_cleary",
    "Yi Jing (Confucian 1) - Thomas Cleary.txt": "confucian_1_cleary",
    "Yi Jing (Confucian 2) - James Legge.txt": "confucian_2_legge",
    "Yi Jing (Daoist 1) - Thomas Cleary.txt": "daoist_1_cleary",
    "Yi Jing (Daoist 2) - Jou Tsung Hwa.txt": "daoist_2_jou",
    "Yi Jing (Gene Keys 1) - Richard Rudd.txt": "gene_keys_1_rudd",
    "Yi Jing (Human Design 1) - Ra Uru Hu.txt": "human_design_1_ra",
    "Yi Jing (Psychological 1) - Richard Wilhelm.txt": "psychological_1_wilhelm",
}

# --- Book-specific split patterns ---
# Split markers match the START of each hexagram chapter (in order 1..64)

# Confucian 1 Cleary: "1. The Creative", "2. The Receptive", etc. (from TOC - exact names)
CONFUCIAN1_NAMES = (
    r"The Creative|The Receptive|Difficulty|Innocence|Waiting|Contention|An Army|Accord|"
    r"Nurture of the Small|Treading|Tranquillity|Obstruction|Sameness with People|Great Possession|"
    r"Humility|Happiness|Following|Disruption|Overseeing|Observing|Biting Through|Adornment|"
    r"Stripping Away|Return|Fidelity|Great Buildup|Nourishment|Predominance of the Great|"
    r"Constant Pitfalls|Fire|Sensitivity|Persistence|Withdrawal|The Power of Greatness|Advance|"
    r"Injury to the Enlightened|People in the Home|Opposition|Halting|Solution|Reduction|Increase|"
    r"Decisiveness|Meeting|Gathering|Rising|Exhaustion|The Well|Change|The Cauldron|Thunder|"
    r"Mountains|Gradual Progress|A Young Woman Going to Marry|Abundance|Travel|Conformity|"
    r"Pleasing|Dispersal|Regulation|Truthfulness in the Center|Predominance of the Small|"
    r"Already Accomplished|Unfinished"
)
CONFUCIAN1_PATTERN = re.compile(r"^(?P<num>\d{1,2})\. (" + CONFUCIAN1_NAMES + r")\s*$", re.MULTILINE)

# Buddhist 1: "1. Heaven", "2. Earth" - names may be followed by page num or inline text
BUDDHIST1_NAMES = (
    r"Heaven|Earth|Difficulty|Darkness|Waiting|Contention|The Army|Accord|"
    r"Small Obstruction \(Nurturance of the Small\)|Small Obstruction|Nurturance of the Small|Treading|"
    r"Tranquillity|Obstruction|Sameness with People|Great Possession|Humility|Joy|"
    r"Following|Degeneration|Overseeing|Observing|Biting Through|Adornment|Stripping Away|"
    r"Return|No Error|Great Buildup|Nourishment|The Passing of Greatness|Multiple Danger|"
    r"Fire|Sensing|Constancy|Withdrawal|The Power of the Great|Advance|"
    r"Damage of Illumination \(Concealment of Illumination\)|Damage of Illumination|Concealment of Illumination|"
    r"People in the Home|Opposition|Trouble|Solution|Reduction|Increase|"
    r"Decision \(Parting\)|Decision|Parting|Meeting|Gathering|Rising|Exhaustion|The Well|Change|"
    r"The Cauldron|Thunder|Mountain|Mountains|Gradual Progress|Marrying a Young Girl|"
    r"A Young Woman Going to Marry|Richness|Abundance|Travel|Conformity|Pleasing|Dispersal|"
    r"Regulation|Truthfulness in the Center|Sincerity in the Center|Predominance of the Small|Small Excess|"
    r"Already Accomplished|Settled|Unfinished|Unsettled|Wind|Delight"
)
# Buddhist 1: "1. Heaven", "30.\n\nFire"; "I CHING 7. The Army 47"; "182 48. The Well 183"
BUDDHIST1_PATTERN = re.compile(
    r"(?:^|[\s]|I CHING )(?P<num>\d{1,2})\.\s*(?:[\r\n]+(?:\s*-?\s*[\r\n]*)?\s*)?(?:THE IMAGE:\s*)?(" + BUDDHIST1_NAMES + r")\b(?:\s+\d+)?",
    re.MULTILINE,
)

# Daoist 1: "1. Heaven", "2. Earth" — hex 36 uses "36. (Injury of Illumination)" (paren prefix)
DAOIST1_PATTERN = re.compile(
    r"^(?P<num>\d{1,2})\.\s+[A-Za-z\(][a-zA-Z \(\)\-]+(?:\s+\d+)?\s*$",
    re.MULTILINE,
)

# Gene Keys: "THE 1ST GENE KEY", "THE 2ND GENE KEY", etc.
GENE_KEYS_PATTERN = re.compile(
    r"^THE (?P<num>\d{1,2})(?:ST|ND|RD|TH) GENE KEY",
    re.MULTILINE,
)

# Human Design: "1 THE GATE OF..." or "10 10 11 THE GATE OF" — tolerate "T HE GATE" typo
HUMAN_DESIGN_PATTERN = re.compile(
    r"^(?:\d+\s+){0,2}(?P<num>\d+)\s+T\s*HE GATE OF ",
    re.MULTILINE,
)

# Wilhelm: "1. Ch'ien / The Creative", "24. Fu / Return (The Turning Point)"
WILHELM_PATTERN = re.compile(
    r"^(?P<num>\d{1,2})\.\s+[\w\x27\u2019\- ]+\s*/\s*[^\n]+$",
    re.MULTILINE | re.UNICODE,
)

# Daoist 2 Jou: right col = (?!\d{1,2}\.); left col = ^ at line start
DAOIST2_RIGHT_OR_MID = re.compile(
    r"(?P<num>\d{1,2})\.\s+(?:(?!\d{1,2}\.).)+?[—\-][\s\-—]*[A-Za-z]+",
    re.MULTILINE,
)
DAOIST2_LEFT_COL = re.compile(
    r"^\s*(?P<num>\d{1,2})\.\s+.+?[—\-][\s\-—]*[A-Za-z]+",
    re.MULTILINE,
)
# No-emdash TOC entries — each as separate pattern (Python re doesn't allow duplicate group names in |)
DAOIST2_48 = re.compile(r"(?P<num>48)\.\s*Jing\s+Well", re.MULTILINE)
DAOIST2_62 = re.compile(r"(?P<num>62)\.\s*Xiaoguo", re.MULTILINE)
DAOIST2_51 = re.compile(r"(?P<num>51)\.\s*Zhen\s+Thunder", re.MULTILINE)
DAOIST2_52 = re.compile(r"(?P<num>52)\.\s*Yin\s+Mountain", re.MULTILINE)
DAOIST2_PAGE_50 = re.compile(r"[\d\s]{3}(?P<num>50)\.", re.MULTILINE)

BOOK_CONFIG = {
    "Yi Jing (Buddhist 1) - Thomas Cleary.txt": {
        "pattern": BUDDHIST1_PATTERN,
        "extract_num": True,
        "prefer_largest": True,
        "section_start": "The Buddhist I Ching",
        "include_match": True,  # avoid empty chunks when headers are back-to-back
    },
    "Yi Jing (Confucian 1) - Thomas Cleary.txt": {
        "pattern": CONFUCIAN1_PATTERN,
        "extract_num": True,
    },
    "Yi Jing (Confucian 2) - James Legge.txt": {
        "pattern": re.compile(r"^Hexagram ([IVXLCDM]+)\.(?:\S)?\s*", re.MULTILINE),  # allow footnote marker e.g. IX.⁹
        "extract_num": False,
        "section_start": "\nHexagram I.\n",  # skip TOC; main body has standalone "Hexagram I." on its own line
    },
    "Yi Jing (Daoist 1) - Thomas Cleary.txt": {
        "pattern": DAOIST1_PATTERN,
        "extract_num": True,
        "prefer_largest": True,
        "section_start": "The Text\n\n1. Heaven",
        "section_end": "Book II",
    },
    "Yi Jing (Daoist 2) - Jou Tsung Hwa.txt": {
        "pattern": [DAOIST2_RIGHT_OR_MID, DAOIST2_LEFT_COL, DAOIST2_48, DAOIST2_51, DAOIST2_52, DAOIST2_62, DAOIST2_PAGE_50],
        "extract_num": True,
        "section_start": "2-6",
        "prefer_largest": True,
        "multi_pattern": True,
    },
    "Yi Jing (Gene Keys 1) - Richard Rudd.txt": {
        "pattern": re.compile(r"^SIDDHI [A-Z]", re.MULTILINE),  # full chapters start with SIDDHI; TOC uses "THE Nth GENE KEY"
        "extract_num": False,  # use match order (1st SIDDHI = hex 1)
        "section_start": "SIDDHI BEAUTY",  # skip INTRODUCTION table
        "include_match": True,  # chunk includes SIDDHI line and full content
    },
    "Yi Jing (Human Design 1) - Ra Uru Hu.txt": {
        "pattern": HUMAN_DESIGN_PATTERN,
        "extract_num": True,
    },
    "Yi Jing (Psychological 1) - Richard Wilhelm.txt": {
        "pattern": WILHELM_PATTERN,
        "extract_num": True,
        "prefer_largest": True,
    },
}

ROMAN_TO_NUM = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20, "XXI": 21, "XXII": 22,
    "XXIII": 23, "XXIV": 24, "XXV": 25, "XXVI": 26, "XXVII": 27, "XXVIII": 28,
    "XXIX": 29, "XXX": 30, "XXXI": 31, "XXXII": 32, "XXXIII": 33, "XXXIV": 34,
    "XXXV": 35, "XXXVI": 36, "XXXVII": 37, "XXXVIII": 38, "XXXIX": 39, "XL": 40,
    "XLI": 41, "XLII": 42, "XLIII": 43, "XLIV": 44, "XLV": 45, "XLVI": 46,
    "XLVII": 47, "XLVIII": 48, "XLIX": 49, "L": 50, "LI": 51, "LII": 52,
    "LIII": 53, "LIV": 54, "LV": 55, "LVI": 56, "LVII": 57, "LVIII": 58,
    "LIX": 59, "LX": 60, "LXI": 61, "LXII": 62, "LXIII": 63, "LXIV": 64,
}


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().replace("\r\n", "\n").replace("\r", "\n")


def debug_missing_hex(text: str, pattern: re.Pattern, extract_num: bool = True) -> None:
    """Print which hex numbers (1-64) are missing from regex matches."""
    matches = list(pattern.finditer(text))
    found = set()
    for m in matches:
        if extract_num and "num" in m.groupdict():
            n = int(m.group("num"))
        else:
            continue
        if 1 <= n <= 64:
            found.add(n)
    missing = sorted(set(range(1, 65)) - found)
    if missing:
        print(f"DEBUG: Missing hex numbers: {missing}", file=sys.stderr)
    else:
        print("DEBUG: All 64 hex numbers found.", file=sys.stderr)


def split_by_pattern(text: str, config: dict) -> dict[int, str]:
    """Split text into chunks using the book's pattern. Returns {1: chunk1, 2: chunk2, ...}."""
    raw_pattern = config["pattern"]
    pattern = raw_pattern if isinstance(raw_pattern, re.Pattern) else raw_pattern[0]
    if config.get("multi_pattern") and isinstance(raw_pattern, list):
        matches = []
        for p in raw_pattern:
            matches.extend(p.finditer(text))
        matches.sort(key=lambda m: m.start())
    else:
        matches = list(pattern.finditer(text))
    extract_num = config.get("extract_num", True)
    prefer_largest = config.get("prefer_largest_chunk", False)  # for books with TOC + body
    include_match = config.get("include_match", False)  # chunk starts at match, not after

    candidates: dict[int, list[tuple[int, int, int]]] = {}  # num -> [(start, end, chunk_len)]

    for i, m in enumerate(matches):
        if extract_num and "num" in m.groupdict():
            num = int(m.group("num"))
        elif not extract_num and m.lastindex and m.lastindex >= 1:
            roman = m.group(1)
            num = ROMAN_TO_NUM.get(roman.upper(), i + 1)
        else:
            num = i + 1

        if num < 1 or num > 64:
            continue
        start = m.start() if include_match else m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk_len = end - start
        if num not in candidates:
            candidates[num] = []
        candidates[num].append((start, end, chunk_len))

    chunks: dict[int, str] = {}
    for num in range(1, 65):
        if num not in candidates:
            continue
        cands = candidates[num]
        if prefer_largest:
            # Prefer largest; if tied, prefer first non-empty
            cands_sorted = sorted(cands, key=lambda x: (-x[2], x[0]))
        else:
            cands_sorted = [cands[-1]]
        for start, end, _ in cands_sorted:
            chunk = text[start:end].strip()
            if chunk:
                chunks[num] = chunk
                break

    return chunks


def chunks_from_main_content(text: str, config: dict) -> dict[int, str]:
    """Apply section limits if specified, then split by pattern."""
    section_start = config.get("section_start")
    section_end = config.get("section_end")
    if section_start is not None:
        idx = text.find(section_start)
        if idx >= 0:
            text = text[idx:]
    if section_end is not None:
        idx = text.find(section_end)
        if idx >= 0:
            text = text[:idx]
    return split_by_pattern(text, config)


def main() -> int:
    root = project_root()
    raw_dir = root / "data" / "raw"
    chunked_base = root / "data" / "chunked"

    if not raw_dir.exists():
        print("ERROR: data/raw/ not found.", file=sys.stderr)
        return 1

    success_count = 0
    fail_count = 0

    for filename, folder_slug in FOLDER_MAP.items():
        if filename not in BOOK_CONFIG:
            print(f"SKIP: {filename} (no config)", file=sys.stderr)
            continue

        path = raw_dir / filename
        if not path.exists():
            print(f"SKIP: {filename} (file not found)", file=sys.stderr)
            fail_count += 1
            continue

        text = read_text(path)
        config = BOOK_CONFIG[filename]
        chunks = chunks_from_main_content(text, config)

        chunk_count = len(chunks)
        if chunk_count != 64:
            print(
                f"ERROR: {filename} yielded {chunk_count} chunks. Regex needs refinement.",
                file=sys.stderr,
            )
            # Debug: which hex numbers are missing from matches
            section_text = text
            if config.get("section_start"):
                idx = text.find(config["section_start"])
                if idx >= 0:
                    section_text = text[idx:]
            if config.get("section_end"):
                idx = section_text.find(config["section_end"])
                if idx >= 0:
                    section_text = section_text[:idx]
            pat = config["pattern"]
            debug_missing_hex(
                section_text,
                pat[0] if isinstance(pat, list) else pat,
                config.get("extract_num", True),
            )
            fail_count += 1
            continue

        out_dir = chunked_base / folder_slug
        out_dir.mkdir(parents=True, exist_ok=True)

        for num in range(1, 65):
            if num not in chunks:
                print(
                    f"ERROR: {filename} missing chunk {num}. Regex needs refinement.",
                    file=sys.stderr,
                )
                fail_count += 1
                break
            out_path = out_dir / f"hex_{num:02d}.txt"
            out_path.write_text(chunks[num], encoding="utf-8")
        else:
            print(f"OK: {filename} -> {folder_slug}/ (64 chunks)")
            success_count += 1

    print("---")
    print(f"Done: {success_count} succeeded, {fail_count} failed.")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
