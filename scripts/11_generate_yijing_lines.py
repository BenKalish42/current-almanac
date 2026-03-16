#!/usr/bin/env python3
"""
Phase 2.5 Task 11.9: Yi Jing Line Analysis Generator.
Orchestrates LLM generation of 2,304 Yi Jing line descriptions (64 hexagrams × 6 lines × 6 philosophies).
Uses primary source texts from src/data/chunked/ (or data/chunked/), stitched by tradition, fed to the LLM.
Output schema: { hexagramId: { lineNumber: { daoism, confucianism, buddhism, psychology, humandesign, genekeys } } }
Resumable: skips hexagrams already present. Incremental save after each hexagram.
"""

import json
import os
import re
import time
from pathlib import Path

from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKED_CANDIDATES = [
    PROJECT_ROOT / "data" / "chunked",
    PROJECT_ROOT / "src" / "data" / "chunked",
]
SEED_HEX_PATH = PROJECT_ROOT / "src" / "data" / "seed_hexagrams.json"
OUTPUT_PATH = PROJECT_ROOT / "src" / "data" / "yiJingLines.json"
SLEEP_BETWEEN_CALLS = 1.5
MAX_CHARS_PER_SOURCE = 25_000  # Truncate long sources to stay under model context limit

SYSTEM_PROMPT = """You are an expert Daoist synthesizer. I am providing you with multiple primary source texts for a single I Ching Hexagram, labeled by their tradition. Your task is to extract the meanings for Line 1 through Line 6, mapping them to 6 specific lenses: daoism, confucianism, buddhism, psychology, humandesign, genekeys. Base your extraction STRICTLY on the provided source texts. If a specific lens is missing from the texts, provide a historically accurate, expert synthesis.

Return ONLY a strict JSON object matching this exact schema—no markdown, no code fences, no extra keys:
{
  "1": { "daoism": "...", "confucianism": "...", "buddhism": "...", "psychology": "...", "humandesign": "...", "genekeys": "..." },
  "2": { "daoism": "...", "confucianism": "...", "buddhism": "...", "psychology": "...", "humandesign": "...", "genekeys": "..." },
  "3": { "daoism": "...", "confucianism": "...", "buddhism": "...", "psychology": "...", "humandesign": "...", "genekeys": "..." },
  "4": { "daoism": "...", "confucianism": "...", "buddhism": "...", "psychology": "...", "humandesign": "...", "genekeys": "..." },
  "5": { "daoism": "...", "confucianism": "...", "buddhism": "...", "psychology": "...", "humandesign": "...", "genekeys": "..." },
  "6": { "daoism": "...", "confucianism": "...", "buddhism": "...", "psychology": "...", "humandesign": "...", "genekeys": "..." }
}
Each value must be a string (2–4 sentences). Keys "1" through "6" are line numbers (1 = bottom, 6 = top)."""


def _load_env() -> None:
    """Load .env from project root or backend/."""
    for env_path in (PROJECT_ROOT / ".env", PROJECT_ROOT / "backend" / ".env"):
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    v = v.strip().strip('"').strip("'")
                    os.environ.setdefault(k.strip(), v)


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise ValueError(
            "Set DEEPSEEK_API_KEY or OPENAI_API_KEY in .env. Get a key at https://platform.deepseek.com/api_keys"
        )
    return OpenAI(api_key=api_key, base_url=base_url)


def get_chunked_base() -> Path:
    """Return the chunked directory (data/chunked or src/data/chunked)."""
    for candidate in CHUNKED_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Chunked directory not found. Tried: {CHUNKED_CANDIDATES}"
    )


def load_combined_context(hex_id: int) -> tuple[str, list[str]]:
    """
    Scan all subfolders in chunked base for hex_{id:02d}.txt.
    Stitch contents with SOURCE headers into combined_context.
    Returns (combined_context, list of folder names found).
    """
    base = get_chunked_base()
    hex_filename = f"hex_{hex_id:02d}.txt"
    combined_context = ""
    sources_found: list[str] = []

    for item in sorted(base.iterdir()):
        if not item.is_dir():
            continue
        folder_name = item.name
        file_path = item / hex_filename
        if not file_path.exists():
            continue
        sources_found.append(folder_name)
        content = file_path.read_text(encoding="utf-8", errors="replace").strip()
        if len(content) > MAX_CHARS_PER_SOURCE:
            content = content[:MAX_CHARS_PER_SOURCE] + "\n\n[... truncated for context limit ...]"
        combined_context += f"\n\n--- SOURCE: {folder_name} ---\n{content}"

    return (combined_context.strip() if combined_context else "", sources_found)


def load_hexagrams() -> list[dict]:
    """Load hexagram metadata from seed_hexagrams.json."""
    data = json.loads(SEED_HEX_PATH.read_text())
    return data if isinstance(data, list) else list(data.values()) if isinstance(data, dict) else []


def extract_json(text: str) -> dict:
    """Extract JSON object from response, handling markdown code blocks."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


def _is_placeholder(hex_lines: dict[str, dict[str, str]]) -> bool:
    """Return True if hex_lines contain stub placeholder text (needs LLM regeneration)."""
    line1 = hex_lines.get("1")
    if not line1 or not isinstance(line1, dict):
        return True
    daoism = line1.get("daoism", "")
    return "Daoist analysis for Hex" in daoism and "Line 1." in daoism


def _ensure_line_entry(data: dict, line_key: str, hex_id: int) -> dict[str, str]:
    """Ensure line entry has all 6 philosophy keys. Fill missing with placeholder."""
    required = {"daoism", "confucianism", "buddhism", "psychology", "humandesign", "genekeys"}
    entry = data.get(line_key)
    if not isinstance(entry, dict):
        entry = {}
    out: dict[str, str] = {}
    for k in required:
        v = entry.get(k)
        out[k] = str(v).strip() if v else f"Analysis placeholder for Hex {hex_id} Line {line_key} ({k})."
    return out


def generate_hexagram_lines(
    client: OpenAI,
    hex_id: int,
    hex_name: str,
    hex_english: str,
    combined_context: str,
) -> dict[str, dict[str, str]] | None:
    """
    Call LLM for one hexagram. Returns { "1": {...}, "2": {...}, ... "6": {...} } or None on failure.
    """
    user = f"""Hexagram {hex_id}: {hex_name} ({hex_english})

Primary source texts (labeled by tradition):

{combined_context}

Extract Line 1 (bottom) through Line 6 (top) and map to the six lenses. Return ONLY the strict JSON object."""

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            max_tokens=4096,
            temperature=0.2,
            timeout=90.0,
        )
        content = resp.choices[0].message.content
        data = extract_json(content)
        if not isinstance(data, dict):
            return None

        result: dict[str, dict[str, str]] = {}
        for line_key in ("1", "2", "3", "4", "5", "6"):
            result[line_key] = _ensure_line_entry(data, line_key, hex_id)
        return result
    except Exception as e:
        import traceback
        print(f"  ERROR Hex {hex_id}: {e}", flush=True)
        traceback.print_exc()
        return None


def main() -> None:
    _load_env()
    base = get_chunked_base()  # Fail fast if chunked dir missing
    print(f"[start] Chunked base: {base}", flush=True)

    hexagrams = load_hexagrams()
    if not hexagrams:
        raise FileNotFoundError(f"No hexagrams found in {SEED_HEX_PATH}")

    # Filter to valid hexagrams and count processable
    valid = [h for h in hexagrams if 1 <= int(h.get("id", 0)) <= 64]
    total = len(valid)
    print(f"[start] Loaded {total} hexagrams from {SEED_HEX_PATH}", flush=True)

    result: dict[str, dict[str, dict[str, str]]] = {}
    if OUTPUT_PATH.exists():
        result = json.loads(OUTPUT_PATH.read_text())
        if not isinstance(result, dict):
            result = {}
    already = sum(1 for h in valid if str(h.get("id")) in result and len(result.get(str(h.get("id")), {})) >= 6 and not _is_placeholder(result.get(str(h.get("id")), {})))
    print(f"[start] Already present: {already} | To generate: {total - already}", flush=True)
    print("---", flush=True)

    client = get_client()
    idx = 0
    for hex_data in hexagrams:
        hex_id = int(hex_data.get("id", 0))
        if hex_id < 1 or hex_id > 64:
            continue
        idx += 1
        hex_name = hex_data.get("pinyin_name", f"Hexagram {hex_id}")
        hex_english = hex_data.get("english_name", "")

        hex_key = str(hex_id)
        # Skip if already has all 6 lines and not placeholder stub
        if hex_key in result and len(result[hex_key]) >= 6 and not _is_placeholder(result[hex_key]):
            print(f"[{idx}/{total}] Skip Hex {hex_id} (already present)", flush=True)
            continue

        combined_context, sources = load_combined_context(hex_id)
        if not combined_context:
            print(f"[{idx}/{total}] Skip Hex {hex_id} (no source texts found)", flush=True)
            continue

        print(f"[{idx}/{total}] Hex {hex_id} ({hex_name}) | sources: {', '.join(sources)}", flush=True)
        print(f"  -> LLM call...", flush=True)
        lines = generate_hexagram_lines(client, hex_id, hex_name, hex_english, combined_context)
        if lines:
            result[hex_key] = lines
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"  -> Saved Hex {hex_id} (lines 1-6)", flush=True)
        else:
            print(f"  -> FAILED Hex {hex_id} (no output)", flush=True)
        time.sleep(SLEEP_BETWEEN_CALLS)

    print("---", flush=True)
    print(f"[done] Output: {OUTPUT_PATH} | hexagrams in file: {len(result)}", flush=True)


if __name__ == "__main__":
    main()
