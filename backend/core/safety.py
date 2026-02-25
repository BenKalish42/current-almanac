"""
Phase 4: Safety Middleware (Pydantic Interceptor).

Validates AI-generated formulas before returning to the frontend.
Blocks any formula containing Tier 3 (restricted) herbs.
"""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client

try:
    from supabase import Client
except ImportError:
    Client = Any  # type: ignore

# -----------------------------------------------------------------------------
# Safety tier constants
# Tier 1: Food grade (safest)
# Tier 2: Apothecary (requires practitioner guidance)
# Tier 3: Restricted / toxic - BLOCKED for digital use
# -----------------------------------------------------------------------------
TIER_3_BLOCKED = 3

# Error message returned when a Tier 3 herb is detected
TIER_3_ERROR_MESSAGE = (
    "Formula contains restricted Tier 3 alchemical materials and cannot be "
    "generated for digital use."
)


class SafetyValidationError(Exception):
    """Raised when a formula fails safety validation (e.g., contains Tier 3 herbs)."""

    def __init__(self, message: str = TIER_3_ERROR_MESSAGE) -> None:
        self.message = message
        super().__init__(message)


def get_herb_ids_from_architecture(architecture: list[dict[str, Any]]) -> list[str]:
    """
    Extract unique herb_ids from a formula architecture array.

    Args:
        architecture: List of dicts with 'herb_id' keys (Jun-Chen-Zuo-Shi roles).

    Returns:
        Unique list of herb_id strings.
    """
    herb_ids = []
    seen: set[str] = set()
    for entry in architecture:
        herb_id = entry.get("herb_id")
        if herb_id and herb_id not in seen:
            seen.add(herb_id)
            herb_ids.append(herb_id)
    return herb_ids


def fetch_herb_safety_tiers(supabase: Client, herb_ids: list[str]) -> dict[str, int]:
    """
    Look up safety_tier for each herb in the database.

    Args:
        supabase: Supabase client instance.
        herb_ids: List of herb IDs to look up.

    Returns:
        Dict mapping herb_id -> safety_tier (1, 2, or 3).
        Missing herbs default to tier 3 (block) for safety.
    """
    if not herb_ids:
        return {}

    result = supabase.table("herbs").select("id, safety_tier").in_("id", herb_ids).execute()

    tiers: dict[str, int] = {}
    for row in result.data or []:
        tiers[row["id"]] = int(row.get("safety_tier", TIER_3_BLOCKED))

    # Any herb not found in DB is treated as restricted
    for hid in herb_ids:
        if hid not in tiers:
            tiers[hid] = TIER_3_BLOCKED

    return tiers


def validate_formula_architecture(
    architecture: list[dict[str, Any]],
    supabase: Client,
) -> None:
    """
    Validate that no herb in the architecture has safety_tier == 3.

    Args:
        architecture: Formula architecture (list of role/herb/dosage dicts).
        supabase: Supabase client for herb lookups.

    Raises:
        SafetyValidationError: If any herb is Tier 3 (restricted).
    """
    herb_ids = get_herb_ids_from_architecture(architecture)
    tiers = fetch_herb_safety_tiers(supabase, herb_ids)

    for herb_id, tier in tiers.items():
        if tier == TIER_3_BLOCKED:
            raise SafetyValidationError(TIER_3_ERROR_MESSAGE)
