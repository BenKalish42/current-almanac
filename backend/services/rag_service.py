"""
KnowledgeRAG — retrieval over the Daoist herb / formula / meridian graph.

Primary backend: Neo4j with the labels/relationships documented in
``docs/architecture/current_neo4j_state.md`` (``Herb``, ``Formula``, ``Meridian``;
``ENTERS``, ``INCLUDED_IN``).

Fallback: when the Neo4j driver cannot connect (no env, password missing,
service unavailable), we scan the local seed JSON via :mod:`backend.db` so the
chat keeps surfacing relevant herbs and formulas.

Cypher security: all queries are strictly parameterized — no f-strings or
string concatenation per ``.cursor/rules/neo4j-cypher.mdc``.
"""

from __future__ import annotations

import os
import re
import string
from typing import Any

try:
    from neo4j import GraphDatabase  # type: ignore
    from neo4j.exceptions import Neo4jError, ServiceUnavailable  # type: ignore

    _NEO4J_AVAILABLE = True
except Exception:  # noqa: BLE001
    GraphDatabase = None  # type: ignore[assignment]
    Neo4jError = Exception  # type: ignore[assignment,misc]
    ServiceUnavailable = Exception  # type: ignore[assignment,misc]
    _NEO4J_AVAILABLE = False

from ..db import load_seed_formulas, load_seed_herbs

# -----------------------------------------------------------------------------
# Tokenization helpers
# -----------------------------------------------------------------------------

_STOPWORDS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "and", "or", "is", "it", "my", "for", "with",
        "of", "to", "in", "on", "about", "how", "can", "what", "need",
        "should", "could", "would", "you", "we", "i", "me", "do", "does",
        "this", "that", "those", "these", "be", "are", "was", "were",
        "have", "has", "had", "but", "from", "into", "by", "as", "at",
    }
)

_PUNCT_RE = re.compile(rf"[{re.escape(string.punctuation)}]+")


def extract_keywords(text: str, *, max_tokens: int = 6, min_len: int = 3) -> list[str]:
    """Lower-case, strip punctuation, drop stopwords/short tokens, dedupe."""
    if not text:
        return []
    cleaned = _PUNCT_RE.sub(" ", text.lower())
    seen: list[str] = []
    seen_set: set[str] = set()
    for raw in cleaned.split():
        tok = raw.strip()
        if len(tok) < min_len:
            continue
        if tok in _STOPWORDS:
            continue
        if tok in seen_set:
            continue
        seen_set.add(tok)
        seen.append(tok)
        if len(seen) >= max_tokens:
            break
    return seen


# -----------------------------------------------------------------------------
# Cypher templates (parameterized — never modify these via f-string)
# -----------------------------------------------------------------------------

_HERB_CYPHER = """
MATCH (h:Herb)
WHERE toLower(coalesce(h.english, '')) CONTAINS $needle
   OR toLower(coalesce(h.pinyin_normalized, '')) CONTAINS $needle
   OR toLower(coalesce(h.pinyin, '')) CONTAINS $needle
OPTIONAL MATCH (h)-[:ENTERS]->(m:Meridian)
RETURN h.id AS id,
       h.english AS english,
       h.pinyin AS pinyin,
       h.safety_tier AS safety_tier,
       collect(DISTINCT m.name) AS meridians
LIMIT $k
""".strip()

_FORMULA_CYPHER = """
MATCH (f:Formula)
WHERE toLower(coalesce(f.english, '')) CONTAINS $needle
   OR toLower(coalesce(f.pinyin, '')) CONTAINS $needle
   OR toLower(coalesce(f.pattern, '')) CONTAINS $needle
OPTIONAL MATCH (h:Herb)-[:INCLUDED_IN]->(f)
WITH f, collect(DISTINCT h.pinyin) AS herbs
RETURN f.id AS id,
       f.english AS english,
       f.pinyin AS pinyin,
       f.pattern AS pattern,
       herbs[0..6] AS herbs
LIMIT $k
""".strip()

_PING_CYPHER = "RETURN 1 AS ok"


# -----------------------------------------------------------------------------
# KnowledgeRAG
# -----------------------------------------------------------------------------


class KnowledgeRAG:
    """Singleton-style helper for retrieving herb/formula context."""

    def __init__(self) -> None:
        self._driver: Any = None
        self._driver_checked: bool = False
        self._available: bool = False

    # ----- driver lifecycle -------------------------------------------------

    def _ensure_driver(self) -> Any | None:
        """Lazy connect; cache result. Returns the driver or ``None`` on failure."""
        if self._driver_checked:
            return self._driver

        self._driver_checked = True

        if not _NEO4J_AVAILABLE or GraphDatabase is None:
            return None

        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD")
        if not password:
            return None

        try:
            driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
                connection_timeout=2.0,
            )
            # Cheap connectivity probe.
            with driver.session() as session:
                session.run(_PING_CYPHER).consume()
            self._driver = driver
            self._available = True
            return driver
        except (ServiceUnavailable, Neo4jError, Exception):  # noqa: BLE001
            self._driver = None
            self._available = False
            return None

    def is_available(self) -> bool:
        """Cheap probe: True if Neo4j is reachable AND auth succeeds."""
        self._ensure_driver()
        return self._available

    def close(self) -> None:
        if self._driver is not None:
            try:
                self._driver.close()
            except Exception:  # noqa: BLE001
                pass
        self._driver = None
        self._driver_checked = False
        self._available = False

    # ----- retrieval --------------------------------------------------------

    def retrieve(self, query: str, *, k: int = 5) -> dict[str, Any]:
        """
        Return ``{"herbs": [...], "formulas": [...], "source": "neo4j"|"seed"}``.

        Each result carries a small bag of fields suitable for prompt context.
        """
        keywords = extract_keywords(query)
        if not keywords:
            return {"herbs": [], "formulas": [], "source": "empty"}

        driver = self._ensure_driver()
        if driver is not None:
            try:
                return self._retrieve_neo4j(driver, keywords, k)
            except Exception:  # noqa: BLE001 — fall through to seed
                self._available = False
        return self._retrieve_seed(keywords, k)

    def _retrieve_neo4j(self, driver: Any, keywords: list[str], k: int) -> dict[str, Any]:
        herbs_by_id: dict[str, dict[str, Any]] = {}
        formulas_by_id: dict[str, dict[str, Any]] = {}

        with driver.session() as session:
            for token in keywords:
                params = {"needle": token, "k": k}

                herb_result = session.run(_HERB_CYPHER, params)
                for rec in herb_result:
                    rid = rec.get("id") or ""
                    if rid and rid not in herbs_by_id:
                        herbs_by_id[rid] = {
                            "id": rid,
                            "english": rec.get("english"),
                            "pinyin": rec.get("pinyin"),
                            "safety_tier": rec.get("safety_tier"),
                            "meridians": [m for m in (rec.get("meridians") or []) if m],
                        }

                formula_result = session.run(_FORMULA_CYPHER, params)
                for rec in formula_result:
                    rid = rec.get("id") or ""
                    if rid and rid not in formulas_by_id:
                        formulas_by_id[rid] = {
                            "id": rid,
                            "english": rec.get("english"),
                            "pinyin": rec.get("pinyin"),
                            "pattern": rec.get("pattern"),
                            "herbs": [h for h in (rec.get("herbs") or []) if h],
                        }

        return {
            "herbs": list(herbs_by_id.values())[:k],
            "formulas": list(formulas_by_id.values())[:k],
            "source": "neo4j",
        }

    def _retrieve_seed(self, keywords: list[str], k: int) -> dict[str, Any]:
        herbs_seed = load_seed_herbs()
        formulas_seed = load_seed_formulas()

        def herb_haystack(h: dict[str, Any]) -> str:
            parts = [
                str(h.get("pinyin_name") or ""),
                str(h.get("common_name") or ""),
                " ".join(str(a) for a in (h.get("aliases") or [])),
                " ".join(str(a) for a in (h.get("actions") or [])),
            ]
            return " ".join(parts).lower()

        def formula_haystack(f: dict[str, Any]) -> str:
            parts = [
                str(f.get("pinyin_name") or ""),
                str(f.get("common_name") or ""),
                str(f.get("primary_pattern") or ""),
                " ".join(str(a) for a in (f.get("actions") or [])),
            ]
            return " ".join(parts).lower()

        herbs_out: list[dict[str, Any]] = []
        for h in herbs_seed:
            hay = herb_haystack(h)
            if any(token in hay for token in keywords):
                herbs_out.append(
                    {
                        "id": h.get("id"),
                        "english": h.get("common_name"),
                        "pinyin": h.get("pinyin_name"),
                        "safety_tier": h.get("safety_tier"),
                        "meridians": list((h.get("properties") or {}).get("meridians") or []),
                    }
                )
                if len(herbs_out) >= k:
                    break

        formulas_out: list[dict[str, Any]] = []
        for f in formulas_seed:
            hay = formula_haystack(f)
            if any(token in hay for token in keywords):
                arch = f.get("architecture") or []
                formulas_out.append(
                    {
                        "id": f.get("id"),
                        "english": f.get("common_name"),
                        "pinyin": f.get("pinyin_name"),
                        "pattern": f.get("primary_pattern"),
                        "herbs": [a.get("pinyin_name") for a in arch[:6] if a.get("pinyin_name")],
                    }
                )
                if len(formulas_out) >= k:
                    break

        return {"herbs": herbs_out, "formulas": formulas_out, "source": "seed"}


# Module-level singleton — main.py imports this.
rag = KnowledgeRAG()


# -----------------------------------------------------------------------------
# Context formatting
# -----------------------------------------------------------------------------


def format_context(snippets: dict[str, Any], *, max_chars: int = 1500) -> str:
    """Render a compact markdown block suitable for prepending to the system prompt."""
    herbs = snippets.get("herbs") or []
    formulas = snippets.get("formulas") or []
    source = snippets.get("source", "neo4j")

    if not herbs and not formulas:
        return ""

    lines: list[str] = ["### Retrieved Knowledge (KnowledgeRAG)"]
    lines.append(f"_source: {source}_")

    if herbs:
        lines.append("")
        lines.append("**Herbs:**")
        for h in herbs:
            pinyin = h.get("pinyin") or h.get("id") or "(unknown)"
            english = h.get("english") or "—"
            meridians = ", ".join(h.get("meridians") or []) or "—"
            tier = h.get("safety_tier")
            tier_label = f"safety_tier {tier}" if tier is not None else "safety_tier ?"
            lines.append(f"- {pinyin} ({english}) · {meridians} · {tier_label}")

    if formulas:
        lines.append("")
        lines.append("**Formulas:**")
        for f in formulas:
            pinyin = f.get("pinyin") or f.get("id") or "(unknown)"
            english = f.get("english") or "—"
            pattern = f.get("pattern") or "—"
            herbs_list = ", ".join(f.get("herbs") or []) or "—"
            lines.append(f"- {pinyin} ({english}) — {pattern} · key herbs: {herbs_list}")

    block = "\n".join(lines)
    if len(block) > max_chars:
        block = block[: max_chars - 1].rstrip() + "…"
    return block
