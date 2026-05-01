"""
Intelligence model service — provider catalog, LiteLLM router, and DeepSeek shim.

Every system prompt across all families is the Output Contract from
`backend.contracts.output_contract.OUTPUT_CONTRACT_SYSTEM`. The legacy
``Zhuang`` persona has been retired in favor of the description-engine spec.

Provider catalog:
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
try:
    import litellm  # type: ignore
except ImportError:  # pragma: no cover — install in dev only
    litellm = None  # noqa: F841

# Output Contract — the single source of truth for system prompts.
from backend.contracts.output_contract import (
    OUTPUT_CONTRACT_SYSTEM as _OUTPUT_CONTRACT_SYSTEM,
)


# -----------------------------------------------------------------------------
# System prompts — all derived from the Output Contract.
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = (
    _OUTPUT_CONTRACT_SYSTEM
    + "\n\nADDITIONAL CONSTRAINT (Alchemy / Wei Dan)\n"
    + "When TCM herbs or formulas appear in the context, describe their existing properties\n"
    + "(temperature, flavor, meridians) only. Do not prescribe. Do not diagnose.\n"
    + "If asked for a recommendation, refuse and describe instead.\n"
)

INTERPRET_INSTRUCTIONS = """Describe the configuration in the following payload. Return a JSON object with these exact keys (use null for any without sufficient signal):
- current_summary: string — 2–4 sentences describing how the natal configuration interacts with the present moment.
- shi: string | null — Timing description (Shí: ripeness vs prematurity).
- shun: string | null — Direction description (Shùn: alignment vs opposition to momentum).
- ji: string | null — Inflection-point observation (Jī).
- load_capacity: string | null — Load vs capacity description.
- misalignment_signals: string | null — Where friction is likely to appear if force is applied.
- recommended_modes: string | null — Modes that match the configuration (description, not prescription).
- avoid: string | null — Modes that would increase friction (description, not prescription).
- self_check: string | null — A neutral observation the user can verify.

Treat the payload as canonical (do not recompute math). If the payload features are weak,
return current_summary equal to the non-action phrase ("No dominant signal. Maintain course.")
and null for the rest. Respond with ONLY valid JSON. Max ~260 words."""


# -----------------------------------------------------------------------------
# Model catalog
# -----------------------------------------------------------------------------

MODEL_CATALOG: dict[str, dict[str, Any]] = {
    "claude": {
        "label": "Claude",
        "provider": "Anthropic",
        "env": ["ANTHROPIC_API_KEY"],
        "subtypes": [
            {"id": "sonnet", "label": "Sonnet", "model": "claude-3-5-sonnet-20241022", "description": "Balanced flagship — best for most prompts."},
            {"id": "opus", "label": "Opus", "model": "claude-3-opus-20240229", "description": "Deep reasoning for complex synthesis."},
            {"id": "haiku", "label": "Haiku", "model": "claude-3-5-haiku-20241022", "description": "Fast, lightweight responses."},
        ],
    },
    "chatgpt": {
        "label": "ChatGPT",
        "provider": "OpenAI",
        "env": ["OPENAI_API_KEY"],
        "subtypes": [
            {"id": "gpt-4o", "label": "GPT-4o", "model": "gpt-4o", "description": "OpenAI flagship multimodal."},
            {"id": "gpt-4o-mini", "label": "GPT-4o mini", "model": "gpt-4o-mini", "description": "Fast & cheap general model."},
            {"id": "reasoning", "label": "Reasoning (o-series)", "model": "o3-mini", "fallback": "o1-mini", "description": "Step-by-step reasoning model."},
        ],
    },
    "gemini": {
        "label": "Gemini",
        "provider": "Google",
        "env": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "subtypes": [
            {"id": "pro", "label": "Pro", "model": "gemini/gemini-1.5-pro", "description": "Google flagship long-context."},
            {"id": "flash", "label": "Flash", "model": "gemini/gemini-1.5-flash", "description": "Fast, cheap general model."},
        ],
    },
    "deepseek": {
        "label": "DeepSeek",
        "provider": "DeepSeek",
        "env": ["DEEPSEEK_API_KEY"],
        "subtypes": [
            {"id": "chat", "label": "Chat", "model": "deepseek/deepseek-chat", "description": "DeepSeek V3 general chat."},
            {"id": "reasoner", "label": "Reasoner", "model": "deepseek/deepseek-reasoner", "description": "DeepSeek R1 reasoning model."},
        ],
    },
}

FAMILY_STRONGEST: dict[str, str] = {
    "claude": "claude-3-opus-20240229",
    "chatgpt": "gpt-4o",
    "gemini": "gemini/gemini-1.5-pro",
    "deepseek": "deepseek/deepseek-reasoner",
}

FAMILY_CHEAPEST: dict[str, str] = {
    "claude": "claude-3-5-haiku-20241022",
    "chatgpt": "gpt-4o-mini",
    "gemini": "gemini/gemini-1.5-flash",
    "deepseek": "deepseek/deepseek-chat",
}

FALLBACK_PRIORITY: list[str] = ["claude", "chatgpt", "gemini", "deepseek"]


class IntelligenceError(RuntimeError):
    """Friendly, user-facing error string for streamed responses."""


def family_key_configured(family_id: str) -> bool:
    fam = MODEL_CATALOG.get(family_id)
    if not fam:
        return False
    for var in fam.get("env", []):
        if os.environ.get(var):
            return True
    return False


def configured_families() -> list[str]:
    return [fid for fid in MODEL_CATALOG if family_key_configured(fid)]


def resolve_subtype(family_id: str, subtype_id: str) -> dict[str, Any] | None:
    fam = MODEL_CATALOG.get(family_id)
    if not fam:
        return None
    for st in fam.get("subtypes", []):
        if st["id"] == subtype_id:
            return st
    return None


def resolve_model(family_id: str, subtype_id: str) -> tuple[str | None, str | None]:
    st = resolve_subtype(family_id, subtype_id)
    if not st:
        return None, None
    return st["model"], st.get("fallback")


def family_for_model(model_name: str) -> str | None:
    for fid, fam in MODEL_CATALOG.items():
        for st in fam.get("subtypes", []):
            if st["model"] == model_name or st.get("fallback") == model_name:
                return fid
    return None


# -----------------------------------------------------------------------------
# LiteLLM core helpers — every call is contract-bound.
# -----------------------------------------------------------------------------


def _normalize_messages(messages: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content")
        if content is None:
            parts = m.get("parts", [])
            text_chunks: list[str] = []
            for p in parts:
                if isinstance(p, dict) and p.get("type") == "text":
                    text_chunks.append(str(p.get("text", "")))
            content = "".join(text_chunks)
        out.append({"role": role, "content": str(content or "")})
    return out


def _ensure_system_prompt(
    messages: list[dict[str, str]], system: str | None
) -> list[dict[str, str]]:
    has_system = any(m.get("role") == "system" for m in messages)
    if has_system or not system:
        return messages
    return [{"role": "system", "content": system}, *messages]


def litellm_complete(
    model: str,
    messages: Iterable[dict[str, Any]],
    *,
    system: str | None = SYSTEM_PROMPT,
    temperature: float = 0.4,
    max_tokens: int = 1024,
    timeout: float = 45.0,
    fallback_model: str | None = None,
) -> str:
    """Non-streaming LiteLLM completion. Always contract-bound."""
    if litellm is None:
        raise IntelligenceError(
            "litellm is not installed. Run `pip install -r backend/requirements.txt`."
        )
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
            content = (
                getattr(msg, "content", None)
                if not isinstance(msg, dict)
                else msg.get("content")
            )
            return (content or "").strip()
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue

    raise IntelligenceError(_friendly_error(model, last_err))


def litellm_stream(
    model: str,
    messages: Iterable[dict[str, Any]],
    *,
    system: str | None = SYSTEM_PROMPT,
    temperature: float = 0.4,
    max_tokens: int = 1024,
    timeout: float = 60.0,
    fallback_model: str | None = None,
) -> Iterator[str]:
    """Stream tokens from LiteLLM, yielding plain text deltas. Contract-bound."""
    if litellm is None:
        yield "litellm is not installed. Run `pip install -r backend/requirements.txt`."
        return
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
    return bool(os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def get_deepseek_client() -> OpenAI:
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
    temperature: float = 0.4,
):
    """
    Legacy DeepSeek streaming. Always prepends the contract.
    """
    client = get_deepseek_client()

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
