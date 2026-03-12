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
# System prompt: Master Daoist herbal alchemist persona (Zhuang)
# CRITICAL: Educational tool only; never diagnose or treat.
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
    temperature: float = 0.6,
):
    """
    Stream chat completions from DeepSeek.
    Yields SSE chunks in AI SDK format: start, text-start, text-delta, text-end, finish.
    """
    client = get_deepseek_client()

    # Build messages with system context if not present
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
