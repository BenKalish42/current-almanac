#!/usr/bin/env python3
"""
Phase 1.5 Task 11.10: HuggingFace BATMAN-TCM 2.0 Formula ETL.

Streams insilicomedicine/batman2, extracts formula structures, maps Jun/Chen/Zuo/Shi
and dosage data to local schema, and writes src/data/formulas.json.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import load_dataset


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data"
HERBS_PATH = DATA_DIR / "herbs.json"
SEED_HERBS_PATH = DATA_DIR / "seed_herbs.json"
OUTPUT_PATH = DATA_DIR / "formulas.json"


def slugify(value: str) -> str:
    """ASCII-safe normalization to underscore slug."""
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower().strip()
    ascii_text = re.sub(r"[^\w\s-]", " ", ascii_text)
    ascii_text = re.sub(r"[\s\-]+", "_", ascii_text)
    ascii_text = re.sub(r"_+", "_", ascii_text).strip("_")
    return ascii_text


def first_non_empty(row: pd.Series, keys: list[str]) -> Any:
    for key in keys:
        if key in row and pd.notna(row[key]) and str(row[key]).strip():
            return row[key]
    return None


def parse_number(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return 0.0
    return 0.0


def normalize_role(role_value: Any) -> str:
    role = str(role_value or "").strip().lower()
    if role in {"jun", "king", "chief", "emperor"}:
        return "Jun"
    if role in {"chen", "minister", "deputy"}:
        return "Chen"
    if role in {"zuo", "assistant", "adjuvant"}:
        return "Zuo"
    if role in {"shi", "envoy", "guide", "courier"}:
        return "Shi"
    return "Zuo"


def load_local_herbs() -> list[dict[str, Any]]:
    source_path = HERBS_PATH if HERBS_PATH.exists() else SEED_HERBS_PATH
    if not source_path.exists():
        raise FileNotFoundError(f"Could not find local herb DB at {HERBS_PATH} or {SEED_HERBS_PATH}")
    with open(source_path, encoding="utf-8") as f:
        herbs = json.load(f)
    if not isinstance(herbs, list):
        raise ValueError(f"Expected list in {source_path}, got {type(herbs)}")
    print(f"Loaded local herbs from: {source_path}")
    return herbs


def build_herb_lookup(herbs: list[dict[str, Any]]) -> dict[str, str]:
    """
    Build multi-key lookup:
    - herb id slug
    - pinyin/common/english names
    - aliases
    """
    lookup: dict[str, str] = {}
    for herb in herbs:
        herb_id = str(herb.get("id", "")).strip()
        if not herb_id:
            continue
        keys = {
            slugify(herb_id),
            slugify(herb_id.replace("herb_", "")),
            slugify(str(herb.get("pinyin_name", ""))),
            slugify(str(herb.get("common_name", ""))),
            slugify(str(herb.get("english_name", ""))),
        }
        for alias in herb.get("aliases", []) if isinstance(herb.get("aliases"), list) else []:
            keys.add(slugify(str(alias)))
        for key in keys:
            if key:
                lookup[key] = herb_id
    return lookup


def normalize_herb_id(raw_name: Any, herb_lookup: dict[str, str]) -> str | None:
    """
    Converts BATMAN herb naming to local herb_id.
    Example: "Chai Hu" -> herb_chai_hu (if present in local DB).
    """
    if raw_name is None:
        return None
    text = str(raw_name).strip()
    if not text:
        return None

    key = slugify(text)
    candidates = [
        key,
        key.replace("herb_", ""),
        f"herb_{key}",
    ]
    for candidate in candidates:
        resolved = herb_lookup.get(candidate)
        if resolved:
            return resolved
    return None


def parse_ingredients_payload(payload: Any) -> list[dict[str, Any]]:
    """
    Normalizes heterogeneous BATMAN ingredient encodings to list[dict].
    """
    if payload is None:
        return []

    if isinstance(payload, list):
        normalized: list[dict[str, Any]] = []
        for item in payload:
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append({"herb_name": item})
        return normalized

    if isinstance(payload, dict):
        return [payload]

    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return []

        # Try JSON list/dict encoded as string
        if (text.startswith("[") and text.endswith("]")) or (text.startswith("{") and text.endswith("}")):
            try:
                decoded = json.loads(text)
                return parse_ingredients_payload(decoded)
            except json.JSONDecodeError:
                pass

        # Fallback: split comma/semicolon separated names
        parts = [p.strip() for p in re.split(r"[;,]", text) if p.strip()]
        return [{"herb_name": p} for p in parts]

    return []


def extract_ingredient_entries(row: pd.Series) -> list[dict[str, Any]]:
    """
    Supports:
    - nested list columns: herb_list / ingredients / composition
    - flat row columns: herb_name + role_label + dosage
    """
    list_payload = first_non_empty(
        row,
        [
            "herb_list",
            "ingredients",
            "ingredient_list",
            "composition",
            "formula_composition",
        ],
    )
    entries = parse_ingredients_payload(list_payload)
    if entries:
        return entries

    herb_name = first_non_empty(
        row,
        [
            "herb_name",
            "ingredient_name",
            "name",
            "drug_name",
            "pinyin_name",
            "latin_name",
        ],
    )
    if herb_name is None:
        return []

    return [
        {
            "herb_name": herb_name,
            "role_label": first_non_empty(row, ["role_label", "role", "position", "jczzs_role"]),
            "dosage": first_non_empty(row, ["dosage", "dose", "weight", "amount", "ratio"]),
        }
    ]


def extract_formula_name(row: pd.Series) -> tuple[str, str]:
    pinyin = first_non_empty(
        row,
        [
            "formula_name",
            "formula_name_pinyin",
            "prescription_name",
            "name_pinyin",
            "name",
            "formula",
        ],
    )
    hanzi = first_non_empty(
        row,
        [
            "formula_name_hanzi",
            "formula_name_cn",
            "formula_cn",
            "name_hanzi",
            "name_zh",
        ],
    )
    pinyin_str = str(pinyin).strip() if pinyin is not None else ""
    hanzi_str = str(hanzi).strip() if hanzi is not None else ""
    if not pinyin_str:
        # last-resort synthetic name
        pinyin_str = "Unknown Formula"
    return pinyin_str, hanzi_str


def extract_brand_name(row: pd.Series) -> str:
    brand = first_non_empty(
        row,
        [
            "brand_name",
            "manufacturer",
            "market_variant",
            "product_name",
            "company",
        ],
    )
    return str(brand).strip() if brand is not None else "BATMAN-TCM 2.0 Reference"


def choose_split(dataset_dict: Any) -> str:
    preferred = ["train", "validation", "test"]
    for split in preferred:
        if split in dataset_dict:
            return split
    keys = list(dataset_dict.keys())
    if not keys:
        raise ValueError("No splits found in dataset.")
    return keys[0]


def main() -> int:
    herbs = load_local_herbs()
    herb_lookup = build_herb_lookup(herbs)

    dataset = load_dataset("insilicomedicine/batman2")
    split_name = choose_split(dataset)
    df = dataset[split_name].to_pandas()

    classical_by_key: dict[str, dict[str, Any]] = {}
    edge_accumulator: dict[tuple[str, str, str], float] = defaultdict(float)
    variant_map: dict[tuple[str, str], dict[str, Any]] = {}

    for _, row in df.iterrows():
        formula_name_pinyin, formula_name_hanzi = extract_formula_name(row)
        formula_slug = slugify(formula_name_pinyin) or "unknown_formula"
        formula_id = f"classical_{formula_slug}"

        if formula_id not in classical_by_key:
            classical_by_key[formula_id] = {
                "id": formula_id,
                "name_hanzi": formula_name_hanzi,
                "name_pinyin": formula_name_pinyin,
                "linguistics": {"cantonese": "", "taiwanese": ""},
                "source_text": str(first_non_empty(row, ["source_text", "source", "text_source"]) or "BATMAN-TCM 2.0"),
                "description": str(first_non_empty(row, ["description", "indication", "formula_desc"]) or ""),
            }

        ingredient_entries = extract_ingredient_entries(row)
        if not ingredient_entries:
            continue

        brand_name = extract_brand_name(row)
        variant_key = (formula_id, brand_name)
        if variant_key not in variant_map:
            variant_map[variant_key] = {
                "id": f"market_{formula_slug}_{slugify(brand_name) or 'reference'}",
                "brand_name": brand_name,
                "formula_id": formula_id,
                "actual_ingredients": [],
                "has_shadow_nodes": False,
            }
        variant_actual_ingredients = variant_map[variant_key]["actual_ingredients"]

        for entry in ingredient_entries:
            herb_name = (
                entry.get("herb_name")
                or entry.get("name")
                or entry.get("ingredient")
                or entry.get("pinyin_name")
                or entry.get("latin_name")
            )
            herb_id = normalize_herb_id(herb_name, herb_lookup)
            if not herb_id:
                # Strict bridge requirement: only mapped local herbs are included.
                continue

            role = normalize_role(entry.get("role_label") or entry.get("role") or row.get("role_label"))
            dosage = parse_number(entry.get("dosage") or entry.get("dose") or entry.get("amount") or row.get("dosage"))
            if dosage <= 0:
                dosage = 1.0

            edge_accumulator[(formula_id, herb_id, role)] += dosage
            variant_actual_ingredients.append(
                {
                    "herb_id": herb_id,
                    "exact_dosage_grams": dosage,
                }
            )

    # Deduplicate variant ingredient lines by summing herb dosages per variant.
    market_variants: list[dict[str, Any]] = []
    for variant in variant_map.values():
        dosage_by_herb: dict[str, float] = defaultdict(float)
        for item in variant["actual_ingredients"]:
            dosage_by_herb[item["herb_id"]] += float(item.get("exact_dosage_grams", 0))
        variant["actual_ingredients"] = [
            {"herb_id": herb_id, "exact_dosage_grams": round(dose, 6)}
            for herb_id, dose in sorted(dosage_by_herb.items(), key=lambda kv: kv[0])
        ]
        market_variants.append(variant)

    formula_ingredients = [
        {
            "formula_id": formula_id,
            "herb_id": herb_id,
            "role": role,
            "classical_dosage_ratio": round(dosage, 6),
        }
        for (formula_id, herb_id, role), dosage in sorted(edge_accumulator.items())
    ]

    payload = {
        "classical_formulas": list(classical_by_key.values()),
        "formula_ingredients": formula_ingredients,
        "market_variants": market_variants,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(
        f"Successfully ingested {len(payload['classical_formulas'])} formulas and "
        f"{len(payload['formula_ingredients'])} edges from BATMAN-TCM 2.0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
