# Hexagram Summaries Offline Pipeline

Goal: generate `src/data/hexagramSummaries.json` with 64 hexagrams × 5 traditions, 4 sentences each.

## Inputs
- One plaintext file per tradition, with clear chapter markers for each hexagram.
- Recommended markers: `Hexagram 1`, `Hexagram 2`, ... `Hexagram 64` on their own lines.
- Traditions: Daoist, Buddhist, Confucian, HumanDesign, GeneKeys.

## Steps
1. Normalize sources into plain text files with consistent `Hexagram N` markers.
2. Parse each file into 64 chunks keyed by hexagram number.
3. For each hexagram, summarize each tradition chunk into ~4 sentences.
4. Assemble the results into a single JSON object keyed by hexagram number.
5. Manual review pass to ensure tone consistency and avoid copying phrasing verbatim.

## Output Shape (JSON)
```
{
  "1": {
    "daoist": "...",
    "buddhist": "...",
    "confucian": "...",
    "humanDesign": "...",
    "geneKeys": "..."
  },
  "2": {
    "daoist": "...",
    "buddhist": "...",
    "confucian": "...",
    "humanDesign": "...",
    "geneKeys": "..."
  }
}
```

## Suggested Script Structure (local)
- Load five files into memory.
- `split_by_hexagram(text)` using the `Hexagram N` markers.
- `summarize(chunk, tradition)` using your preferred model and prompt.
- Write JSON to `src/data/hexagramSummaries.json`.

## Run (inside repo)
```
python scripts/hexagram_summaries_pipeline.py \
  --daoist /ABS/PATH/daoist.txt \
  --buddhist /ABS/PATH/buddhist.txt \
  --confucian /ABS/PATH/confucian.txt \
  --human-design /ABS/PATH/human_design.txt \
  --gene-keys /ABS/PATH/gene_keys.txt \
  --summarize \
  --out src/data/hexagramSummaries.json
```

## Optional
- Use `--chunks-out /ABS/PATH/chunks.json` to inspect parsing.
- Use `--limit 3` to test a small subset.
- Remove `--summarize` to generate an empty template JSON.

## Notes
- Keep each tradition summary distinct in tone to highlight its lens.
- Avoid copying any official text verbatim; paraphrase consistently.
