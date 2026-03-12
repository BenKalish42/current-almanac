#!/usr/bin/env python3
"""
Transform data/output/seed_formulas.json (Shanghan Lun schema) to
src/data/seed_formulas.json (app schema) for Alchemy integration.

Schema mapping:
- english_name -> common_name
- architecture: herb_pinyin, role, classical_dosage -> herb_id, pinyin_name, role (Jun/Chen/Zuo/Shi), dosage_percentage, purpose
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "output" / "seed_formulas.json"
OUTPUT_PATH = PROJECT_ROOT / "src" / "data" / "seed_formulas.json"
HERBS_PATH = PROJECT_ROOT / "src" / "data" / "seed_herbs.json"

ROLE_MAP = {
    "King": "King (Jun)",
    "Minister": "Minister (Chen)",
    "Assistant": "Assistant (Zuo)",
    "Envoy": "Envoy (Shi)",
}

# Common pinyin aliases: formula name -> seed_herbs pinyin_name
PINYIN_ALIASES = {
    "Gan Cao": "Zhi Gan Cao",  # Licorice: raw vs honey-fried
    "Shao Yao": "Bai Shao",    # Peony: Shao Yao = Bai Shao
    "Ban Xia": "Zhi Ban Xia",  # Pinellia: raw vs prepared
}


def slug(s: str) -> str:
    """Convert 'Gui Zhi' -> 'gui_zhi' for synthetic herb_id."""
    return re.sub(r"[^a-z0-9]+", "_", s.lower().strip()).strip("_") or "unknown"


def parse_classical_dosage(d: str) -> float:
    """
    Parse classical dosage to a numeric weight for relative percentage.
    liang ~ 1 unit, jin ~ 16 liang, ge ~ 0.1, pieces ~ 0.01 each, sheng ~ 10.
    """
    if not d or not isinstance(d, str):
        return 1.0
    d = d.strip().lower()
    m = re.search(r"([\d.]+)\s*(\w+)", d)
    if not m:
        return 1.0
    num = float(m.group(1))
    unit = m.group(2)
    if "liang" in unit:
        return num
    if "jin" in unit:
        return num * 16
    if "ge" in unit or "个" in unit:
        return num * 0.1
    if "piece" in unit or "pieces" in unit or "枚" in unit or "个" in unit:
        return num * 0.01
    if "sheng" in unit or "升" in unit:
        return num * 2  # approximate
    return num


def build_pinyin_to_herb_id(herbs: list[dict]) -> dict[str, str]:
    """Build pinyin_name -> herb_id map, with aliases."""
    m: dict[str, str] = {}
    for h in herbs:
        pid = h.get("id", "")
        pinyin = h.get("pinyin_name", "")
        if pid and pinyin:
            m[pinyin] = pid
            # Also add normalized (lowercase, no parens) for fuzzy match
            norm = pinyin.lower().replace(" (zhi)", "").replace("(zhi)", "").strip()
            if norm and norm not in m:
                m[norm] = pid
    return m


def resolve_herb_id(pinyin: str, pinyin_map: dict[str, str]) -> str:
    """Resolve herb_pinyin to herb_id. Use synthetic id if not in seed_herbs."""
    if not pinyin:
        return "herb_unknown"
    # Exact match
    if pinyin in pinyin_map:
        return pinyin_map[pinyin]
    # Alias
    alias = PINYIN_ALIASES.get(pinyin)
    if alias and alias in pinyin_map:
        return pinyin_map[alias]
    # Synthetic
    return f"herb_{slug(pinyin)}"


def transform_architecture(
    arch: list[dict],
    pinyin_map: dict[str, str],
    primary_action: str,
) -> list[dict]:
    """Convert extracted architecture to app schema."""
    if not arch:
        return []
    weights: list[tuple[dict, float]] = []
    for entry in arch:
        herb_pinyin = entry.get("herb_pinyin", "")
        role_raw = entry.get("role", "")
        role = ROLE_MAP.get(role_raw, role_raw)
        classical = entry.get("classical_dosage", "1 liang")
        weight = parse_classical_dosage(classical)
        herb_id = resolve_herb_id(herb_pinyin, pinyin_map)
        weights.append(
            (
                {
                    "role": role,
                    "herb_id": herb_id,
                    "pinyin_name": herb_pinyin,
                    "purpose": primary_action or "Classical role in formula",
                },
                weight,
            )
        )
    total = sum(w for _, w in weights)
    if total <= 0:
        total = 1
    result = []
    for d, w in weights:
        d["dosage_percentage"] = round((w / total) * 100, 2)
        result.append(d)
    return result


def transform_formula(f: dict, pinyin_map: dict[str, str]) -> dict:
    """Transform one formula to app schema."""
    actions = f.get("actions", [])
    primary_action = actions[0] if actions else ""
    arch = transform_architecture(
        f.get("architecture", []),
        pinyin_map,
        primary_action,
    )
    return {
        "id": f.get("id", ""),
        "pinyin_name": f.get("pinyin_name", ""),
        "common_name": f.get("english_name", f.get("common_name", "")),
        "primary_pattern": f.get("primary_pattern", ""),
        "actions": actions,
        "architecture": arch,
        "safety_note": f.get("safety_note", ""),
    }


def main() -> None:
    with open(INPUT_PATH, encoding="utf-8") as f:
        formulas = json.load(f)
    with open(HERBS_PATH, encoding="utf-8") as f:
        herbs = json.load(f)
    pinyin_map = build_pinyin_to_herb_id(herbs)
    transformed = [transform_formula(f, pinyin_map) for f in formulas]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(transformed, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(transformed)} formulas to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
