#!/usr/bin/env python3
"""
Phase 5: The Master Herb Fusion.
Convert SymMap SMHB file (XLSX or CSV) into production-ready seed_herbs.json for the database.

Input: data/raw/SymMap v2.0, SMHB file.xlsx (or .csv if exported)
Output: data/output/seed_herbs.json
"""

import csv
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False
    pd = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_XLSX = PROJECT_ROOT / "data" / "raw" / "SymMap v2.0, SMHB file.xlsx"
INPUT_CSV = PROJECT_ROOT / "data" / "raw" / "SymMap v2.0, SMHB file.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "output" / "seed_herbs.json"


def _col_from_keys(keys: list[str], *candidates: str) -> str | None:
    """Find first matching column (case-insensitive) from list of keys."""
    key_lower = {k.strip().lower(): k for k in keys if isinstance(k, str)}
    for cand in candidates:
        key = cand.strip().lower()
        if key in key_lower:
            return key_lower[key]
    return None


def _safe_str(val) -> str:
    """Convert value to string, empty if NaN/None."""
    if val is None:
        return ""
    s = str(val).strip()
    return "" if not s or s.lower() == "nan" else s


def _split_list(val, sep: str = ",") -> list[str]:
    """Split string by separator, strip each item, filter empties."""
    if val is None:
        return []
    s = str(val).strip()
    if not s:
        return []
    return [x.strip() for x in s.split(sep) if x.strip()]


def _safety_tier(properties_str: str) -> int:
    """
    CRITICAL: Derive safety_tier from Properties_English.
    - "Toxic" -> 3
    - "Slightly Toxic" -> 2
    - Otherwise -> 1
    """
    if not properties_str:
        return 1
    s = str(properties_str).strip().lower()
    if "toxic" in s:
        if "slightly toxic" in s:
            return 2
        return 3
    return 1


def _col(df, *candidates: str) -> str | None:
    """Find first matching column (case-insensitive). For pandas DataFrame."""
    return _col_from_keys(list(df.columns), *candidates)


def _is_real_csv(path: Path) -> bool:
    """CSV files are plain text; Excel/OLE files start with D0 CF 11 E0."""
    with open(path, "rb") as f:
        header = f.read(8)
    return not (len(header) >= 4 and header[:4] == b"\xd0\xcf\x11\xe0")


def _col_idx(letter: str) -> int:
    """A=0, B=1, ..., Z=25, AA=26, etc."""
    n = 0
    for c in letter.upper():
        n = n * 26 + (ord(c) - ord("A") + 1)
    return n - 1


def _read_xlsx_stdlib(path: Path) -> list[dict]:
    """Read XLSX using only stdlib (zipfile + xml.etree). Returns list of row dicts."""
    NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    shared_strings: list[str] = []

    with zipfile.ZipFile(path, "r") as zf:
        # Load shared strings
        if "xl/sharedStrings.xml" in zf.namelist():
            with zf.open("xl/sharedStrings.xml") as f:
                tree = ET.parse(f)
                for si in tree.getroot().findall("main:si", NS):
                    parts = []
                    for t in si.findall(".//main:t", NS):
                        if t.text:
                            parts.append(t.text)
                    shared_strings.append("".join(parts) if parts else "")

        # Load first sheet
        sheet_path = "xl/worksheets/sheet1.xml"
        if sheet_path not in zf.namelist():
            raise ValueError(f"No sheet1 in XLSX: {path}")

        with zf.open(sheet_path) as f:
            tree = ET.parse(f)
            root = tree.getroot()

        rows_data: list[list[str]] = []
        for row_elem in root.findall(".//main:row", NS):
            row_idx = int(row_elem.get("r", 0))
            cells: list[tuple[int, str]] = []
            for c in row_elem.findall("main:c", NS):
                ref = c.get("r", "")
                col_letter = re.sub(r"\d+", "", ref)
                col_idx = _col_idx(col_letter) if col_letter else len(cells)
                cell_type = c.get("t", "n")
                v_elem = c.find("main:v", NS)
                val = v_elem.text if v_elem is not None and v_elem.text else ""
                if cell_type == "s" and val.isdigit():
                    idx = int(val)
                    val = shared_strings[idx] if idx < len(shared_strings) else ""
                cells.append((col_idx, val))
            if cells:
                max_col = max(col for col, _ in cells)
                row_vals = [""] * (max_col + 1)
                for col, v in cells:
                    row_vals[col] = v
                rows_data.append(row_vals)

    if not rows_data:
        return []

    # First row = headers
    headers = [str(h).strip() for h in rows_data[0]]
    rows: list[dict] = []
    for row_vals in rows_data[1:]:
        row = {}
        for i, h in enumerate(headers):
            if i < len(row_vals):
                row[h] = row_vals[i]
            else:
                row[h] = ""
        rows.append(row)
    return rows


def _read_csv_stdlib(path: Path) -> list[dict]:
    """Read CSV using stdlib. Returns list of row dicts."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _load_rows() -> list[dict]:
    """Load herb rows from XLSX or CSV. Uses pandas if available, else stdlib."""
    if INPUT_XLSX.exists():
        if _HAS_PANDAS:
            try:
                df = pd.read_excel(INPUT_XLSX, engine="openpyxl")
                return [row.to_dict() for _, row in df.iterrows()]
            except ImportError:
                pass
        return _read_xlsx_stdlib(INPUT_XLSX)
    if INPUT_CSV.exists() and _is_real_csv(INPUT_CSV):
        if _HAS_PANDAS:
            try:
                df = pd.read_csv(INPUT_CSV, encoding="utf-8")
                return [row.to_dict() for _, row in df.iterrows()]
            except Exception:
                pass
        return _read_csv_stdlib(INPUT_CSV)
    raise FileNotFoundError(
        f"SymMap file not found. Expected:\n  {INPUT_XLSX}\n"
        "Download from http://www.symmap.org/download/ (SMHB file)."
    )


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = _load_rows()
    if not rows:
        raise ValueError("No rows loaded from SymMap file.")

    # Resolve column names (SymMap v2 SMHB schema)
    keys = list(rows[0].keys()) if rows else []
    if len(rows) < 2:
        raise ValueError(f"Only header row loaded. Keys: {keys}")
    pinyin_col = _col_from_keys(keys, "Pinyin_name", "pinyin_name")
    chinese_col = _col_from_keys(keys, "Chinese_name", "chinese_name")
    english_col = _col_from_keys(keys, "English_name", "english_name")
    meridians_col = _col_from_keys(keys, "Meridians_English", "meridians_english")
    properties_col = _col_from_keys(keys, "Properties_English", "properties_english")
    tcmsp_col = _col_from_keys(keys, "TCMSP_id", "tcmsp_id")
    tcmid_col = _col_from_keys(keys, "TCMID_id", "tcmid_id")
    suppress_col = _col_from_keys(keys, "Suppress", "suppress")

    if not pinyin_col or not chinese_col:
        raise ValueError(
            f"Required columns not found. Available: {keys}\n"
            "Expected: Pinyin_name, Chinese_name, English_name, Meridians_English, "
            "Properties_English, TCMSP_id, TCMID_id"
        )

    herbs: list[dict] = []
    for row in rows:
        pinyin = _safe_str(row.get(pinyin_col, ""))
        chinese = _safe_str(row.get(chinese_col, ""))
        if not pinyin or not chinese:
            continue
        if suppress_col:
            supp = _safe_str(row.get(suppress_col, ""))
            if supp and supp.lower() not in ("0", "false", "no", ""):
                continue

        properties_str = _safe_str(row.get(properties_col, "")) if properties_col else ""
        meridians_str = _safe_str(row.get(meridians_col, "")) if meridians_col else ""

        herb_id = f"herb_sym_{len(herbs) + 1:03d}"

        external_ids: dict[str, str] = {}
        if tcmsp_col:
            v = _safe_str(row.get(tcmsp_col, ""))
            if v:
                external_ids["TCMSP_id"] = v
        if tcmid_col:
            v = _safe_str(row.get(tcmid_col, ""))
            if v:
                external_ids["TCMID_id"] = v

        obj: dict = {
            "id": herb_id,
            "pinyin_name": pinyin,
            "chinese_name": chinese,
            "english_name": _safe_str(row.get(english_col, "")) if english_col else "",
            "meridians": _split_list(meridians_str),
            "properties": _split_list(properties_str),
            "safety_tier": _safety_tier(properties_str),
        }
        if external_ids:
            obj["external_ids"] = external_ids

        herbs.append(obj)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(herbs, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(herbs)} herbs to {OUTPUT_PATH}")
    if herbs:
        sample = herbs[0]
        print(
            f"Sample: {sample['pinyin_name']} ({sample['chinese_name']}) - "
            f"tier {sample['safety_tier']}"
        )


if __name__ == "__main__":
    main()
