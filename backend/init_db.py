"""
Phase 3: Database initialization script.
Loads seed_herbs.json and seed_formulas.json into Supabase.

Usage:
    Set SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_KEY) in backend/.env
    or env vars. From project root: python -m backend.init_db
"""

import json
import os
from pathlib import Path

# Load backend/.env so SUPABASE_* are available
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), val)

from supabase import create_client, Client

from backend.schemas import Formula, FormulaArchitecture, Herb, HerbProperties, NeiDanPractice


def get_project_root() -> Path:
    """Project root (parent of backend/)."""
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> list | dict:
    """Load and parse JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_supabase_client() -> Client:
    """Create Supabase client from environment."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_KEY) environment variables."
        )
    return create_client(url, key)


def load_herbs(project_root: Path) -> list[Herb]:
    """Load and validate herbs from seed_herbs.json."""
    path = project_root / "src" / "data" / "seed_herbs.json"
    raw = load_json(path)
    return [Herb.model_validate(h) for h in raw]


def load_formulas(project_root: Path) -> list[Formula]:
    """Load and validate formulas from seed_formulas.json."""
    path = project_root / "src" / "data" / "seed_formulas.json"
    raw = load_json(path)
    return [Formula.model_validate(f) for f in raw]


def load_neidan_practices(project_root: Path) -> list[NeiDanPractice]:
    """Load and validate Nei Dan practices from seed_neidan.json."""
    path = project_root / "src" / "data" / "seed_neidan.json"
    raw = load_json(path)
    return [NeiDanPractice.model_validate(p) for p in raw]


def neidan_to_row(practice: NeiDanPractice) -> dict:
    """Convert NeiDanPractice model to Supabase row."""
    return {
        "id": practice.id,
        "name": practice.name,
        "type": practice.type,
        "target_pattern": practice.target_pattern,
        "instructions": practice.instructions,
        "safety_note": practice.safety_note,
    }


def herb_to_row(herb: Herb) -> dict:
    """Convert Herb model to Supabase row."""
    return {
        "id": herb.id,
        "pinyin_name": herb.pinyin_name,
        "common_name": herb.common_name,
        "safety_tier": herb.safety_tier,
        "properties": herb.properties.model_dump(),
        "actions": herb.actions,
        "contraindications": herb.contraindications,
    }


def formula_to_row(formula: Formula) -> dict:
    """Convert Formula model to Supabase row (excluding architecture)."""
    return {
        "id": formula.id,
        "pinyin_name": formula.pinyin_name,
        "common_name": formula.common_name,
        "primary_pattern": formula.primary_pattern,
        "actions": formula.actions,
        "safety_note": formula.safety_note,
    }


def architecture_to_row(arch: FormulaArchitecture, formula_id: str) -> dict:
    """Convert FormulaArchitecture to Supabase row."""
    return {
        "formula_id": formula_id,
        "role": arch.role,
        "herb_id": arch.herb_id,
        "pinyin_name": arch.pinyin_name,
        "dosage_percentage": float(arch.dosage_percentage),
        "purpose": arch.purpose,
    }


def run() -> None:
    """Load seed data and insert into Supabase."""
    project_root = get_project_root()
    client = get_supabase_client()

    # Load seed data
    herbs = load_herbs(project_root)
    formulas = load_formulas(project_root)

    # Upsert herbs first (formula_architecture references herbs)
    herb_rows = [herb_to_row(h) for h in herbs]
    client.table("herbs").upsert(herb_rows, on_conflict="id").execute()
    print(f"Upserted {len(herbs)} herbs.")

    # Upsert formulas
    formula_rows = [formula_to_row(f) for f in formulas]
    client.table("formulas").upsert(formula_rows, on_conflict="id").execute()
    print(f"Upserted {len(formulas)} formulas.")

    # Remove existing formula_architecture for these formulas, then insert
    formula_ids = [f.id for f in formulas]
    for fid in formula_ids:
        client.table("formula_architecture").delete().eq("formula_id", fid).execute()

    # Insert formula_architecture (formula -> herb links)
    arch_rows = []
    for formula in formulas:
        for arch in formula.architecture:
            arch_rows.append(architecture_to_row(arch, formula.id))
    if arch_rows:
        client.table("formula_architecture").insert(arch_rows).execute()
    print(f"Inserted {len(arch_rows)} formula_architecture rows.")

    # Upsert Nei Dan practices (Dual Cultivation)
    practices = load_neidan_practices(project_root)
    practice_rows = [neidan_to_row(p) for p in practices]
    client.table("nei_dan_practices").upsert(practice_rows, on_conflict="id").execute()
    print(f"Upserted {len(practices)} nei_dan_practices.")

    print("Database initialization complete.")


if __name__ == "__main__":
    run()
