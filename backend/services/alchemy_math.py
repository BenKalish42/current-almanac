"""
Phase 4: He Fang (Formula Merger) Engine.
Phase 9: Dual Cultivation - Prescription (Wei Dan + Nei Dan pairing).

Merges two classical formulas, handling overlapping herbs, primary-formula
dosage bumps, and Spleen-protective volume scaling.
Pairs herbal formulas with matching Nei Dan (internal alchemy) practices.
"""

import random
from typing import Any

from ..schemas import NeiDanPractice, Prescription

# -----------------------------------------------------------------------------
# Constants for He Fang merge algorithm
# -----------------------------------------------------------------------------
PRIMARY_DOSAGE_MULTIPLIER = 1.1  # 10% bump for herbs from primary formula
VOLUME_SCALE_FACTOR = 0.75  # 25% reduction to protect Spleen/digestion


def _architecture_to_list(architecture: Any) -> list[dict[str, Any]]:
    """
    Normalize architecture input to a list of dicts.
    Handles both Formula model instances and raw dicts.
    """
    if architecture is None:
        return []
    if isinstance(architecture, list):
        return [item if isinstance(item, dict) else dict(item) for item in architecture]
    return []


def _get_formula_id(formula: Any) -> str:
    """Extract formula id from Formula model or dict."""
    if hasattr(formula, "id"):
        return str(formula.id)
    return str(formula.get("id", ""))


def merge_formulas(
    formula_a: Any,
    formula_b: Any,
    primary_formula_id: str,
) -> list[dict[str, Any]]:
    """
    Merge two formulas into a single architecture array (He Fang algorithm).

    Steps:
    1. Unpack architecture from both formulas.
    2. Identify overlapping herbs (by herb_id) and sum their dosage_percentage.
    3. Apply 1.1x multiplier to dosages of herbs from the primary formula.
    4. Recalculate total relative percentages (normalize).
    5. Scale final combined volume down by 25% (multiply by 0.75).

    Args:
        formula_a: First formula (Formula model or dict with 'id' and 'architecture').
        formula_b: Second formula (same structure).
        primary_formula_id: ID of the formula whose herbs receive the 10% dosage bump.

    Returns:
        Merged architecture array: list of dicts with role, herb_id, pinyin_name,
        dosage_percentage, purpose.
    """
    # -------------------------------------------------------------------------
    # Step 1: Unpack architecture from both formulas
    # -------------------------------------------------------------------------
    arch_a = _architecture_to_list(
        formula_a.architecture if hasattr(formula_a, "architecture") else formula_a.get("architecture", [])
    )
    arch_b = _architecture_to_list(
        formula_b.architecture if hasattr(formula_b, "architecture") else formula_b.get("architecture", [])
    )

    id_a = _get_formula_id(formula_a)
    id_b = _get_formula_id(formula_b)

    # -------------------------------------------------------------------------
    # Step 2: Build merged map by herb_id; sum overlapping dosages
    # Map: herb_id -> { dosage_sum, role, pinyin_name, purpose, from_primary }
    # -------------------------------------------------------------------------
    merged: dict[str, dict[str, Any]] = {}

    for entry in arch_a:
        herb_id = entry.get("herb_id")
        if not herb_id:
            continue
        dosage = float(entry.get("dosage_percentage", 0))
        from_primary = id_a == primary_formula_id

        if herb_id in merged:
            merged[herb_id]["dosage_sum"] += dosage
            # If either source is primary, mark as from_primary for the bump
            merged[herb_id]["from_primary"] = merged[herb_id]["from_primary"] or from_primary
        else:
            merged[herb_id] = {
                "dosage_sum": dosage,
                "role": entry.get("role", ""),
                "pinyin_name": entry.get("pinyin_name", ""),
                "purpose": entry.get("purpose", ""),
                "from_primary": from_primary,
            }

    for entry in arch_b:
        herb_id = entry.get("herb_id")
        if not herb_id:
            continue
        dosage = float(entry.get("dosage_percentage", 0))
        from_primary = id_b == primary_formula_id

        if herb_id in merged:
            merged[herb_id]["dosage_sum"] += dosage
            merged[herb_id]["from_primary"] = merged[herb_id]["from_primary"] or from_primary
        else:
            merged[herb_id] = {
                "dosage_sum": dosage,
                "role": entry.get("role", ""),
                "pinyin_name": entry.get("pinyin_name", ""),
                "purpose": entry.get("purpose", ""),
                "from_primary": from_primary,
            }

    # -------------------------------------------------------------------------
    # Step 3: Apply 1.1x multiplier to dosages of herbs from primary formula
    # -------------------------------------------------------------------------
    for herb_id, data in merged.items():
        if data["from_primary"]:
            data["dosage_sum"] *= PRIMARY_DOSAGE_MULTIPLIER

    # -------------------------------------------------------------------------
    # Step 4: Recalculate total relative percentages (normalize to sum = 100)
    # -------------------------------------------------------------------------
    total_dosage = sum(d["dosage_sum"] for d in merged.values())
    if total_dosage <= 0:
        return []

    for data in merged.values():
        data["dosage_percentage"] = (data["dosage_sum"] / total_dosage) * 100

    # -------------------------------------------------------------------------
    # Step 5: Scale final combined volume down by 25% (multiply by 0.75)
    # -------------------------------------------------------------------------
    result: list[dict[str, Any]] = []
    for herb_id, data in merged.items():
        scaled_pct = data["dosage_percentage"] * VOLUME_SCALE_FACTOR
        result.append({
            "role": data["role"],
            "herb_id": herb_id,
            "pinyin_name": data["pinyin_name"],
            "dosage_percentage": round(scaled_pct, 2),
            "purpose": data["purpose"],
        })

    return result


# -----------------------------------------------------------------------------
# Dual Cultivation: Nei Dan pairing
# -----------------------------------------------------------------------------


def match_neidan_for_pattern(
    primary_pattern: str,
    practices: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Find a Nei Dan practice whose target_pattern matches the formula's primary_pattern.

    Matching logic:
    1. Exact match: primary_pattern in practice.target_pattern
    2. Substring match: any target in practice.target_pattern is a substring of primary_pattern
       (e.g. "Liver Qi Stagnation" matches "Liver Qi Stagnation with Blood Deficiency")

    If multiple practices match, returns one randomly.
    """
    if not primary_pattern or not practices:
        return None

    primary = primary_pattern.strip()
    matches: list[dict[str, Any]] = []

    for p in practices:
        targets = p.get("target_pattern") or []
        if not isinstance(targets, list):
            continue
        for t in targets:
            t_str = str(t).strip()
            if primary == t_str:
                matches.append(p)
                break
            if t_str and t_str in primary:
                matches.append(p)
                break

    if not matches:
        return None
    return random.choice(matches)


def build_prescription(
    formula: dict[str, Any],
    architecture: list[dict[str, Any]],
    nei_dan_practice: dict[str, Any] | None,
) -> Prescription:
    """Build a Prescription object with wei_dan (herbal) and nei_dan (internal practice)."""
    nei_dan = None
    if nei_dan_practice:
        nei_dan = NeiDanPractice(
            id=nei_dan_practice.get("id", ""),
            name=nei_dan_practice.get("name", ""),
            type=nei_dan_practice.get("type", ""),
            target_pattern=nei_dan_practice.get("target_pattern") or [],
            instructions=nei_dan_practice.get("instructions") or [],
            safety_note=nei_dan_practice.get("safety_note", ""),
        )

    return Prescription(
        wei_dan=architecture,
        nei_dan=nei_dan,
        formula_id=formula.get("id", ""),
        pinyin_name=formula.get("pinyin_name", ""),
        common_name=formula.get("common_name", ""),
        primary_pattern=formula.get("primary_pattern", ""),
        actions=formula.get("actions", []),
        safety_note=formula.get("safety_note", ""),
    )
