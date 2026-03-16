#!/usr/bin/env python3
"""
Phase 1.5 Task 11.0: Build Master Formula Graph seed payload.

Creates src/data/formulas.json with:
- classical_formulas nodes
- formula_ingredients edges
- market_variants nodes
"""

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "src" / "data" / "formulas.json"


def build_payload() -> dict[str, Any]:
    # Two classical formula blueprint nodes
    classical_formulas = [
        {
            "id": "classical_liu_wei_di_huang_wan",
            "name_hanzi": "六味地黄丸",
            "name_pinyin": "Liu Wei Di Huang Wan",
            "linguistics": {
                "cantonese": "luk6 mei6 dei6 wong4 jyun4",
                "taiwanese": "la̍k-bī tē-hông-oân",
            },
            "source_text": "Xiao Er Yao Zheng Zhi Jue",
            "description": (
                "Foundational Kidney Yin tonic formula that nourishes Liver-Kidney Yin "
                "with Shu Di Huang as the core herb."
            ),
        },
        {
            "id": "classical_bao_he_wan",
            "name_hanzi": "保和丸",
            "name_pinyin": "Bao He Wan",
            "linguistics": {
                "cantonese": "bou2 wo4 jyun4",
                "taiwanese": "pó-hô-oân",
            },
            "source_text": "Dan Xi Xin Fa",
            "description": (
                "Food stagnation resolving formula that reduces clumping, transforms "
                "phlegm, and supports middle burner movement."
            ),
        },
    ]

    # Ingredient edges between classical formula nodes and herb nodes
    formula_ingredients = [
        # Liu Wei Di Huang Wan
        {
            "formula_id": "classical_liu_wei_di_huang_wan",
            "herb_id": "herb_shu_di_huang",
            "role": "Jun",
            "classical_dosage_ratio": 8.0,
        },
        {
            "formula_id": "classical_liu_wei_di_huang_wan",
            "herb_id": "herb_shan_zhu_yu",
            "role": "Chen",
            "classical_dosage_ratio": 4.0,
        },
        {
            "formula_id": "classical_liu_wei_di_huang_wan",
            "herb_id": "herb_shan_yao",
            "role": "Chen",
            "classical_dosage_ratio": 4.0,
        },
        {
            "formula_id": "classical_liu_wei_di_huang_wan",
            "herb_id": "herb_ze_xie",
            "role": "Zuo",
            "classical_dosage_ratio": 3.0,
        },
        {
            "formula_id": "classical_liu_wei_di_huang_wan",
            "herb_id": "herb_fu_ling",
            "role": "Zuo",
            "classical_dosage_ratio": 3.0,
        },
        {
            "formula_id": "classical_liu_wei_di_huang_wan",
            "herb_id": "herb_mu_dan_pi",
            "role": "Shi",
            "classical_dosage_ratio": 3.0,
        },
        # Bao He Wan
        {
            "formula_id": "classical_bao_he_wan",
            "herb_id": "herb_shan_zha",
            "role": "Jun",
            "classical_dosage_ratio": 6.0,
        },
        {
            "formula_id": "classical_bao_he_wan",
            "herb_id": "herb_shen_qu",
            "role": "Chen",
            "classical_dosage_ratio": 2.0,
        },
        {
            "formula_id": "classical_bao_he_wan",
            "herb_id": "herb_lai_fu_zi",
            "role": "Chen",
            "classical_dosage_ratio": 2.0,
        },
        {
            "formula_id": "classical_bao_he_wan",
            "herb_id": "herb_ban_xia",
            "role": "Zuo",
            "classical_dosage_ratio": 3.0,
        },
        {
            "formula_id": "classical_bao_he_wan",
            "herb_id": "herb_fu_ling",
            "role": "Zuo",
            "classical_dosage_ratio": 3.0,
        },
        {
            "formula_id": "classical_bao_he_wan",
            "herb_id": "herb_lian_qiao",
            "role": "Shi",
            "classical_dosage_ratio": 1.0,
        },
    ]

    # Market product nodes that point to classical formula nodes
    market_variants = [
        {
            "id": "market_liu_wei_plum_flower",
            "brand_name": "Plum Flower",
            "formula_id": "classical_liu_wei_di_huang_wan",
            "actual_ingredients": [
                {"herb_id": "herb_shu_di_huang", "exact_dosage_grams": 1.60},
                {"herb_id": "herb_shan_zhu_yu", "exact_dosage_grams": 0.80},
                {"herb_id": "herb_shan_yao", "exact_dosage_grams": 0.80},
                {"herb_id": "herb_ze_xie", "exact_dosage_grams": 0.60},
                {"herb_id": "herb_fu_ling", "exact_dosage_grams": 0.60},
                {"herb_id": "herb_mu_dan_pi", "exact_dosage_grams": 0.60},
            ],
            "has_shadow_nodes": False,
        },
        {
            "id": "market_liu_wei_solstice",
            "brand_name": "Solstice",
            "formula_id": "classical_liu_wei_di_huang_wan",
            "actual_ingredients": [
                {"herb_id": "herb_shu_di_huang", "exact_dosage_grams": 1.55},
                {"herb_id": "herb_shan_zhu_yu", "exact_dosage_grams": 0.75},
                {"herb_id": "herb_shan_yao", "exact_dosage_grams": 0.78},
                {"herb_id": "herb_ze_xie", "exact_dosage_grams": 0.62},
                {"herb_id": "herb_fu_ling", "exact_dosage_grams": 0.60},
                {"herb_id": "herb_mu_dan_pi", "exact_dosage_grams": 0.58},
            ],
            "has_shadow_nodes": True,
        },
        {
            "id": "market_bao_he_solstice",
            "brand_name": "Solstice",
            "formula_id": "classical_bao_he_wan",
            "actual_ingredients": [
                {"herb_id": "herb_shan_zha", "exact_dosage_grams": 1.20},
                {"herb_id": "herb_shen_qu", "exact_dosage_grams": 0.42},
                {"herb_id": "herb_lai_fu_zi", "exact_dosage_grams": 0.42},
                {"herb_id": "herb_ban_xia", "exact_dosage_grams": 0.60},
                {"herb_id": "herb_fu_ling", "exact_dosage_grams": 0.60},
                {"herb_id": "shadow_herb_lian_qiao", "exact_dosage_grams": 0.20},
            ],
            "has_shadow_nodes": True,
        },
    ]

    return {
        "classical_formulas": classical_formulas,
        "formula_ingredients": formula_ingredients,
        "market_variants": market_variants,
    }


def validate_payload(payload: dict[str, Any]) -> None:
    required_top_level = {"classical_formulas", "formula_ingredients", "market_variants"}
    missing_top_level = required_top_level - set(payload.keys())
    if missing_top_level:
        raise ValueError(f"Payload missing top-level keys: {sorted(missing_top_level)}")

    for formula in payload["classical_formulas"]:
        for key in ("id", "name_hanzi", "name_pinyin", "linguistics", "source_text", "description"):
            if key not in formula:
                raise ValueError(f"ClassicalFormula missing key '{key}': {formula}")
        linguistics = formula["linguistics"]
        if not isinstance(linguistics, dict) or "cantonese" not in linguistics or "taiwanese" not in linguistics:
            raise ValueError(f"ClassicalFormula has invalid linguistics payload: {formula}")

    for edge in payload["formula_ingredients"]:
        for key in ("formula_id", "herb_id", "role", "classical_dosage_ratio"):
            if key not in edge:
                raise ValueError(f"FormulaIngredient missing key '{key}': {edge}")
        if edge["role"] not in {"Jun", "Chen", "Zuo", "Shi"}:
            raise ValueError(f"Invalid FormulaIngredient role '{edge['role']}': {edge}")

    for variant in payload["market_variants"]:
        for key in ("id", "brand_name", "formula_id", "actual_ingredients", "has_shadow_nodes"):
            if key not in variant:
                raise ValueError(f"MarketVariant missing key '{key}': {variant}")
        if not isinstance(variant["actual_ingredients"], list):
            raise ValueError(f"MarketVariant actual_ingredients must be a list: {variant}")
        for ingredient in variant["actual_ingredients"]:
            if "herb_id" not in ingredient or "exact_dosage_grams" not in ingredient:
                raise ValueError(f"MarketIngredient missing required keys: {ingredient}")


def write_payload(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    payload = build_payload()
    validate_payload(payload)
    write_payload(payload, OUTPUT_PATH)
    print(f"Wrote formula graph payload to: {OUTPUT_PATH}")
    print(f"Classical formulas: {len(payload['classical_formulas'])}")
    print(f"Formula ingredient edges: {len(payload['formula_ingredients'])}")
    print(f"Market variants: {len(payload['market_variants'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
