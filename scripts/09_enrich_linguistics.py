#!/usr/bin/env python3
"""
Phase 1.9 Task 9: Linguistic Enrichment.
Enrich src/data/seed_herbs.json with aliases and linguistics (tonal_pinyin, jyutping, hokkien)
via DeepSeek API. Resumable: skips herbs that already have linguistics. Incremental save after each call.
"""

import json
import os
import re
import time
from pathlib import Path

from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = PROJECT_ROOT / "src" / "data" / "seed_herbs.json"
SLEEP_BETWEEN_CALLS = 0.5

SYSTEM_PROMPT = """You are an elite Traditional Chinese Medicine linguist and pharmacologist. Analyze the botanical: '{pinyin_name}' / '{common_name}'. Return a raw, parseable JSON object with two keys: 1) aliases (an array of strings: you MUST include the properly spaced classical pinyin if the provided name is squished like 'Guizi' -> 'Gui Zhi', traditional Hanzi characters, and common clinical synonyms), and 2) linguistics (an object containing three string keys: tonal_pinyin [properly spaced with tone marks, e.g., 'Guì Zhī'], jyutping [Cantonese], and hokkien [Taiwanese Pe̍h-ōe-jī])."""


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


def extract_json(text: str) -> dict:
    """Extract JSON object from response, handling markdown code blocks."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


def enrich_herb(client: OpenAI, herb: dict) -> dict | None:
    """Call DeepSeek for one herb. Returns {aliases, linguistics} or None on failure."""
    pinyin = herb.get("pinyin_name", "")
    common = herb.get("common_name", "")
    system = SYSTEM_PROMPT.format(pinyin_name=pinyin, common_name=common)

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": "Return only the JSON object, no other text."},
            ],
            max_tokens=1024,
            temperature=0.1,
            timeout=30.0,
        )
        content = resp.choices[0].message.content
        data = extract_json(content)

        aliases = data.get("aliases")
        linguistics = data.get("linguistics")

        if aliases is None:
            aliases = []
        if linguistics is None:
            linguistics = {}

        return {
            "aliases": aliases if isinstance(aliases, list) else [str(aliases)] if aliases else [],
            "linguistics": {
                "tonal_pinyin": str(linguistics.get("tonal_pinyin", "")).strip() or None,
                "jyutping": str(linguistics.get("jyutping", "")).strip() or None,
                "hokkien": str(linguistics.get("hokkien", "")).strip() or None,
            }
            if isinstance(linguistics, dict)
            else {},
        }
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"  Skip ({herb.get('pinyin_name', '?')}): {e}")
        return None


def save_herbs(herbs: list[dict]) -> None:
    with open(SEED_PATH, "w", encoding="utf-8") as f:
        json.dump(herbs, f, indent=2, ensure_ascii=False)


def main() -> int:
    _load_env()

    if not SEED_PATH.exists():
        print(f"Error: {SEED_PATH} not found")
        return 1

    with open(SEED_PATH, encoding="utf-8") as f:
        herbs = json.load(f)

    # Resumable: skip herbs that already have linguistics
    pending = [i for i, h in enumerate(herbs) if "linguistics" not in h or not h.get("linguistics")]
    if not pending:
        print("All herbs already enriched.")
        return 0

    client = get_client()
    total = len(herbs)
    num_pending = len(pending)
    print(f"Enriching {num_pending} / {total} herbs (skipping {total - num_pending} already done)\n")

    for queue_pos, idx in enumerate(pending, start=1):
        herb = herbs[idx]
        pinyin = herb.get("pinyin_name", "?")
        print(f"[{queue_pos}/{num_pending}] {pinyin} ... ", end="", flush=True)
        result = enrich_herb(client, herb)
        if result:
            herb["aliases"] = result["aliases"]
            herb["linguistics"] = {k: v for k, v in result["linguistics"].items() if v}
            save_herbs(herbs)
            print("Enriched", flush=True)
        else:
            print("Skipped", flush=True)
        time.sleep(SLEEP_BETWEEN_CALLS)

    enriched = sum(1 for h in herbs if h.get("linguistics"))
    print(f"\nDone. {enriched} / {total} herbs enriched.")

    return 0


if __name__ == "__main__":
    exit(main())
