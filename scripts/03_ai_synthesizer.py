#!/usr/bin/env python3
"""
Phase 3 ETL: AI Synthesizer.
Reads chunked hexagram texts from 7 traditions, sends to DeepSeek API,
synthesizes into structured JSON, and writes data/output/seed_hexagrams.json.

With --deploy: after all 64 hexagrams, runs deploy script (git push → Netlify).
Without: when done, run ./scripts/deploy_to_benkalish.sh and press Enter to publish.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from openai import OpenAI

# --- 7 successful chunked folders (Daoist 2 excluded) ---
CHUNKED_FOLDERS = [
    "daoist_1_cleary",
    "confucian_1_cleary",
    "confucian_2_legge",
    "buddhist_1_cleary",
    "human_design_1_ra",
    "gene_keys_1_rudd",
    "psychological_1_wilhelm",
]

# --- Tradition → folder mapping for prompt labels ---
TRADITION_LABELS = {
    "daoist_1_cleary": "Daoist (Liu Yiming)",
    "confucian_1_cleary": "Confucian (Cleary)",
    "confucian_2_legge": "Confucian (Legge)",
    "buddhist_1_cleary": "Buddhist (Ou-i)",
    "human_design_1_ra": "Human Design (Ra Uru Hu)",
    "gene_keys_1_rudd": "Gene Keys (Richard Rudd)",
    "psychological_1_wilhelm": "Psychological (Wilhelm)",
}


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_backend_env() -> None:
    """Load backend/.env so DEEPSEEK_API_KEY is available (same as backend)."""
    env_path = project_root() / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key.strip(), val)


def gather_hex_texts(chunked_base: Path, i: int) -> dict[str, str]:
    """Read hex_{i:02d}.txt from each folder. Missing files → empty string."""
    texts: dict[str, str] = {}
    for folder in CHUNKED_FOLDERS:
        path = chunked_base / folder / f"hex_{i:02d}.txt"
        try:
            texts[folder] = path.read_text(encoding="utf-8", errors="replace").strip()
        except FileNotFoundError:
            texts[folder] = ""
    return texts


def build_user_prompt(texts: dict[str, str]) -> str:
    """Build user prompt with labeled source texts."""
    parts = []
    for folder, text in texts.items():
        label = TRADITION_LABELS[folder]
        if text:
            parts.append(f"--- {label} ---\n{text}")
        else:
            parts.append(f"--- {label} ---\n[No text available]")
    return "\n\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI synthesizer for 64 hexagrams")
    parser.add_argument("--deploy", action="store_true", help="After completing 64 hexagrams, deploy to benkalish.com (git push)")
    args = parser.parse_args()

    root = project_root()
    chunked_base = root / "data" / "chunked"
    output_dir = root / "data" / "output"
    output_path = output_dir / "seed_hexagrams.json"

    output_dir.mkdir(parents=True, exist_ok=True)

    load_backend_env()
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY or OPENAI_API_KEY not set. Add to backend/.env", file=sys.stderr)
        return 1

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    master_list: list[dict] = []

    for i in range(1, 65):
        print(f"Processing Hexagram {i}...", file=sys.stderr)

        texts = gather_hex_texts(chunked_base, i)
        user_content = build_user_prompt(texts)

        system_prompt = f"""You are 'Zhuang', the Chief Architect and Scribe for a Daoist app. Your task is to read the provided source texts for Hexagram {i} and synthesize them into 6 distinct summaries. Apply your own deep knowledge of these traditions to fill in any gaps.

Rules:
- Daoist: Synthesize the Liu Yiming text (Internal Alchemy). (Max 4 sentences)
- Confucian: Synthesize the Legge and Cleary Confucian texts. (Max 4 sentences)
- Buddhist: Synthesize the Ou-i text (Mind-training/Emptiness). (Max 4 sentences)
- Psychological: Synthesize the Wilhelm text (Jungian archetypes). (Max 4 sentences)
- Human Design (IP SAFE): Extract bio-energetic mechanics from the Ra Uru Hu text. DO NOT use trademarked jargon. (Max 4 sentences)
- Gene Keys (IP SAFE): Extract trinary frequency from the Rudd text. DO NOT use the words "Shadow, Gift, Siddhi". Label them strictly as "Contracted State", "Harmonized State", and "Luminous State". (Max 4 sentences)

Output ONLY raw, parsable JSON. No markdown blocks.

JSON Schema Requirement:
{{
  "id": {i},
  "pinyin_name": "...",
  "english_name": "...",
  "perspectives": {{
    "daoist": "...",
    "confucian": "...",
    "buddhist": "...",
    "psychological": "...",
    "human_design": "...",
    "gene_keys": "..."
  }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            print(f"ERROR: API call failed for Hexagram {i}: {e}", file=sys.stderr)
            return 1

        content = response.choices[0].message.content
        if not content:
            print(f"ERROR: Empty response for Hexagram {i}", file=sys.stderr)
            return 1

        # Strip markdown code blocks if present
        raw = content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines)

        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON for Hexagram {i}: {e}", file=sys.stderr)
            print(f"Raw content: {raw[:500]}...", file=sys.stderr)
            return 1

        # Ensure id matches
        obj["id"] = i
        master_list.append(obj)

        output_path.write_text(
            json.dumps(master_list, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"  Saved ({len(master_list)} hexagrams so far)", file=sys.stderr)

        if i < 64:
            time.sleep(2)

    print(f"\nDone. Wrote {output_path} with {len(master_list)} hexagrams.", file=sys.stderr)

    if args.deploy:
        deploy_script = root / "scripts" / "deploy_to_benkalish.sh"
        if deploy_script.exists():
            print("Deploying to benkalish.com (git push)...", file=sys.stderr)
            # Run deploy script; use echo to auto-press Enter for non-interactive
            result = subprocess.run(
                ["bash", str(deploy_script)],
                cwd=str(root),
                input=b"\n",
                timeout=60,
            )
            if result.returncode != 0:
                print(f"Deploy script exited with {result.returncode}", file=sys.stderr)
                return result.returncode
        else:
            print("Deploy script not found. Run ./scripts/deploy_to_benkalish.sh manually.", file=sys.stderr)
    else:
        print("To publish: ./scripts/deploy_to_benkalish.sh  (then press Enter)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
