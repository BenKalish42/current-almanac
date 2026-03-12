#!/usr/bin/env python3
"""
Phase 6.2: Linguistic Enrichment.
Enrich herb data with precise linguistics via DeepSeek API.
"""

import json
import os
import re
import time
from pathlib import Path

from openai import OpenAI
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "output" / "seed_herbs.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "output" / "enriched_herbs.json"
BATCH_SIZE = 40
MAX_RETRIES = 5
RETRY_SLEEP = 5

SYSTEM_PROMPT = """You are a master TCM linguist. I am giving you a JSON array of herbs. You must return a strict JSON object where the keys are the herb IDs, and the values are objects containing exactly these 5 keys:
- name_pinyin_display (lowercase, with exact pinyin tones, e.g., 'guī zhī')
- name_pinyin_search (lowercase, spaces, no tones, e.g., 'gui zhi')
- name_pinyin_slug (lowercase, no spaces, no tones, e.g., 'guizhi')
- name_hanzi_simplified (e.g., '桂枝')
- name_hanzi_traditional (e.g., '桂枝')
Ensure your response is parseable JSON."""


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise ValueError(
            "Set DEEPSEEK_API_KEY or OPENAI_API_KEY. Get a key at https://platform.deepseek.com/api_keys"
        )
    return OpenAI(api_key=api_key, base_url=base_url)


def extract_json(text: str) -> dict:
    """Extract JSON object from response, handling markdown code blocks."""
    text = text.strip()
    # Remove markdown code block if present
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


def call_deepseek(client: OpenAI, batch: list[dict]) -> dict:
    """Call DeepSeek with retries on 429/502. 90s timeout to avoid freezing."""
    payload = [
        {"id": h["id"], "pinyin_name": h["pinyin_name"], "english_name": h.get("english_name", "")}
        for h in batch
    ]
    user_msg = json.dumps(payload, ensure_ascii=False)

    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=4096,
                temperature=0.1,
                timeout=90.0,
            )
            content = resp.choices[0].message.content
            return extract_json(content)
        except Exception as e:
            code = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
            if code in (429, 502) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_SLEEP)
                continue
            raise


def _load_env() -> None:
    """Load .env from backend/ if present."""
    env_path = PROJECT_ROOT / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k.strip(), v)


def main() -> int:
    _load_env()
    if not INPUT_PATH.exists():
        print(f"Error: {INPUT_PATH} not found")
        return 1

    with open(INPUT_PATH, encoding="utf-8") as f:
        herbs = json.load(f)

    # Resume: load existing enriched data if present
    if OUTPUT_PATH.exists():
        try:
            with open(OUTPUT_PATH, encoding="utf-8") as f:
                existing = json.load(f)
            if len(existing) == len(herbs):
                by_id = {h["id"]: h for h in existing}
                for h in herbs:
                    if h["id"] in by_id:
                        for key in ("name_pinyin_display", "name_pinyin_search", "name_pinyin_slug", "name_hanzi_simplified", "name_hanzi_traditional"):
                            if key in by_id[h["id"]]:
                                h[key] = by_id[h["id"]][key]
        except (json.JSONDecodeError, KeyError):
            pass

    pending = [i for i, h in enumerate(herbs) if "name_pinyin_display" not in h]
    if not pending:
        print("All herbs already enriched.")
        total = len(herbs)
        pct = 100.0 * sum(1 for h in herbs if "name_pinyin_display" in h) / total if total else 0
        print(f"  Herbs enriched: {sum(1 for h in herbs if 'name_pinyin_display' in h)} / {total} ({pct:.1f}%)")
        return 0

    client = get_client()
    total = len(herbs)

    for start in tqdm(range(0, len(pending), BATCH_SIZE), desc="Enriching batches"):
        indices = pending[start : start + BATCH_SIZE]
        batch = [herbs[i] for i in indices]
        result = call_deepseek(client, batch)

        for h in batch:
            hid = h["id"]
            if hid in result:
                obj = result[hid]
                for key in (
                    "name_pinyin_display",
                    "name_pinyin_search",
                    "name_pinyin_slug",
                    "name_hanzi_simplified",
                    "name_hanzi_traditional",
                ):
                    if key in obj and obj[key] is not None:
                        h[key] = str(obj[key]).strip()

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(herbs, f, indent=2, ensure_ascii=False)

    all_enriched = all(
        "name_pinyin_display" in h and "name_hanzi_simplified" in h
        for h in herbs
    )
    pct = 100.0 * sum(1 for h in herbs if "name_pinyin_display" in h) / total if total else 0

    print()
    print("=" * 60)
    print("Phase 6.2: Linguistic Enrichment — COMPLETE")
    print("=" * 60)
    print(f"  Output: {OUTPUT_PATH}")
    print(f"  Herbs enriched: {sum(1 for h in herbs if 'name_pinyin_display' in h)} / {total}")
    print(f"  Coverage: {pct:.1f}%")
    print(f"  Status: {'100% enriched' if all_enriched else 'Partial (some herbs missing fields)'}")
    print()
    print("Open data/output/enriched_herbs.json to view the enriched data.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
