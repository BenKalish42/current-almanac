"""
Current Backend - FastAPI application.
Phase 2: Health check and basic calculation endpoints.
Phase 5: Cauldron API (formula, override check, merge).
Phase 7: AI Chat + Interpret via DeepSeek.
"""

import json
import traceback
import os
from pathlib import Path

# Load .env from backend/ so DEEPSEEK_API_KEY, SUPABASE_*, etc. take effect
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), val)

import random
import uuid
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .core.safety import TIER_3_BLOCKED, TIER_3_ERROR_MESSAGE
from .db import get_all_formulas, get_all_neidan_practices, get_formula_by_id, get_herb_tier, get_pantry, get_supabase, toggle_pantry
from .schemas import (
    FormulaRequest,
    HealthResponse,
    InterpretationRequest,
    InterpretationResponse,
    MergeFormulasRequest,
    MergeFormulasResponse,
    OverrideCheckRequest,
    OverrideCheckResponse,
    PantryItem,
    PantryToggleRequest,
    Prescription,
)
from .services.alchemy_math import build_prescription, match_neidan_for_pattern, merge_formulas as he_fang_merge
from .services.ensembles import run_ensemble
from .services.llm_service import (
    MODEL_CATALOG,
    chat_stream,
    family_key_configured,
    has_deepseek_key,
    interpret_with_llm,
)
from .services.rag_service import format_context, rag

try:
    from openai import APIError, APIStatusError, APIConnectionError
except ImportError:
    APIError = type("APIError", (Exception,), {})
    APIStatusError = type("APIStatusError", (Exception,), {})
    APIConnectionError = type("APIConnectionError", (Exception,), {})

app = FastAPI(
    title="Current API",
    description="Daoist Astrology & Herbal Alchemy backend",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return 500 with error detail for unhandled exceptions."""
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


# -----------------------------------------------------------------------------
# Intelligence workbench: model catalog + ensemble strategy metadata
# -----------------------------------------------------------------------------

ENSEMBLE_STRATEGIES = [
    {
        "id": "single",
        "label": "Single",
        "description": "Use only the selected model.",
    },
    {
        "id": "fallback",
        "label": "Fallback",
        "description": "Try the selected model, then configured providers in priority order.",
    },
    {
        "id": "parallel_judge",
        "label": "Parallel Judge",
        "description": "Each configured family drafts; the selected model synthesizes a final answer.",
        "needsMultipleProviders": True,
    },
    {
        "id": "specialist_committee",
        "label": "Specialist Committee",
        "description": "DeepSeek=Astrology · ChatGPT=Herbal Alchemy · Claude=Plain Language · Gemini=Synthesis.",
        "needsMultipleProviders": True,
    },
    {
        "id": "self_consistency",
        "label": "Self-Consistency",
        "description": "Three drafts from the selected model, then a consolidator pass.",
    },
    {
        "id": "critic_reviser",
        "label": "Critic / Reviser",
        "description": "Draft, then critique, then revise — all on the selected model.",
    },
    {
        "id": "confidence_escalation",
        "label": "Confidence Escalation",
        "description": "Cheap model first; escalate to the strongest model if uncertainty is detected.",
    },
    {
        "id": "structured_verifier",
        "label": "Structured Verifier",
        "description": "Primary draft + verifier audit pass for safety, disclaimers, and herb grounding.",
    },
]


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check for load balancers and monitoring."""
    return HealthResponse(status="ok", version="current_v1")


@app.get("/api/models")
def list_models() -> dict[str, Any]:
    """
    Return Intelligence workbench metadata: model families/subtypes, ensemble
    strategies, and KnowledgeRAG availability. Frontend uses this to render
    provider cards and badges. No API keys are returned.
    """
    families = []
    for fid, fam in MODEL_CATALOG.items():
        families.append(
            {
                "id": fid,
                "label": fam.get("label", fid),
                "provider": fam.get("provider", ""),
                "envKeys": list(fam.get("env", []) or []),
                "keyConfigured": family_key_configured(fid),
                "subtypes": [
                    {
                        "id": st["id"],
                        "label": st["label"],
                        "model": st["model"],
                        "description": st.get("description", ""),
                    }
                    for st in fam.get("subtypes", [])
                ],
            }
        )

    rag_available = rag.is_available()
    return {
        "families": families,
        "strategies": ENSEMBLE_STRATEGIES,
        "rag": {
            "available": rag_available,
            "backend": "neo4j" if rag_available else "seed",
        },
    }


@app.post("/api/interpret", response_model=InterpretationResponse)
async def interpret(request: InterpretationRequest) -> InterpretationResponse:
    """
    Accept the frontend payload, call DeepSeek, and return a Daoist interpretation.
    When DEEPSEEK_API_KEY is not set, returns a friendly 200 response instead of 503.
    """
    if not has_deepseek_key():
        return InterpretationResponse(
            current_summary=(
                "To enable AI interpretation, set DEEPSEEK_API_KEY in your backend environment. "
                "Get a key at https://platform.deepseek.com/api_keys — then restart the backend "
                "and try Past or Present again."
            ),
            shi=None,
            shun=None,
            ji=None,
            load_capacity=None,
            misalignment_signals=None,
            recommended_modes=None,
            avoid=None,
            self_check=None,
        )
    try:
        payload = request.model_dump(mode="json")
        result = interpret_with_llm(payload)
        return InterpretationResponse(
            current_summary=result.get("current_summary"),
            shi=result.get("shi"),
            shun=result.get("shun"),
            ji=result.get("ji"),
            load_capacity=result.get("load_capacity"),
            misalignment_signals=result.get("misalignment_signals"),
            recommended_modes=result.get("recommended_modes"),
            avoid=result.get("avoid"),
            self_check=result.get("self_check"),
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except APIStatusError as e:
        status = getattr(e, "status_code", 503)
        msg = str(e) or "DeepSeek API error"
        if status == 401:
            msg = "Invalid DeepSeek API key. Check DEEPSEEK_API_KEY at platform.deepseek.com/api_keys"
        elif status == 429:
            msg = "DeepSeek rate limit exceeded. Try again shortly."
        elif status == 404:
            msg = "DeepSeek API endpoint not found. Try DEEPSEEK_BASE_URL=https://api.deepseek.com/v1"
        raise HTTPException(status_code=min(status, 503), detail=msg) from e
    except APIConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach DeepSeek API. Check network or DEEPSEEK_BASE_URL.",
        ) from e
    except APIError as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=f"DeepSeek API error: {e}. Check API key and try again.",
        ) from e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Interpretation error: {e}") from e


@app.post("/api/formula", response_model=Prescription)
def fetch_formula(request: FormulaRequest) -> Prescription:
    """
    Return a Prescription (Dual Cultivation) based on astro + user state.
    Wei Dan: herbal formula architecture.
    Nei Dan: matched internal practice by primary_pattern.
    Uses seed data only (no DeepSeek). Picks a formula at random for variety.
    """
    try:
        supabase = get_supabase()
        formulas = get_all_formulas(supabase)
        if not formulas:
            raise HTTPException(
                status_code=404,
                detail="No formulas available. Ensure src/data/seed_formulas.json exists.",
            )
        formula = random.choice(formulas)
        architecture = formula.get("architecture", [])

        practices = get_all_neidan_practices(supabase)
        nei_dan = match_neidan_for_pattern(formula.get("primary_pattern", ""), practices)

        return build_prescription(formula, architecture, nei_dan)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Formula error: {e}") from e


@app.post("/api/check-override", response_model=OverrideCheckResponse)
def check_override(request: OverrideCheckRequest) -> OverrideCheckResponse:
    """
    Check if adding an herb to the current formula is safe.
    Blocks Tier 3 herbs; returns synergy note for Tier 1/2.
    """
    supabase = get_supabase()
    tier = get_herb_tier(request.herb_id, supabase)
    if tier == TIER_3_BLOCKED:
        return OverrideCheckResponse(
            allowed=False,
            message=TIER_3_ERROR_MESSAGE,
        )
    return OverrideCheckResponse(
        allowed=True,
        message="Herb is compatible. Current is an AI alchemical tool. Consult a licensed practitioner before beginning any herbal regimen.",
    )


@app.post("/api/chat")
async def chat_stream_endpoint(request: Request) -> StreamingResponse:
    """
    Stream chat completions for the Intelligence workbench.

    Body shape (all ``intelligence`` fields optional, defaults applied):
        {
          "messages": [...],
          "intelligence": {
            "family": "claude"|"chatgpt"|"gemini"|"deepseek",
            "model":  subtype id,
            "strategy": one of ENSEMBLE_STRATEGIES.id,
            "selectedModelsByFamily": {family_id: subtype_id},
            "ragEnabled": bool
          }
        }

    Streams the AI-SDK SSE envelope (``start``, ``text-start``, ``text-delta``,
    ``text-end``, ``finish``) so the existing ``useChat`` composable continues
    to render incremental output unchanged.
    """
    message_id = str(uuid.uuid4())
    text_id = "text-1"

    try:
        body = await request.json()
        messages_raw = body.get("messages", []) or []
        intelligence = body.get("intelligence") or {}
    except Exception:
        messages_raw = []
        intelligence = {}

    messages: list[dict[str, Any]] = [
        {"role": m.get("role", "user"), "content": _message_text(m)}
        for m in messages_raw
    ]

    # Normalize intelligence options with defaults.
    family = intelligence.get("family") or "deepseek"
    subtype = intelligence.get("model") or "chat"
    strategy = intelligence.get("strategy") or "single"
    selected_by_family = intelligence.get("selectedModelsByFamily") or {}
    rag_enabled = bool(intelligence.get("ragEnabled"))

    opts = {
        "family": family,
        "model": subtype,
        "strategy": strategy,
        "selectedModelsByFamily": selected_by_family,
        "ragEnabled": rag_enabled,
    }

    # Build optional KnowledgeRAG context block from the most recent user turn.
    rag_context: str | None = None
    if rag_enabled and messages:
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        if last_user:
            try:
                snippets = rag.retrieve(last_user, k=5)
                rag_context = format_context(snippets)
            except Exception:
                rag_context = None

    async def generate() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'type': 'start', 'messageId': message_id})}\n\n"
        yield f"data: {json.dumps({'type': 'text-start', 'id': text_id})}\n\n"

        if not messages:
            fallback = "Send a message to chat with the Intelligence workbench."
            for ch in fallback:
                yield f"data: {json.dumps({'type': 'text-delta', 'id': text_id, 'delta': ch})}\n\n"
        else:
            try:
                for delta in run_ensemble(strategy, messages, opts, rag_context):
                    if not delta:
                        continue
                    yield (
                        "data: "
                        f"{json.dumps({'type': 'text-delta', 'id': text_id, 'delta': delta})}"
                        "\n\n"
                    )
            except Exception as e:  # noqa: BLE001 — funnel into stream
                err = (
                    "Intelligence backend error: "
                    f"{type(e).__name__}: {str(e)[:200]}. "
                    "Check backend logs."
                )
                yield f"data: {json.dumps({'type': 'text-delta', 'id': text_id, 'delta': err})}\n\n"

        yield f"data: {json.dumps({'type': 'text-end', 'id': text_id})}\n\n"
        yield f"data: {json.dumps({'type': 'finish', 'finishReason': 'stop'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "x-vercel-ai-data-stream": "v1",
        },
    )


def _message_text(m: dict[str, Any]) -> str:
    """Extract text from AI SDK message format (parts with type text)."""
    parts = m.get("parts", [])
    for p in parts:
        if isinstance(p, dict) and p.get("type") == "text":
            return p.get("text", "") or ""
    return str(m.get("content", ""))


@app.get("/api/pantry")
def fetch_pantry(user_id: str = "default") -> list[PantryItem]:
    """
    Phase 8: Fetch user's pantry inventory.
    Pass user_id as query param (default: 'default' for anonymous/session).
    """
    supabase = get_supabase()
    items = get_pantry(user_id, supabase)
    return [PantryItem(herb_id=row["herb_id"], in_stock=row["in_stock"]) for row in items]


@app.post("/api/pantry/toggle")
def pantry_toggle(request: PantryToggleRequest) -> dict:
    """
    Phase 8: Toggle herb in/out of pantry.
    Adds herb if not present, flips in_stock if present.
    """
    supabase = get_supabase()
    new_stock = toggle_pantry(request.user_id, request.herb_id, supabase)
    return {"herb_id": request.herb_id, "in_stock": new_stock}


@app.post("/api/merge-formulas", response_model=MergeFormulasResponse)
def merge_formulas_endpoint(request: MergeFormulasRequest) -> MergeFormulasResponse:
    """
    Merge two formulas using the He Fang algorithm.
    """
    supabase = get_supabase()
    formula_a = get_formula_by_id(request.formula_a_id, supabase)
    formula_b = get_formula_by_id(request.formula_b_id, supabase)
    if not formula_a:
        raise HTTPException(status_code=404, detail=f"Formula not found: {request.formula_a_id}")
    if not formula_b:
        raise HTTPException(status_code=404, detail=f"Formula not found: {request.formula_b_id}")

    architecture = he_fang_merge(
        formula_a,
        formula_b,
        request.primary_formula_id,
    )
    return MergeFormulasResponse(architecture=architecture)
