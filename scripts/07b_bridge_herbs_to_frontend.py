#!/usr/bin/env python3
"""
Bridge script: Map data/output/seed_herbs.json to Alchemy UI schema.
Output: src/data/seed_herbs.json (overwrites existing 18-herb file).
"""

import json
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "output" / "seed_herbs.json"
OUTPUT_PATH = ROOT / "src" / "data" / "seed_herbs.json"

# Temperature keywords (case-insensitive); property contains one of these → temperature
TEMPERATURE_KEYWORDS = (
    "cold", "cool", "warm", "hot", "calm", "neutral",
    "slightly cold", "slightly cool", "slightly warm", "slightly hot",
    "very cold", "very warm", "extremely hot"
)


def extract_temperature(properties: list[str]) -> str:
    """Extract temperature from properties array. Returns first match or 'Neutral'."""
    if not properties:
        return "Neutral"
    for p in properties:
        lower = p.strip().lower()
        for kw in TEMPERATURE_KEYWORDS:
            if kw in lower or lower == kw:
                return p.strip()
    return "Neutral"


def extract_flavor(properties: list[str], temperature: str) -> list[str]:
    """Extract flavor terms (everything not temperature)."""
    if not properties:
        return []
    flavor = []
    temp_lower = temperature.lower()
    for p in properties:
        lower = p.strip().lower()
        # Skip if it's a temperature term
        is_temp = any(kw in lower for kw in TEMPERATURE_KEYWORDS)
        if not is_temp:
            flavor.append(p.strip())
    return flavor


def map_herb(raw: dict) -> dict:
    """Map a raw output herb to the Alchemy UI schema."""
    props_arr = raw.get("properties") or []
    temp = extract_temperature(props_arr)
    flavor = extract_flavor(props_arr, temp)
    meridians = raw.get("meridians") or []

    return {
        "id": raw.get("id", ""),
        "pinyin_name": raw.get("pinyin_name", ""),
        "common_name": raw.get("english_name") or raw.get("chinese_name", ""),
        "safety_tier": raw.get("safety_tier", 1),
        "properties": {
            "temperature": temp,
            "flavor": flavor,
            "meridians": meridians,
        },
        "actions": ["Harmonizes systemic function"],
        "contraindications": "",
    }


def main() -> None:
    with open(INPUT_PATH, encoding="utf-8") as f:
        raw_herbs = json.load(f)

    mapped = [map_herb(h) for h in raw_herbs]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(mapped, f, indent=2, ensure_ascii=False)

    print(f"Bridged {len(mapped)} herbs from {INPUT_PATH} → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
