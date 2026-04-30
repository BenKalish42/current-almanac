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

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .core.safety import TIER_3_BLOCKED, TIER_3_ERROR_MESSAGE
from .db import (
    get_all_formulas,
    get_all_neidan_practices,
    get_formula_by_id,
    get_herb_tier,
    get_pantry,
    get_profile,
    get_subscription_state,
    get_supabase,
    get_supabase_anon_client,
    insert_subscription_event,
    toggle_pantry,
    upsert_profile,
    upsert_subscription_customer,
    upsert_subscription_state,
)
from .schemas import (
    AuthEmailOtpRequest,
    AuthSessionResponse,
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
    RevenueCatWebhookEventEnvelope,
    SubscriptionStateResponse,
    UserProfileResponse,
)
from .services.alchemy_math import build_prescription, match_neidan_for_pattern, merge_formulas as he_fang_merge
from .services.llm_service import chat_stream, has_deepseek_key, interpret_with_llm
from .services.subscription_sync import (
    fetch_revenuecat_subscriber,
    normalize_revenuecat_subscriber,
)

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


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check for load balancers and monitoring."""
    return HealthResponse(status="ok", version="current_v1")


def _resolve_authenticated_user(authorization: str | None) -> dict[str, Any]:
    """Validate a Supabase bearer token and return the user payload."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token.")

    supabase = get_supabase_anon_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase auth is not configured.")

    try:
        response = supabase.auth.get_user(token)
        user = getattr(response, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid Supabase session.")
        return user.model_dump() if hasattr(user, "model_dump") else dict(user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Supabase session: {exc}") from exc


def _sync_profile_and_subscription_state(user: dict[str, Any]) -> tuple[dict | None, dict | None]:
    """Upsert profile and refresh normalized subscription state."""
    supabase = get_supabase()
    user_id = str(user.get("id") or "")
    if not user_id:
        return None, None

    email = user.get("email")
    profile = upsert_profile(user_id, email, supabase)
    if profile is None:
        profile = get_profile(user_id, supabase)

    subscription_state = get_subscription_state(user_id, supabase)
    if not subscription_state:
        subscriber = fetch_revenuecat_subscriber(user_id)
        if subscriber:
            normalized = normalize_revenuecat_subscriber(user_id, subscriber)
            upsert_subscription_customer(
                user_id,
                user_id,
                normalized.get("original_app_user_id"),
                supabase,
            )
            subscription_state = upsert_subscription_state(normalized, supabase)
    return profile, subscription_state


def _extract_authorization_header(
    authorization: str | None,
    revenuecat_authorization: str | None,
) -> str | None:
    """Prefer the standard Authorization header, fallback to RevenueCat-specific alias."""
    return authorization or revenuecat_authorization


@app.post("/api/auth/email-otp")
def request_email_otp(payload: AuthEmailOtpRequest) -> dict[str, bool]:
    """Trigger a Supabase email OTP / magic link sign-in flow."""
    supabase = get_supabase_anon_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase auth is not configured.")

    options: dict[str, Any] = {}
    redirect_to = os.environ.get("SUPABASE_AUTH_REDIRECT_URL")
    if redirect_to:
        options["email_redirect_to"] = redirect_to

    try:
        supabase.auth.sign_in_with_otp(
            {
                "email": payload.email,
                "options": {
                    **options,
                    "should_create_user": True,
                },
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not request sign-in link: {exc}") from exc

    return {"ok": True}


@app.get("/api/auth/session", response_model=AuthSessionResponse)
def get_auth_session(
    authorization: str | None = Header(default=None),
    revenuecat_authorization: str | None = Header(default=None, alias="X-RevenueCat-Authorization"),
) -> AuthSessionResponse:
    """Return the authenticated Supabase user plus normalized subscription snapshot."""
    user = _resolve_authenticated_user(
        _extract_authorization_header(authorization, revenuecat_authorization)
    )
    profile, subscription_state = _sync_profile_and_subscription_state(user)

    return AuthSessionResponse(
        user=user,
        profile=UserProfileResponse.model_validate(profile) if profile else None,
        subscription=SubscriptionStateResponse.model_validate(subscription_state)
        if subscription_state
        else None,
    )


@app.get("/api/me", response_model=AuthSessionResponse)
def get_me(
    authorization: str | None = Header(default=None),
    revenuecat_authorization: str | None = Header(default=None, alias="X-RevenueCat-Authorization"),
) -> AuthSessionResponse:
    """Alias for /api/auth/session."""
    return get_auth_session(authorization, revenuecat_authorization)


@app.get("/api/subscription/state", response_model=SubscriptionStateResponse)
def get_subscription_snapshot(
    authorization: str | None = Header(default=None),
    revenuecat_authorization: str | None = Header(default=None, alias="X-RevenueCat-Authorization"),
) -> SubscriptionStateResponse:
    """Fetch the current normalized subscription state for the authenticated user."""
    user = _resolve_authenticated_user(
        _extract_authorization_header(authorization, revenuecat_authorization)
    )
    _, subscription_state = _sync_profile_and_subscription_state(user)
    if not subscription_state:
        return SubscriptionStateResponse(user_id=str(user.get("id")), is_paid=False)
    return SubscriptionStateResponse.model_validate(subscription_state)


@app.post("/api/revenuecat/webhook")
async def revenuecat_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict[str, bool]:
    """Ingest RevenueCat webhook events and refresh the customer's normalized state."""
    expected_auth = os.environ.get("REVENUECAT_WEBHOOK_AUTHORIZATION")
    if expected_auth and authorization != expected_auth:
        raise HTTPException(status_code=401, detail="Invalid RevenueCat webhook authorization.")

    payload = RevenueCatWebhookEventEnvelope.model_validate(await request.json())
    event = payload.event
    supabase = get_supabase()

    inserted = insert_subscription_event(
        {
            "event_id": event.id,
            "user_id": event.app_user_id,
            "event_type": event.type,
            "store": event.store,
            "payload": payload.model_dump(mode="json"),
        },
        supabase,
    )
    if inserted is None and supabase:
        return {"ok": True}

    user_id = event.app_user_id or event.original_app_user_id
    if user_id:
        subscriber = fetch_revenuecat_subscriber(user_id)
        if subscriber:
            normalized = normalize_revenuecat_subscriber(user_id, subscriber)
            upsert_subscription_customer(
                user_id,
                user_id,
                normalized.get("original_app_user_id"),
                supabase,
            )
            upsert_subscription_state(normalized, supabase)

    return {"ok": True}


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
    Stream chat completions from DeepSeek (Zhuang).
    AI SDK UI Message Stream format. Requires DEEPSEEK_API_KEY.
    """
    message_id = str(uuid.uuid4())
    text_id = "text-1"

    try:
        body = await request.json()
        messages_raw = body.get("messages", [])
        messages = [
            {"role": m.get("role", "user"), "content": _message_text(m)}
            for m in messages_raw
        ]
    except Exception:
        messages = []

    async def generate() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'type': 'start', 'messageId': message_id})}\n\n"
        yield f"data: {json.dumps({'type': 'text-start', 'id': text_id})}\n\n"

        if not messages:
            fallback = "Send a message to chat with Zhuang about Daoist astrology or herbal alchemy."
            for ch in fallback:
                yield f"data: {json.dumps({'type': 'text-delta', 'id': text_id, 'delta': ch})}\n\n"
        else:
            try:
                for chunk in chat_stream(messages):
                    delta = chunk.get("delta", "")
                    if delta:
                        yield f"data: {json.dumps({'type': 'text-delta', 'id': text_id, 'delta': delta})}\n\n"
            except (ValueError, APIStatusError, APIConnectionError) as e:
                err = str(e)
                if isinstance(e, APIStatusError):
                    sc = getattr(e, "status_code", None)
                    if sc == 401:
                        err = "Invalid DeepSeek API key. Check DEEPSEEK_API_KEY."
                    elif sc == 429:
                        err = "DeepSeek rate limit exceeded. Try again shortly."
                    elif sc == 404:
                        err = "DeepSeek API endpoint not found. Try DEEPSEEK_BASE_URL=https://api.deepseek.com/v1"
                elif isinstance(e, APIConnectionError):
                    err = "Cannot reach DeepSeek API. Check network."
                for ch in err:
                    yield f"data: {json.dumps({'type': 'text-delta', 'id': text_id, 'delta': ch})}\n\n"
            except Exception as e:
                for ch in "AI service error. Try again or check backend logs.":
                    yield f"data: {json.dumps({'type': 'text-delta', 'id': text_id, 'delta': ch})}\n\n"

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
