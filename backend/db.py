"""
Database helpers: Supabase client and seed-data fallback.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from supabase import Client, create_client
    _SUPABASE_AVAILABLE = True
except ImportError:
    Client = Any  # type: ignore
    create_client = None  # type: ignore
    _SUPABASE_AVAILABLE = False


def get_supabase() -> "Client | None":
    """Create Supabase client if env vars are set and supabase package is available."""
    if not _SUPABASE_AVAILABLE or create_client is None:
        return None
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


def _seed_path(filename: str) -> Path:
    """Resolve path to seed data file. Tries project root, then cwd."""
    project_root = Path(__file__).resolve().parent.parent
    p = project_root / "src" / "data" / filename
    if p.exists():
        return p
    # Fallback: cwd (e.g. when run from project root)
    p = Path.cwd() / "src" / "data" / filename
    return p


def load_seed_herbs() -> list[dict]:
    """Load herbs from seed JSON (fallback when Supabase unavailable)."""
    path = _seed_path("seed_herbs.json")
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return []


def load_seed_formulas() -> list[dict]:
    """Load formulas from seed JSON (fallback when Supabase unavailable)."""
    path = _seed_path("seed_formulas.json")
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return []


def load_seed_neidan() -> list[dict]:
    """Load Nei Dan practices from seed JSON (fallback when Supabase unavailable)."""
    path = _seed_path("seed_neidan.json")
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return []


def get_herb_tier(herb_id: str, supabase: Client | None) -> int:
    """Get safety_tier for herb from Supabase or seed data. Returns 3 if not found."""
    if supabase:
        try:
            r = supabase.table("herbs").select("safety_tier").eq("id", herb_id).single().execute()
            if r.data:
                return int(r.data.get("safety_tier", 3))
        except Exception:
            pass
    for h in load_seed_herbs():
        if h.get("id") == herb_id:
            return int(h.get("safety_tier", 3))
    return 3  # Unknown = restricted


def _arch_row_to_dict(row: dict) -> dict:
    """Convert formula_architecture row to architecture entry dict."""
    return {
        "role": row.get("role", ""),
        "herb_id": row.get("herb_id", ""),
        "pinyin_name": row.get("pinyin_name", ""),
        "dosage_percentage": float(row.get("dosage_percentage", 0)),
        "purpose": row.get("purpose", ""),
    }


def get_formula_by_id(formula_id: str, supabase: Client | None) -> dict | None:
    """Get formula by ID from Supabase or seed data, with architecture."""
    if supabase:
        try:
            r = supabase.table("formulas").select("*").eq("id", formula_id).single().execute()
            if r.data:
                formula = dict(r.data)
                arch_r = supabase.table("formula_architecture").select("*").eq("formula_id", formula_id).order("id").execute()
                formula["architecture"] = [_arch_row_to_dict(row) for row in (arch_r.data or [])]
                return formula
        except Exception:
            pass
    for f in load_seed_formulas():
        if f.get("id") == formula_id:
            return f
    return None


def get_all_formulas(supabase: Client | None) -> list[dict]:
    """Get all formulas from Supabase or seed data, with architecture."""
    if supabase:
        try:
            r = supabase.table("formulas").select("*").execute()
            if r.data:
                formulas = []
                for row in r.data:
                    fid = row["id"]
                    arch_r = supabase.table("formula_architecture").select("*").eq("formula_id", fid).order("id").execute()
                    formula = dict(row)
                    formula["architecture"] = [_arch_row_to_dict(a) for a in (arch_r.data or [])]
                    formulas.append(formula)
                return formulas
        except Exception:
            pass
    return load_seed_formulas()


def get_all_neidan_practices(supabase: Client | None) -> list[dict]:
    """Get all Nei Dan practices from Supabase or seed data."""
    if supabase:
        try:
            r = supabase.table("nei_dan_practices").select("*").execute()
            if r.data:
                return [dict(row) for row in r.data]
        except Exception:
            pass
    return load_seed_neidan()


def get_all_herbs(supabase: Client | None) -> list[dict]:
    """Get all herbs from Supabase or seed data."""
    if supabase:
        try:
            r = supabase.table("herbs").select("*").execute()
            if r.data:
                return [dict(row) for row in r.data]
        except Exception:
            pass
    return load_seed_herbs()


# In-memory pantry fallback when Supabase is unavailable (e.g. local dev)
_pantry_fallback: dict[str, dict[str, bool]] = {}  # user_id -> { herb_id -> in_stock }


def get_pantry(user_id: str, supabase: Client | None) -> list[dict]:
    """Get user's pantry inventory (herb_id, in_stock) from Supabase or fallback."""
    if supabase:
        try:
            r = supabase.table("user_pantry").select("herb_id, in_stock").eq("user_id", user_id).execute()
            if r.data:
                return [{"herb_id": row["herb_id"], "in_stock": bool(row.get("in_stock", True))} for row in r.data]
        except Exception:
            pass
    # Fallback: in-memory store
    if user_id not in _pantry_fallback:
        return []
    return [{"herb_id": hid, "in_stock": st} for hid, st in _pantry_fallback[user_id].items()]


def toggle_pantry(user_id: str, herb_id: str, supabase: Client | None) -> bool:
    """
    Toggle herb in user's pantry. If exists and in_stock, set in_stock=false.
    If exists and not in_stock, set in_stock=true. If not exists, insert with in_stock=true.
    Returns the new in_stock value.
    """
    if supabase:
        try:
            r = supabase.table("user_pantry").select("id, in_stock").eq("user_id", user_id).eq("herb_id", herb_id).execute()
            if r.data and len(r.data) > 0:
                row = r.data[0]
                new_stock = not bool(row.get("in_stock", True))
                supabase.table("user_pantry").update({"in_stock": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", row["id"]).execute()
                return new_stock
            else:
                supabase.table("user_pantry").insert({"user_id": user_id, "herb_id": herb_id, "in_stock": True}).execute()
                return True
        except Exception:
            pass
    # Fallback: in-memory store
    if user_id not in _pantry_fallback:
        _pantry_fallback[user_id] = {}
    if herb_id not in _pantry_fallback[user_id]:
        _pantry_fallback[user_id][herb_id] = True
        return True
    _pantry_fallback[user_id][herb_id] = not _pantry_fallback[user_id][herb_id]
    return _pantry_fallback[user_id][herb_id]
