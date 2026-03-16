# Task 9: Linguistic Enrichment (AI)

**Phase:** 1.9 — Linguistic Architecture  
**Task:** 9

---

## 1. Files Created / Modified

| Action | Path |
|--------|------|
| Modified | `scripts/09_enrich_linguistics.py` — rewritten for frontend schema |
| Modified | `src/data/seed_herbs.json` — updated by script when run (aliases, linguistics injected) |
| Created | `docs/architecture/phase_1/Task9_LinguisticEnrichment.md` |

---

## 2. LLM Prompt Logic

**System + user prompt (per herb):**

> You are an elite Traditional Chinese Medicine linguist and pharmacologist. Analyze the botanical: '{pinyin_name}' / '{common_name}'. Return a raw, parseable JSON object with two keys: 1) **aliases** (an array of strings: you MUST include the properly spaced classical pinyin if the provided name is squished like 'Guizi' -> 'Gui Zhi', traditional Hanzi characters, and common clinical synonyms), and 2) **linguistics** (an object containing three string keys: **tonal_pinyin** [properly spaced with tone marks, e.g., 'Guì Zhī'], **jyutping** [Cantonese], and **hokkien** [Taiwanese Pe̍h-ōe-jī]).

**Expected response shape:** `{ "aliases": ["Gui Zhi", "桂枝", ...], "linguistics": { "tonal_pinyin": "Guì Zhī", "jyutping": "gwai3 zi1", "hokkien": "Kùi-ki" } }`

---

## 3. One-Sentence Summary for AI CTO

A Python script uses the DeepSeek API to enrich each herb in `src/data/seed_herbs.json` with `aliases` and `linguistics` (tonal pinyin, Cantonese jyutping, Taiwanese hokkien), saves incrementally after each successful call, and skips herbs that already have linguistics so the run is resumable.

---

## 4. Core Logic / Mechanics

- **API:** OpenAI client with `base_url=https://api.deepseek.com`, `DEEPSEEK_API_KEY` from `.env` (project root or `backend/.env`)
- **Resumability:** If an herb already has the `linguistics` key, skip it
- **Incremental save:** After every successful API call, write the full herb array back to `src/data/seed_herbs.json`
- **Resilience:** `try/except` around each call; `time.sleep(0.5)` between calls for rate limits; JSON parse errors logged and herb skipped
- **Console output:** `Enriched: {pinyin_name}` on success
- **Single-herb processing:** One API call per herb (no batching)

---

## 5. Usage

```bash
# Set DEEPSEEK_API_KEY in .env or backend/.env first
python3.12 scripts/09_enrich_linguistics.py
# Or, if default Python has SSL issues:
./scripts/run_enrich_linguistics.sh
```
