"""
Intelligence model service — provider catalog, LiteLLM router, and DeepSeek shim.

This module replaces the old single-provider DeepSeek-only path with a
LiteLLM-backed router that supports:
  - Claude (Sonnet, Opus, Haiku)
  - ChatGPT (GPT-4o, GPT-4o mini, reasoning o-series)
  - Gemini (Pro, Flash)
  - DeepSeek (Chat, Reasoner)

API keys are read from the environment (server-side only). The legacy
``chat_stream`` and ``interpret_with_llm`` helpers continue to work against
DeepSeek for backwards compatibility with the existing /api/interpret route.
"""

from __future__ import annotations

import json
import os
from typing import Any, Iterable, Iterator

# OpenAI client retained for the DeepSeek shim used by /api/interpret.
from openai import OpenAI

# LiteLLM is imported lazily; tests can monkeypatch ``litellm`` if needed.
import litellm

# -----------------------------------------------------------------------------
# Zhuang persona — used as the default system prompt across all families.
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = """You are Zhuang (莊), a master Daoist herbal alchemist and astrologer. You bridge ancient clinical TCM safety with modern astronomical math. Your tone is grounded, poetic, and highly educational.
CRITICAL RULES:
1. You are an educational tool, not a doctor. Never diagnose, treat, or cure medical conditions.
2. Use the 'Internal Weather' (Eight Parameters) to describe imbalances.
3. Only recommend herbs and formulas provided in your context.
4. Always append this disclaimer to any herbal suggestion: 'Current is an AI alchemical tool. Consult a licensed practitioner before beginning any herbal regimen.'"""

INTERPRET_INSTRUCTIONS = """Analyze the user's Daoist astrological data and return a JSON object with these exact keys (use null for any you omit):
- current_summary: string — A 2–4 sentence synthesis of how birth BaZi meets the present moment.
- shi: string | null — What to lean into (時).
- shun: string | null — What to flow with (順).
- ji: string | null — What to seize (機).
- load_capacity: string | null — Load vs capacity balance.
- misalignment_signals: string | null — Where friction may appear.
- recommended_modes: string | null — Suggested approaches.
- avoid: string | null — What to avoid.
- self_check: string | null — A question for self-reflection.

Respond with ONLY valid JSON, no markdown or extra text. Be concise (output_contract max_length_words: 260)."""


# -----------------------------------------------------------------------------
# Model catalog
# -----------------------------------------------------------------------------

# Each subtype dict shape: { id, label, model, description, fallback? }
MODEL_CATALOG: dict[str, dict[str, Any]] = {
    "claude": {
        "label": "Claude",
        "provider": "Anthropic",
        "env": ["ANTHROPIC_API_KEY"],
        "subtypes": [
            {
                "id": "sonnet",
                "label": "Sonnet",
                "model": "claude-3-5-sonnet-20241022",
                "description": "Balanced flagship — best for most prompts.",
            },
            {
                "id": "opus",
                "label": "Opus",
                "model": "claude-3-opus-20240229",
                "description": "Deep reasoning for complex synthesis.",
            },
            {
                "id": "haiku",
                "label": "Haiku",
                "model": "claude-3-5-haiku-20241022",
                "description": "Fast, lightweight responses.",
            },
        ],
    },
    "chatgpt": {
        "label": "ChatGPT",
        "provider": "OpenAI",
        "env": ["OPENAI_API_KEY"],
        "subtypes": [
            {
                "id": "gpt-4o",
                "label": "GPT-4o",
                "model": "gpt-4o",
                "description": "OpenAI flagship multimodal.",
            },
            {
                "id": "gpt-4o-mini",
                "label": "GPT-4o mini",
                "model": "gpt-4o-mini",
                "description": "Fast & cheap general model.",
            },
            {
                "id": "reasoning",
                "label": "Reasoning (o-series)",
                "model": "o3-mini",
                "fallback": "o1-mini",
                "description": "Step-by-step reasoning model.",
            },
        ],
    },
    "gemini": {
        "label": "Gemini",
        "provider": "Google",
        "env": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "subtypes": [
            {
                "id": "pro",
                "label": "Pro",
                "model": "gemini/gemini-1.5-pro",
                "description": "Google flagship long-context.",
            },
            {
                "id": "flash",
                "label": "Flash",
                "model": "gemini/gemini-1.5-flash",
                "description": "Fast, cheap general model.",
            },
        ],
    },
    "deepseek": {
        "label": "DeepSeek",
        "provider": "DeepSeek",
        "env": ["DEEPSEEK_API_KEY"],
        "subtypes": [
            {
                "id": "chat",
                "label": "Chat",
                "model": "deepseek/deepseek-chat",
                "description": "DeepSeek V3 general chat.",
            },
            {
                "id": "reasoner",
                "label": "Reasoner",
                "model": "deepseek/deepseek-reasoner",
                "description": "DeepSeek R1 reasoning model.",
            },
        ],
    },
}

# Strongest model per family (used by parallel_judge / confidence_escalation).
FAMILY_STRONGEST: dict[str, str] = {
    "claude": "claude-3-opus-20240229",
    "chatgpt": "gpt-4o",
    "gemini": "gemini/gemini-1.5-pro",
    "deepseek": "deepseek/deepseek-reasoner",
}

# Cheap/fast model per family (used by confidence_escalation).
FAMILY_CHEAPEST: dict[str, str] = {
    "claude": "claude-3-5-haiku-20241022",
    "chatgpt": "gpt-4o-mini",
    "gemini": "gemini/gemini-1.5-flash",
    "deepseek": "deepseek/deepseek-chat",
}

# Fallback priority order: providers tried in this order when "fallback" runs.
FALLBACK_PRIORITY: list[str] = ["claude", "chatgpt", "gemini", "deepseek"]


class IntelligenceError(RuntimeError):
    """Friendly, user-facing error string for streamed responses."""


def family_key_configured(family_id: str) -> bool:
    """Return True iff at least one env var listed for the family is set."""
    fam = MODEL_CATALOG.get(family_id)
    if not fam:
        return False
    for var in fam.get("env", []):
        if os.environ.get(var):
            return True
    return False


def configured_families() -> list[str]:
    """Return list of family ids with at least one env key set."""
    return [fid for fid in MODEL_CATALOG if family_key_configured(fid)]


def resolve_subtype(family_id: str, subtype_id: str) -> dict[str, Any] | None:
    """Look up a subtype dict by family and subtype id."""
    fam = MODEL_CATALOG.get(family_id)
    if not fam:
        return None
    for st in fam.get("subtypes", []):
        if st["id"] == subtype_id:
            return st
    return None


def resolve_model(family_id: str, subtype_id: str) -> tuple[str | None, str | None]:
    """
    Return ``(model_name, fallback_model_or_none)`` for a given family+subtype.
    Returns (None, None) if family or subtype is unknown.
    """
    st = resolve_subtype(family_id, subtype_id)
    if not st:
        return None, None
    return st["model"], st.get("fallback")


def family_for_model(model_name: str) -> str | None:
    """Best-effort reverse lookup: which family does this LiteLLM model belong to?"""
    for fid, fam in MODEL_CATALOG.items():
        for st in fam.get("subtypes", []):
            if st["model"] == model_name or st.get("fallback") == model_name:
                return fid
    return None


# -----------------------------------------------------------------------------
# LiteLLM core helpers
# -----------------------------------------------------------------------------


def _normalize_messages(messages: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Coerce messages to the simple {role, content} shape LiteLLM expects."""
    out: list[dict[str, str]] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content")
        if content is None:
            # Pull from AI-SDK style "parts"
            parts = m.get("parts", [])
            text_chunks: list[str] = []
            for p in parts:
                if isinstance(p, dict) and p.get("type") == "text":
                    text_chunks.append(str(p.get("text", "")))
            content = "".join(text_chunks)
        out.append({"role": role, "content": str(content or "")})
    return out


def _ensure_system_prompt(messages: list[dict[str, str]], system: str | None) -> list[dict[str, str]]:
    """Prepend a system prompt if none present."""
    has_system = any(m.get("role") == "system" for m in messages)
    if has_system or not system:
        return messages
    return [{"role": "system", "content": system}, *messages]


def litellm_complete(
    model: str,
    messages: Iterable[dict[str, Any]],
    *,
    system: str | None = SYSTEM_PROMPT,
    temperature: float = 0.6,
    max_tokens: int = 1024,
    timeout: float = 45.0,
    fallback_model: str | None = None,
) -> str:
    """
    Non-streaming LiteLLM completion. Returns the assistant text.

    Raises ``IntelligenceError`` with a friendly message on failure.
    """
    norm = _normalize_messages(messages)
    norm = _ensure_system_prompt(norm, system)

    last_err: Exception | None = None
    for candidate in [m for m in (model, fallback_model) if m]:
        try:
            resp = litellm.completion(
                model=candidate,
                messages=norm,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                stream=False,
            )
            choices = getattr(resp, "choices", None) or []
            if not choices:
                continue
            msg = getattr(choices[0], "message", None) or {}
            content = getattr(msg, "content", None) if not isinstance(msg, dict) else msg.get("content")
            return (content or "").strip()
        except Exception as e:  # noqa: BLE001 — funnel into friendly error
            last_err = e
            continue

    raise IntelligenceError(_friendly_error(model, last_err))


def litellm_stream(
    model: str,
    messages: Iterable[dict[str, Any]],
    *,
    system: str | None = SYSTEM_PROMPT,
    temperature: float = 0.6,
    max_tokens: int = 1024,
    timeout: float = 60.0,
    fallback_model: str | None = None,
) -> Iterator[str]:
    """
    Stream tokens from LiteLLM, yielding plain text deltas.

    On failure, yields the friendly error string and stops.
    """
    norm = _normalize_messages(messages)
    norm = _ensure_system_prompt(norm, system)

    candidates = [m for m in (model, fallback_model) if m]
    last_err: Exception | None = None

    for candidate in candidates:
        try:
            stream = litellm.completion(
                model=candidate,
                messages=norm,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                stream=True,
            )
            for chunk in stream:
                # LiteLLM mirrors the OpenAI streaming shape.
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                content: str | None
                if delta is None:
                    content = None
                elif isinstance(delta, dict):
                    content = delta.get("content")
                else:
                    content = getattr(delta, "content", None)
                if content:
                    yield content
            return
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue

    yield _friendly_error(model, last_err)


def _friendly_error(model: str, err: Exception | None) -> str:
    """Map provider/SDK exceptions into a user-friendly streamable message."""
    fam = family_for_model(model) or "the selected provider"
    fam_label = MODEL_CATALOG.get(fam, {}).get("label", fam)
    env_keys = ", ".join(MODEL_CATALOG.get(fam, {}).get("env", []) or [])

    if err is None:
        return f"{fam_label} ({model}) returned no response. Try a different model."

    msg = str(err) or err.__class__.__name__
    lower = msg.lower()

    if "api key" in lower or "authentication" in lower or "unauthorized" in lower or "401" in lower:
        return (
            f"Missing or invalid API key for {fam_label}. "
            f"Set {env_keys} in backend/.env to enable {model}, then restart the backend."
        )
    if "not found" in lower or "404" in lower or "does not exist" in lower:
        return (
            f"{fam_label} model `{model}` is unavailable on your account. "
            "Try a different subtype or strategy."
        )
    if "rate" in lower and "limit" in lower:
        return f"{fam_label} rate limit hit. Wait a moment and try again."
    if "timeout" in lower or "timed out" in lower:
        return f"{fam_label} request timed out. Try again or pick a faster subtype."
    if "connection" in lower or "network" in lower or "dns" in lower:
        return f"Cannot reach {fam_label}. Check your network or provider status."

    return f"{fam_label} error ({model}): {msg[:200]}"


# -----------------------------------------------------------------------------
# Legacy DeepSeek shim — kept for /api/interpret backwards compatibility.
# -----------------------------------------------------------------------------


def has_deepseek_key() -> bool:
    """Check if DeepSeek API key is configured."""
    return bool(os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def get_deepseek_client() -> OpenAI:
    """OpenAI-compatible client pointed at DeepSeek's API."""
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise ValueError(
            "Set DEEPSEEK_API_KEY or OPENAI_API_KEY environment variable. "
            "Get a key at https://platform.deepseek.com/api_keys"
        )
    return OpenAI(api_key=api_key, base_url=base_url)


def interpret_with_llm(
    payload: dict[str, Any],
    *,
    model: str = "deepseek-chat",
    max_tokens: int = 800,
    temperature: float = 0.4,
) -> dict[str, Any]:
    """Send the interpretation payload to DeepSeek and parse a structured response."""
    client = get_deepseek_client()

    user_content = (
        f"{INTERPRET_INSTRUCTIONS}\n\n"
        "User data (includes moment, calendar, BaZi, Qimen, advanced_astro, ZWDS):\n"
        f"{json.dumps(payload, ensure_ascii=False, default=str)}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    content = (response.choices[0].message.content or "").strip()
    if not content:
        return {"current_summary": "No interpretation generated."}

    text = content
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end] if end > 0 else text[start:]
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        text = text[start:end] if end > 0 else text[start:]

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    return {"current_summary": content}


def chat_stream(
    messages: list[dict[str, str]],
    *,
    model: str = "deepseek-chat",
    max_tokens: int = 1024,
    temperature: float = 0.6,
):
    """
    Legacy DeepSeek streaming helper — kept for callers that import it directly.

    New code should prefer :func:`litellm_stream` or the ensemble dispatcher.
    """
    client = get_deepseek_client()

    system_present = any(m.get("role") == "system" for m in messages)
    if not system_present:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages,
        ]

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    )

    text_id = "text-1"
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and getattr(delta, "content", None):
            yield {"type": "text-delta", "id": text_id, "delta": delta.content}
