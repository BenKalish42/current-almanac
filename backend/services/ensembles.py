"""
Ensemble strategies for the Intelligence workbench.

Each strategy is a generator yielding plain text deltas. The dispatcher
``run_ensemble`` is consumed by :mod:`backend.main` which wraps each delta
into the existing AI-SDK SSE envelope (``text-delta`` events).

Strategies:
  - single                 — selected model only
  - fallback               — selected then configured-provider fallbacks
  - parallel_judge         — drafts across configured families, judged by selected
  - specialist_committee   — DeepSeek=Astrology, ChatGPT=Herbal, Claude=Plain Lang, Gemini=Synthesis
  - self_consistency       — N drafts on selected, consolidator pass
  - critic_reviser         — draft → critique → revise (selected)
  - confidence_escalation  — cheap first; escalate on uncertainty/safety markers
  - structured_verifier    — primary draft + verifier audit pass

Intermediate passes are non-streaming (``litellm_complete``) so the user only
sees the final pass stream. We emit short status delta lines like
``> drafting with claude-opus…`` so the UI shows progress without breaking the
SSE contract.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Iterator

from .llm_service import (
    FALLBACK_PRIORITY,
    FAMILY_CHEAPEST,
    FAMILY_STRONGEST,
    MODEL_CATALOG,
    SYSTEM_PROMPT,
    IntelligenceError,
    configured_families,
    family_key_configured,
    litellm_complete,
    litellm_stream,
    resolve_model,
)


# -----------------------------------------------------------------------------
# Types & helpers
# -----------------------------------------------------------------------------


IntelligenceOptions = dict[str, Any]
"""
Shape:
  {
    "family": "claude"|"chatgpt"|"gemini"|"deepseek",
    "model":  subtype id,
    "strategy": "single"|...,
    "selectedModelsByFamily": {family_id: subtype_id},
    "ragEnabled": bool,
  }
"""


def _status(line: str) -> str:
    """Format a status line as a streamed delta (visible to user)."""
    return f"> {line}\n"


def _resolve(family: str | None, subtype: str | None) -> tuple[str | None, str | None]:
    if not family or not subtype:
        return None, None
    return resolve_model(family, subtype)


def _default_subtype(family: str) -> str | None:
    fam = MODEL_CATALOG.get(family)
    if not fam or not fam.get("subtypes"):
        return None
    return fam["subtypes"][0]["id"]


def _system_with_rag(rag_context: str | None) -> str:
    """Combine the Zhuang persona with optional RAG context."""
    if rag_context:
        return f"{SYSTEM_PROMPT}\n\n{rag_context}"
    return SYSTEM_PROMPT


def _selected_model(opts: IntelligenceOptions) -> tuple[str, str, str | None]:
    """Resolve (family_id, model_name, fallback_model) from options. Defaults applied."""
    family = opts.get("family") or "deepseek"
    subtype = opts.get("model") or _default_subtype(family) or "chat"
    model, fallback = _resolve(family, subtype)
    if not model:
        # Bad subtype — fall back to family's first subtype.
        subtype = _default_subtype(family) or "chat"
        model, fallback = _resolve(family, subtype)
    return family, (model or ""), fallback


def _selected_model_for(opts: IntelligenceOptions, family: str) -> tuple[str, str | None]:
    """Resolve the user's chosen subtype for ``family`` (not the active family)."""
    sel = (opts.get("selectedModelsByFamily") or {}).get(family) or _default_subtype(family) or ""
    model, fallback = _resolve(family, sel)
    return (model or ""), fallback


def _missing_key_message(family: str) -> str:
    fam = MODEL_CATALOG.get(family, {})
    label = fam.get("label", family)
    env_keys = ", ".join(fam.get("env", []) or [])
    return (
        f"Missing API key for {label}. Set {env_keys} in backend/.env to enable this provider, "
        "then restart the backend. The Intelligence workbench will route through this model "
        "as soon as the key is configured."
    )


# -----------------------------------------------------------------------------
# Strategies
# -----------------------------------------------------------------------------


def run_single(messages: list[dict[str, Any]], opts: IntelligenceOptions, rag_context: str | None) -> Iterator[str]:
    family, model, fallback = _selected_model(opts)

    if not family_key_configured(family):
        yield _missing_key_message(family)
        return

    yield _status(f"routing to {family} · {model}")
    yield from litellm_stream(
        model=model,
        fallback_model=fallback,
        messages=messages,
        system=_system_with_rag(rag_context),
    )


def run_fallback(messages: list[dict[str, Any]], opts: IntelligenceOptions, rag_context: str | None) -> Iterator[str]:
    family, model, fallback = _selected_model(opts)

    chain: list[tuple[str, str, str | None]] = []
    if model:
        chain.append((family, model, fallback))
    for fid in FALLBACK_PRIORITY:
        if fid == family:
            continue
        m, fb = _selected_model_for(opts, fid)
        if m:
            chain.append((fid, m, fb))

    configured = configured_families()
    if not configured:
        yield (
            "No provider keys configured. Add ANTHROPIC_API_KEY, OPENAI_API_KEY, "
            "GEMINI_API_KEY, or DEEPSEEK_API_KEY to backend/.env, then restart the backend."
        )
        return

    last_err: str | None = None
    for fid, m, fb in chain:
        if not family_key_configured(fid):
            yield _status(f"skipping {fid} ({m}) — missing key")
            continue
        yield _status(f"trying {fid} · {m}")
        try:
            got_any = False
            for delta in litellm_stream(
                model=m,
                fallback_model=fb,
                messages=messages,
                system=_system_with_rag(rag_context),
            ):
                got_any = True
                yield delta
            if got_any:
                return
            last_err = f"{fid} returned no content"
        except IntelligenceError as e:
            last_err = str(e)
            yield _status(f"{fid} failed: {last_err}")
            continue

    if last_err:
        yield f"\nAll configured providers failed. Last error: {last_err}"


def run_parallel_judge(messages: list[dict[str, Any]], opts: IntelligenceOptions, rag_context: str | None) -> Iterator[str]:
    family, judge_model, judge_fallback = _selected_model(opts)
    system = _system_with_rag(rag_context)

    drafts: list[tuple[str, str]] = []  # (family_label, text)
    for fid in FALLBACK_PRIORITY:
        if not family_key_configured(fid):
            continue
        m, fb = _selected_model_for(opts, fid)
        if not m:
            continue
        label = MODEL_CATALOG[fid]["label"]
        yield _status(f"drafting · {label} ({m})")
        try:
            text = litellm_complete(
                model=m,
                fallback_model=fb,
                messages=messages,
                system=system,
                max_tokens=600,
                temperature=0.5,
            )
            if text:
                drafts.append((label, text))
        except IntelligenceError as e:
            yield _status(f"{label} draft failed: {e}")

    if not drafts:
        yield (
            "No provider keys configured for parallel_judge. "
            "Add at least one provider key in backend/.env."
        )
        return

    if not family_key_configured(family):
        yield _missing_key_message(family)
        return

    yield _status(f"synthesizing with judge · {family} ({judge_model})")
    judge_prompt = [
        {
            "role": "user",
            "content": (
                "You are the Judge. Below are independent drafts from multiple AI models "
                "responding to the same user question. Synthesize a single clear, accurate, "
                "Daoist-grounded answer that takes the strongest points of each draft and "
                "resolves contradictions.\n\n"
                "Original question:\n"
                f"{_last_user(messages)}\n\n"
                + "\n\n".join(f"### Draft from {label}\n{text}" for label, text in drafts)
            ),
        }
    ]
    yield from litellm_stream(
        model=judge_model,
        fallback_model=judge_fallback,
        messages=judge_prompt,
        system=system,
    )


_SPECIALIST_ROLES: dict[str, str] = {
    "deepseek": (
        "You cover the **Astrology** lens. Read the user's question through Daoist astrology — "
        "BaZi, Five Phases, current Qi tides. Output a focused 2-paragraph note titled "
        "'Astrology Read'."
    ),
    "chatgpt": (
        "You cover the **Herbal Alchemy** lens. Read the user's question through clinical TCM "
        "herbal pattern matching. Reference herbs and formulas only from the Retrieved Knowledge "
        "if any was provided. Output a focused 2-paragraph note titled 'Herbal Read'."
    ),
    "claude": (
        "You cover the **Plain Language** lens. Translate the question and likely advice into "
        "warm, accessible everyday language with no jargon. Output a focused 2-paragraph note "
        "titled 'Plain Language'."
    ),
    "gemini": (
        "You are the **Synthesizer**. Take the three specialist notes (Astrology, Herbal, Plain "
        "Language) and weave them into a unified Daoist response. Keep the safety disclaimer."
    ),
}


def run_specialist_committee(messages: list[dict[str, Any]], opts: IntelligenceOptions, rag_context: str | None) -> Iterator[str]:
    system = _system_with_rag(rag_context)
    notes: list[tuple[str, str]] = []

    for fid in ("deepseek", "chatgpt", "claude"):
        if not family_key_configured(fid):
            yield _status(f"skipping specialist {fid} — missing key")
            continue
        m, fb = _selected_model_for(opts, fid)
        if not m:
            continue
        yield _status(f"specialist · {fid} ({m})")
        try:
            text = litellm_complete(
                model=m,
                fallback_model=fb,
                messages=messages,
                system=f"{system}\n\n{_SPECIALIST_ROLES[fid]}",
                max_tokens=500,
                temperature=0.5,
            )
            if text:
                notes.append((fid, text))
        except IntelligenceError as e:
            yield _status(f"specialist {fid} failed: {e}")

    if not notes:
        yield (
            "No specialist providers configured. Add at least one of ANTHROPIC_API_KEY, "
            "OPENAI_API_KEY, or DEEPSEEK_API_KEY to backend/.env."
        )
        return

    # Synthesizer is Gemini if configured, else fall back to selected family.
    synth_family = "gemini" if family_key_configured("gemini") else (opts.get("family") or "deepseek")
    if not family_key_configured(synth_family):
        # Use whoever is configured.
        configured = configured_families()
        if not configured:
            yield "No synthesizer available — no provider keys configured."
            return
        synth_family = configured[0]

    synth_subtype = (opts.get("selectedModelsByFamily") or {}).get(synth_family) or _default_subtype(synth_family) or ""
    synth_model, synth_fallback = _resolve(synth_family, synth_subtype)
    if not synth_model:
        yield "Synthesizer model unresolved — try a different family."
        return

    yield _status(f"synthesizing · {synth_family} ({synth_model})")
    synth_messages = [
        {
            "role": "user",
            "content": (
                "Specialist notes from the Intelligence Committee follow. Synthesize them into "
                "one unified Daoist response to the user. Preserve the safety disclaimer.\n\n"
                f"User question:\n{_last_user(messages)}\n\n"
                + "\n\n".join(f"### {fid.title()} note\n{text}" for fid, text in notes)
            ),
        }
    ]
    yield from litellm_stream(
        model=synth_model,
        fallback_model=synth_fallback,
        messages=synth_messages,
        system=f"{system}\n\n{_SPECIALIST_ROLES['gemini']}",
    )


def run_self_consistency(messages: list[dict[str, Any]], opts: IntelligenceOptions, rag_context: str | None) -> Iterator[str]:
    family, model, fallback = _selected_model(opts)
    if not family_key_configured(family):
        yield _missing_key_message(family)
        return

    system = _system_with_rag(rag_context)
    n_drafts = 3
    drafts: list[str] = []

    for i in range(n_drafts):
        yield _status(f"draft {i + 1}/{n_drafts} · {family} ({model})")
        try:
            text = litellm_complete(
                model=model,
                fallback_model=fallback,
                messages=messages,
                system=system,
                max_tokens=500,
                temperature=0.9,
            )
            if text:
                drafts.append(text)
        except IntelligenceError as e:
            yield _status(f"draft {i + 1} failed: {e}")

    if not drafts:
        yield "Self-consistency drafting failed. Try a different model or strategy."
        return

    yield _status("consolidating consensus")
    consolidator_messages = [
        {
            "role": "user",
            "content": (
                "Below are independent drafts you produced for the same question. Reconcile "
                "them. Identify the consensus answer. Where drafts disagree, pick the most "
                "Daoist-grounded option. Output a single coherent response.\n\n"
                f"User question:\n{_last_user(messages)}\n\n"
                + "\n\n".join(f"### Draft {i + 1}\n{text}" for i, text in enumerate(drafts))
            ),
        }
    ]
    yield from litellm_stream(
        model=model,
        fallback_model=fallback,
        messages=consolidator_messages,
        system=system,
        temperature=0.4,
    )


def run_critic_reviser(messages: list[dict[str, Any]], opts: IntelligenceOptions, rag_context: str | None) -> Iterator[str]:
    family, model, fallback = _selected_model(opts)
    if not family_key_configured(family):
        yield _missing_key_message(family)
        return

    system = _system_with_rag(rag_context)

    yield _status(f"drafting · {family} ({model})")
    try:
        draft = litellm_complete(
            model=model,
            fallback_model=fallback,
            messages=messages,
            system=system,
            max_tokens=600,
            temperature=0.6,
        )
    except IntelligenceError as e:
        yield str(e)
        return

    if not draft:
        yield "Draft pass produced no output."
        return

    yield _status("critiquing draft")
    critic_system = (
        f"{system}\n\nYou are the Critic. Find inaccuracies, missing safety notes, "
        "unsupported herb/formula recommendations, weak Daoist framing, and tone issues. "
        "Be specific. Bullet points only."
    )
    try:
        critique = litellm_complete(
            model=model,
            fallback_model=fallback,
            messages=[
                {"role": "user", "content": f"User question:\n{_last_user(messages)}\n\nDraft:\n{draft}"}
            ],
            system=critic_system,
            max_tokens=400,
            temperature=0.4,
        )
    except IntelligenceError as e:
        critique = f"(critique unavailable: {e})"

    yield _status("revising")
    reviser_messages = [
        {
            "role": "user",
            "content": (
                "Apply the Critic's feedback and produce a final, improved answer. "
                "Preserve the Daoist tone and safety disclaimer.\n\n"
                f"User question:\n{_last_user(messages)}\n\n"
                f"Draft:\n{draft}\n\n"
                f"Critic notes:\n{critique}"
            ),
        }
    ]
    yield from litellm_stream(
        model=model,
        fallback_model=fallback,
        messages=reviser_messages,
        system=system,
    )


_UNCERTAINTY_RE = re.compile(
    r"\b(uncertain|not sure|consult|contraindic|pregnan|toxic|interaction|"
    r"dose|dosage|overdose|emergency|warning|please see)\b",
    re.IGNORECASE,
)


def run_confidence_escalation(messages: list[dict[str, Any]], opts: IntelligenceOptions, rag_context: str | None) -> Iterator[str]:
    family = opts.get("family") or "deepseek"
    if not family_key_configured(family):
        yield _missing_key_message(family)
        return

    cheap_model = FAMILY_CHEAPEST.get(family)
    strong_model = FAMILY_STRONGEST.get(family)
    if not cheap_model or not strong_model:
        yield from run_single(messages, opts, rag_context)
        return

    system = _system_with_rag(rag_context)

    yield _status(f"trying cheap pass · {family} ({cheap_model})")
    try:
        cheap_text = litellm_complete(
            model=cheap_model,
            messages=messages,
            system=system,
            max_tokens=500,
            temperature=0.5,
        )
    except IntelligenceError as e:
        yield _status(f"cheap pass failed: {e}")
        cheap_text = ""

    if cheap_text and not _UNCERTAINTY_RE.search(cheap_text):
        # Confident enough — re-stream so the UX is consistent.
        yield _status("confident — streaming cheap response")
        # Stream a passthrough by chunking the cheap text.
        for chunk in _chunk_text(cheap_text):
            yield chunk
        return

    yield _status(f"escalating · {family} ({strong_model})")
    yield from litellm_stream(
        model=strong_model,
        messages=messages,
        system=system,
    )


def run_structured_verifier(messages: list[dict[str, Any]], opts: IntelligenceOptions, rag_context: str | None) -> Iterator[str]:
    family, model, fallback = _selected_model(opts)
    if not family_key_configured(family):
        yield _missing_key_message(family)
        return

    system = _system_with_rag(rag_context)

    yield _status(f"primary draft · {family} ({model})")
    primary_chunks: list[str] = []
    for delta in litellm_stream(
        model=model,
        fallback_model=fallback,
        messages=messages,
        system=system,
    ):
        primary_chunks.append(delta)
        yield delta
    primary_text = "".join(primary_chunks)

    if not primary_text:
        return

    yield "\n\n---\n**Verification pass:**\n"

    verifier_system = (
        f"{system}\n\nYou are the Safety Verifier. Audit the primary answer below.\n"
        "Check: (1) Daoist safety disclaimer present? (2) Any herb/formula mentioned that is "
        "NOT in the Retrieved Knowledge context? Flag those. (3) Any safety_tier 3 herb? "
        "Flag prominently. (4) Any unsupported medical claim? Output a short Markdown audit "
        "with bullet points; if everything checks out, write 'No issues detected.'"
    )
    yield from litellm_stream(
        model=model,
        fallback_model=fallback,
        messages=[
            {
                "role": "user",
                "content": (
                    f"User question:\n{_last_user(messages)}\n\nPrimary answer:\n{primary_text}"
                ),
            }
        ],
        system=verifier_system,
        max_tokens=400,
        temperature=0.2,
    )


# -----------------------------------------------------------------------------
# Dispatcher
# -----------------------------------------------------------------------------


_STRATEGY_REGISTRY = {
    "single": run_single,
    "fallback": run_fallback,
    "parallel_judge": run_parallel_judge,
    "specialist_committee": run_specialist_committee,
    "self_consistency": run_self_consistency,
    "critic_reviser": run_critic_reviser,
    "confidence_escalation": run_confidence_escalation,
    "structured_verifier": run_structured_verifier,
}


def run_ensemble(
    strategy: str,
    messages: Iterable[dict[str, Any]],
    opts: IntelligenceOptions,
    rag_context: str | None = None,
) -> Iterator[str]:
    """Dispatch to the named strategy. Unknown strategies fall back to ``single``."""
    msg_list = list(messages)
    fn = _STRATEGY_REGISTRY.get(strategy or "single", run_single)
    yield from fn(msg_list, opts or {}, rag_context)


# -----------------------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------------------


def _last_user(messages: list[dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            content = m.get("content")
            if isinstance(content, str):
                return content
            # AI-SDK parts shape
            parts = m.get("parts") or []
            chunks = [str(p.get("text", "")) for p in parts if isinstance(p, dict) and p.get("type") == "text"]
            return "".join(chunks)
    return ""


def _chunk_text(text: str, *, size: int = 24) -> Iterator[str]:
    """Yield ``text`` in small chunks for a cheaper-than-real streaming feel."""
    for i in range(0, len(text), size):
        yield text[i : i + size]
