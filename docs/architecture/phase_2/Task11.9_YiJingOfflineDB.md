# Task 11.9 - Yi Jing Offline DB & Lazy Loading

## Scope

Introduces an offline JSON database of Yi Jing line-by-line analyses (64 hexagrams × 6 lines × 6 philosophies) and lazy-loads them into `HexagramModal` when the exploded view or line click is used.

## Architecture

### Data Pipeline

- **Generator**: `scripts/11_generate_yijing_lines.py`
- **Input**: Primary source texts from `data/chunked/` (or `src/data/chunked/`)
- **Output**: `src/data/yiJingLines.json` — resumable, incremental save after each hexagram
- **LLM**: DeepSeek (or OpenAI via env override)

### Chunked Source Traversal (11.9c)

The generator discovers primary source texts by **dynamic traversal** of the chunked directory:

1. **Candidate paths** (first existing wins):
   - `{PROJECT_ROOT}/data/chunked`
   - `{PROJECT_ROOT}/src/data/chunked`

2. **Subfolder discovery**: For each hexagram ID 1–64, the script iterates over all subdirectories under the chunked base.

3. **File naming**: Each subfolder may contain `hex_{id:02d}.txt` (e.g. `hex_01.txt`, `hex_47.txt`).

4. **Stitching**: For each hexagram:
   - Collect all `hex_{id:02d}.txt` files from every subfolder
   - Build `combined_context` with headers: `--- SOURCE: {folder_name} ---\n{content}`
   - Folder names (e.g. `daoist_1_cleary`, `confucian_2_legge`) label the tradition/source

5. **One LLM call per hexagram**: The combined context is sent to the LLM. Expected JSON schema:
   ```json
   {
     "1": { "daoism": "...", "confucianism": "...", "buddhism": "...", "psychology": "...", "humandesign": "...", "genekeys": "..." },
     "2": { ... },
     ...
     "6": { ... }
   }
   ```
   Keys `"1"`–`"6"` are line numbers (1 = bottom, 6 = top).

6. **Resumable**: Hexagrams already present in `yiJingLines.json` are skipped (unless placeholder stub detected).

### Output Schema

```ts
// From src/data/schema_yijing.ts
{
  [hexagramId: string]: {
    [lineNumber: string]: {
      daoism: string;
      confucianism: string;
      buddhism: string;
      psychology: string;
      humandesign: string;
      genekeys: string;
    };
  };
}
```

### Frontend Integration

- **HexagramModal.vue**:
  - `lineData` ref, loaded via dynamic `import('@/data/yiJingLines.json')` when `isExploded` becomes true or user clicks a line
  - `activeLineText` computed from `lineData?.[hexNum]?.[activeLine]?.[activePhilosophy]`
  - Placeholder shown when data is missing

## Files

- `scripts/11_generate_yijing_lines.py` — LLM generator with chunked traversal
- `src/data/yiJingLines.json` — output (full 64 hexagrams)
- `src/data/schema_yijing.ts` — `YaoLineAnalysis` type
- `src/components/HexagramModal.vue` — lazy loader + UI

## Environment

Set `DEEPSEEK_API_KEY` or `OPENAI_API_KEY` in `.env`. Optional: `DEEPSEEK_BASE_URL` for custom endpoint.

---

## Data Audit & Fixes (2026-03)

### Issues Found

1. **Hex 1 and 2**: Contained stub placeholder text (`"Daoist analysis for Hex X Line Y."`) instead of LLM-generated content.
2. **Hex 64**: Missing entirely — not in `seed_hexagrams.json`, so the generator never processed it.
3. **Hex 64 context overflow**: On first run, hex 64 sources exceeded model context limit (137k tokens).

### Fixes Applied

1. **Hex 64 in `seed_hexagrams.json`** — Added entry for Wèi Jì / Before Completion with full perspectives (daoist, confucian, buddhist, psychological, human_design, gene_keys).

2. **Placeholder detection** — Added `_is_placeholder(hex_lines)` to detect stub text. Hexagrams with placeholder data are regenerated instead of skipped. Skip logic: `len(result[hex_key]) >= 6 and not _is_placeholder(result[hex_key])`.

3. **Context truncation** — `MAX_CHARS_PER_SOURCE = 25_000`. Each source file truncated to 25k chars with `[... truncated for context limit ...]` appended when over limit. Prevents 400 errors on long hexagrams (e.g. 64).

4. **Progress output** — Startup summary, per-hex sources, `[idx/total]` progress, `-> LLM call...` / `-> Saved` / `-> FAILED`, and error tracebacks on failure.

### Result

- All 64 hexagrams now have LLM-generated line analyses.
- No remaining placeholder or `"Analysis placeholder"` patterns in `yiJingLines.json`.
- Script is resumable and regenerates placeholder data on subsequent runs.
