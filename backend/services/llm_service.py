"""
Phase 4: DeepSeek LLM integration for Daoist herbal alchemy interpretations.

Uses the OpenAI-compatible DeepSeek API. Set DEEPSEEK_API_KEY (or OPENAI_API_KEY)
and optionally DEEPSEEK_BASE_URL for the API client.
"""

import json
import os
from typing import Any

from openai import OpenAI

# -----------------------------------------------------------------------------
# System prompt: Output Contract — descriptive timing instrument.
# Sourced from backend.contracts.output_contract; mirrors src/contracts.
# Educational tool only; never diagnose, prescribe, or predict.
# -----------------------------------------------------------------------------
from backend.contracts.output_contract import OUTPUT_CONTRACT_SYSTEM as _OUTPUT_CONTRACT_SYSTEM

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


def has_deepseek_key() -> bool:
    """Check if DeepSeek API key is configured."""
    return bool(os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def get_deepseek_client() -> OpenAI:
    """
    Create an OpenAI-compatible client configured for DeepSeek API.
    Reads DEEPSEEK_API_KEY or OPENAI_API_KEY from environment.
    Uses https://api.deepseek.com (official endpoint). Override with DEEPSEEK_BASE_URL if needed.
    """
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
    """
    Send the interpretation payload to DeepSeek and return a structured response.

    Args:
        payload: The full interpretation request (inputs, advanced_astro, zwds, etc.).
        model: DeepSeek model name.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.

    Returns:
        Parsed dict with current_summary, shi, shun, ji, etc. Falls back to
        {"current_summary": raw_text} if JSON parse fails.
    """
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

    # Try to extract JSON (in case model wraps in markdown)
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
    Stream chat completions from DeepSeek.
    Yields SSE chunks in AI SDK format: start, text-start, text-delta, text-end, finish.

    Always prepends OUTPUT_CONTRACT_SYSTEM. Callers may add their own
    system message, but the contract is non-negotiable.
    """
    client = get_deepseek_client()

    # Always prepend the contract.
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
