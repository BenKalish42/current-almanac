#!/usr/bin/env python3
"""
Phase 4: Classical Formula Extractor.
Reads scraped Shanghan Lun text, uses DeepSeek to extract formula architectures
in targeted batches. Idempotent: appends to existing seed_formulas.json.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

from openai import OpenAI

# All 113 Shanghan Lun formulas (Pinyin) - from formula names in the text
target_formulas = [
    "Gui Zhi Tang", "Gui Zhi Jia Ge Gen Tang", "Gui Zhi Jia Fu Zi Tang", "Gui Zhi Qu Shao Yao Tang",
    "Gui Zhi Qu Shao Yao Jia Fu Zi Tang", "Gui Zhi Jia Hou Pu Xing Ren Tang",
    "Gui Zhi Jia Shao Yao Sheng Jiang Ren Shen Xin Jia Tang", "Gui Zhi Qu Gui Jia Fu Ling Bai Zhu Tang",
    "Gui Zhi Er Yue Bi Yi Tang", "Gui Zhi Ma Huang Ge Ban Tang", "Gui Zhi Er Ma Huang Yi Tang",
    "Gui Zhi Jia Gui Tang", "Gui Zhi Gan Cao Tang", "Gui Zhi Gan Cao Long Gu Mu Li Tang",
    "Gui Zhi Qu Shao Yao Jia Shu Qi Long Gu Mu Li Jiu Ni Tang", "Gan Cao Gan Jiang Tang",
    "Shao Yao Gan Cao Tang", "Tiao Wei Cheng Qi Tang", "Si Ni Tang", "Ge Gen Tang",
    "Ge Gen Jia Ban Xia Tang", "Ge Gen Huang Qin Huang Lian Tang", "Ma Huang Tang",
    "Da Qing Long Tang", "Xiao Qing Long Tang", "Ma Huang Xing Ren Gan Cao Shi Gao Tang",
    "Gan Jiang Fu Zi Tang", "Fu Ling Gui Zhi Gan Cao Da Zao Tang",
    "Hou Pu Sheng Jiang Gan Cao Ban Xia Ren Shen Tang", "Fu Ling Gui Zhi Bai Zhu Gan Cao Tang",
    "Shao Yao Gan Cao Fu Zi Tang", "Fu Ling Si Ni Tang", "Wu Ling San", "Fu Ling Gan Cao Tang",
    "Zhi Zi Chi Tang", "Zhi Zi Gan Cao Chi Tang", "Zhi Zi Sheng Jiang Chi Tang", "Zhi Zi Hou Pu Tang",
    "Zhi Zi Gan Jiang Tang", "Xiao Chai Hu Tang", "Xiao Jian Zhong Tang", "Da Chai Hu Tang",
    "Chai Hu Jia Mang Xiao Tang", "Tao He Cheng Qi Tang", "Chai Hu Jia Long Gu Mu Li Tang",
    "Di Dang Tang", "Di Dang Wan", "Da Xian Xiong Wan", "Da Xian Xiong Tang", "Xiao Xian Xiong Tang",
    "Wen Ge San", "Chai Hu Gui Zhi Gan Jiang Tang", "Ban Xia Xie Xin Tang", "Shi Zao Tang",
    "Da Huang Huang Lian Xie Xin Tang", "Fu Zi Xie Xin Tang", "Chi Shi Zhi Yu Yu Liang Tang",
    "Xuan Fu Dai Zhe Shi Tang", "Gui Zhi Ren Shen Tang", "Gua Di San", "Huang Qin Tang", "Huang Lian Tang",
    "Gui Zhi Fu Zi Tang", "Gan Cao Fu Zi Tang", "Bai Hu Tang", "Bai Hu Jia Ren Shen Tang",
    "Zhi Gan Cao Tang", "Da Cheng Qi Tang", "Xiao Cheng Qi Tang", "Zhu Ling Tang",
    "Yin Chen Hao Tang", "Wu Zhu Yu Tang", "Ma Ren Wan", "Zhi Zi Bai Pi Tang",
    "Ma Huang Lian Qiao Chi Xiao Dou Tang", "Ma Huang Fu Zi Xi Xin Tang", "Ma Huang Fu Zi Gan Cao Tang",
    "Huang Lian E Jiao Tang", "Fu Zi Tang", "Tao Hua Tang", "Zhu Fu Tang", "Gan Cao Tang",
    "Jie Geng Tang", "Ku Jiu Tang", "Ban Xia San Ji Tang", "Bai Tong Tang",
    "Bai Tong Jia Zhu Dan Zhi Tang", "Zhen Wu Tang", "Tong Mai Si Ni Tang", "Si Ni San",
    "Dang Gui Si Ni Tang", "Ma Huang Sheng Ma Tang", "Gan Jiang Huang Lian Huang Qin Ren Shen Tang",
    "Bai Tou Weng Tang", "Li Zhong Wan", "Li Zhong Tang", "Shao Kun San", "Zhi Shi Zhi Zi Chi Tang",
    "Mu Li Ze Xie San", "Zhu Ye Shi Gao Tang", "Chai Hu Gui Zhi Tang",
]

BATCH_SIZE = 5
BATCH_DELAY_SEC = 5

RULES = """Rules:
- Read the Chinese text to find the exact classical dosages (e.g., "3 liang", "12 pieces", "half a sheng"). DO NOT invent or convert dosages to metric. Preserve the ancient weights.
- Assign the classical architectural roles to the herbs: "King", "Minister", "Assistant", or "Envoy".
- Use standard Pinyin for the herb names so they can be matched against a modern database later.
- Output ONLY raw, parsable JSON. No markdown blocks, no code fences, no explanatory text.
- Return a JSON object with a "formulas" key containing an array of formula objects."""

SCHEMA_HINT = """Each formula object must have:
- id: e.g. "form_shl_011"
- pinyin_name: e.g. "Ge Gen Tang"
- english_name: e.g. "Kudzu Decoction"
- primary_pattern: e.g. "Taiyang with Stiff Neck"
- actions: array of action strings
- architecture: array of {herb_pinyin, role, classical_dosage}"""


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


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def main() -> int:
    load_backend_env()
    root = project_root()
    raw_path = root / "data" / "raw" / "10_tcm_shl_chinese.txt"
    output_path = root / "data" / "output" / "seed_formulas.json"

    if not raw_path.exists():
        print(f"Error: {raw_path} not found. Run 04_scrape_ctext.py first.", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable not set.", file=sys.stderr)
        return 1

    text = raw_path.read_text(encoding="utf-8")
    if len(text) < 1000:
        print("Error: Shanghan Lun text appears too short.", file=sys.stderr)
        return 1

    text_to_send = text
    if len(text) > 100_000:
        text_to_send = text[:100_000] + "\n\n[... text truncated ...]"
        print(f"Truncating text to 100,000 chars for API", file=sys.stderr)

    print(f"Loaded {len(text):,} chars from {raw_path}", file=sys.stderr)
    print(f"Extracting {len(target_formulas)} formulas in batches of {BATCH_SIZE}", file=sys.stderr)

    # Idempotent: load existing formulas if present, deduplicate by pinyin_name
    master_list = []
    if output_path.exists():
        try:
            raw = json.loads(output_path.read_text(encoding="utf-8"))
            master_list = raw if isinstance(raw, list) else [raw]
            seen = set()
            deduped = []
            for f in master_list:
                name = f.get("pinyin_name") if isinstance(f, dict) else None
                if name and name not in seen:
                    seen.add(name)
                    deduped.append(f)
            master_list = deduped
            print(f"Loaded {len(master_list)} existing formulas from {output_path}", file=sys.stderr)
        except json.JSONDecodeError:
            pass

    existing_names = {f.get("pinyin_name") for f in master_list if isinstance(f, dict) and f.get("pinyin_name")}
    formulas_to_extract = [f for f in target_formulas if f not in existing_names]
    if not formulas_to_extract:
        print("All formulas already extracted. Nothing to do.", file=sys.stderr)
        return 0
    print(f"Skipping {len(existing_names)} already extracted. {len(formulas_to_extract)} remaining.", file=sys.stderr)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    batches = list(chunks(formulas_to_extract, BATCH_SIZE))
    total_batches = len(batches)

    for batch_idx, batch in enumerate(batches):
        batch_num = batch_idx + 1
        print(f"\nBatch {batch_num}/{total_batches}: {', '.join(batch)}", file=sys.stderr)

        system_content = (
            f"You are 'Zhuang', the Chief Alchemist. Read the provided Shanghan Lun text. "
            f"Extract ONLY the following formulas: {batch}. Output them as a strict JSON object with a 'formulas' key.\n\n"
            f"{RULES}\n\n{SCHEMA_HINT}"
        )

        user_content = f"Here is the Shanghan Lun text:\n\n---\n{text_to_send}\n---"

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
        except Exception as e:
            if "response_format" in str(e).lower() or "json_object" in str(e).lower():
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_content + "\n\nOutput ONLY valid JSON. No markdown."},
                        {"role": "user", "content": user_content},
                    ],
                )
            else:
                raise

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```\s*$", "", content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parse error in batch {batch_num}: {e}", file=sys.stderr)
            print("Raw (first 500 chars):", content[:500], file=sys.stderr)
            return 1

        if isinstance(data, dict) and "formulas" in data:
            batch_formulas = data["formulas"]
        elif isinstance(data, list):
            batch_formulas = data
        else:
            batch_formulas = [data]

        if not isinstance(batch_formulas, list):
            batch_formulas = [batch_formulas]

        master_list.extend(batch_formulas)
        output_path.write_text(
            json.dumps(master_list, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  -> Extracted {len(batch_formulas)} formulas. Total: {len(master_list)}. Saved.", file=sys.stderr)

        if batch_idx < total_batches - 1:
            print(f"  -> Sleeping {BATCH_DELAY_SEC}s before next batch...", file=sys.stderr)
            time.sleep(BATCH_DELAY_SEC)

    print(f"\nBatch {total_batches}/{total_batches} complete.", file=sys.stderr)
    print(f"Saved {len(master_list)} formulas to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
