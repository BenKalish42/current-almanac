#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
import urllib.request

HEX_MARKER = re.compile(r"^\s*Hexagram\s+(\d{1,2})\s*[:\-–—]?\s*$", re.MULTILINE)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n").replace("\r", "\n")


def split_by_hexagram(text: str) -> dict[int, str]:
    matches = list(HEX_MARKER.finditer(text))
    if not matches:
        raise ValueError("No hexagram markers found. Expected lines like 'Hexagram 1'.")
    out: dict[int, str] = {}
    for i, match in enumerate(matches):
        num = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        out[num] = chunk
    return out


def build_prompt(tradition: str, chunk: str, sentences: int) -> str:
    return (
        f"Summarize the following I Ching hexagram chapter from the {tradition} tradition.\n"
        f"Write about {sentences} sentences. Paraphrase, avoid quoting or copying original phrasing.\n"
        "Use clear modern language while preserving the tradition's lens.\n\n"
        f"CHAPTER:\n{chunk}\n"
    )


def openai_summarize(prompt: str, api_key: str, base_url: str, model: str) -> str:
    payload = {
        "model": model,
        "temperature": 0.4,
        "max_tokens": 320,
        "messages": [
            {"role": "system", "content": "You are a careful summarizer. Respond with plain text only."},
            {"role": "user", "content": prompt},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
    parsed = json.loads(raw.decode("utf-8"))
    return parsed["choices"][0]["message"]["content"].strip()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build hexagram summaries JSON from 5 tradition source texts."
    )
    p.add_argument("--daoist", required=True, help="Path to Daoist source text.")
    p.add_argument("--buddhist", required=True, help="Path to Buddhist source text.")
    p.add_argument("--confucian", required=True, help="Path to Confucian source text.")
    p.add_argument("--human-design", required=True, help="Path to Human Design source text.")
    p.add_argument("--gene-keys", required=True, help="Path to Gene Keys source text.")
    p.add_argument("--out", default="src/data/hexagramSummaries.json", help="Output JSON path.")
    p.add_argument("--chunks-out", help="Optional path to dump chunked sources for review.")
    p.add_argument("--summarize", action="store_true", help="Generate summaries via OpenAI API.")
    p.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    p.add_argument("--sentences", type=int, default=4)
    p.add_argument("--limit", type=int, default=0, help="Limit to first N hexagrams for testing.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    sources = {
        "daoist": read_text(args.daoist),
        "buddhist": read_text(args.buddhist),
        "confucian": read_text(args.confucian),
        "humanDesign": read_text(args.human_design),
        "geneKeys": read_text(args.gene_keys),
    }

    chunks: dict[str, dict[int, str]] = {k: split_by_hexagram(v) for k, v in sources.items()}

    missing = {k: sorted(set(range(1, 65)) - set(v.keys())) for k, v in chunks.items()}
    missing_any = {k: v for k, v in missing.items() if v}
    if missing_any:
        raise ValueError(f"Missing hexagrams in sources: {missing_any}")

    if args.chunks_out:
        with open(args.chunks_out, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=True)

    data: dict[str, dict[str, str]] = {}

    if args.summarize:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when --summarize is set.")
        base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")

    for num in range(1, 65):
        if args.limit and num > args.limit:
            break
        entry: dict[str, str] = {}
        for tradition, chunk_map in chunks.items():
            if not args.summarize:
                entry[tradition] = ""
                continue
            prompt = build_prompt(tradition, chunk_map[num], args.sentences)
            entry[tradition] = openai_summarize(prompt, api_key, base_url, args.model)
            time.sleep(0.35)
        data[str(num)] = entry

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
