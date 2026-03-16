# Daoist Datasets & Neo4j Migration — Status Report

**Date:** March 11, 2026  
**Auditor:** Lead Data Engineer  
**Audience:** AI CTO  
**Scope:** `data/`, `scripts/`, `backend/` — scraped Big 4 datasets and Neo4j integration

---

## Executive Summary

The Big 4 raw scrapes (Shennong Bencao Jing, Huangdi Neijing, Shanghan Lun, SymMap) are present in `data/raw/`. A Neo4j ingestion script exists and runs correctly. The frontend uses a small hand-curated `src/data/seed_herbs.json` (~18 herbs) instead of the full SymMap-derived dataset (~500 herbs) because **no pipeline step copies or transforms** `data/output/seed_herbs.json` into `src/data/`. There is no Neo4j→JSON export for offline/mobile use.

---

## 1. Raw Scrapes (Big 4)

**Location:** `data/raw/` (not `data/output/`)

| Dataset | File(s) | Format | Source Script |
|---------|---------|--------|---------------|
| **Shennong Bencao Jing** | `09_tcm_snbcj_chinese.txt`, `12_tcm_snbcj_chinese.txt` | TXT | `04_scrape_ctext.py`, `06_scrape_snbcj_hdnj.py` |
| **Huangdi Neijing** | `13_tcm_hdnj_chinese.txt` | TXT | `06_scrape_snbcj_hdnj.py`, `08_scrape_wikisource.py` |
| **Shanghan Lun** | `10_tcm_shl_chinese.txt` | TXT | `04_scrape_ctext.py` |
| **SymMap (modern pharmacology)** | `SymMap v2.0, SMHB file.xlsx`, `SymMap v2.0, SMHB file.csv` | XLSX / CSV | Manual download (not scraped) |

All classical TCM texts are plain TXT. SymMap is structured XLSX/CSV. No raw scrapes live in `data/output/`; that directory holds processed JSON only.

---

## 2. Graph Migration (Neo4j)

**Script:** `scripts/08_build_graph.py`

- **Inputs:** `data/output/seed_herbs.json`, `data/output/seed_formulas.json`
- **Target:** Neo4j at `bolt://localhost:7687` (via `docker-compose up -d`)
- **Nodes:** Herb, Formula, Meridian
- **Relationships:** Herb→Meridian (ENTERS), Herb→Formula (INCLUDED_IN)

The script exists, runs, and ingests correctly. No other Python scripts in `scripts/` or `backend/` push data into Neo4j.

---

## 3. The Disconnect (Why `src/data/seed_herbs.json` ≠ Full Database)

### Schema Mismatch

| File | Size | Count | Schema |
|------|------|-------|--------|
| `data/output/seed_herbs.json` | ~239 KB | ~500+ herbs | SymMap-style: `herb_sym_XXX`, `chinese_name`, `english_name`, `meridians`, `properties`, `external_ids` |
| `src/data/seed_herbs.json` | ~18 KB | ~18 herbs | Alchemy-style: `herb_001`, `common_name`, `properties.temperature`, `actions`, `contraindications` |

`src/data/seed_herbs.json` appears to be an early hand-curated seed for development, not an export of the SymMap pipeline.

### Pipeline Gap

- `07_build_master_herbs.py` outputs SymMap herbs → `data/output/seed_herbs.json`
- **No script** copies or transforms `data/output/seed_herbs.json` → `src/data/seed_herbs.json`
- `07_transform_formulas_for_alchemy.py` transforms formulas (data/output → src/data) but **reads** herbs from `src/data/seed_herbs.json` — so formula resolution uses the limited herb set

### Neo4j ↔ App

- **Direction:** Seed JSON → Neo4j (one-way)
- **No export script:** Neo4j is never dumped back to JSON for frontend/offline use
- Frontend/backend both import `src/data/seed_herbs.json` directly; neither queries Neo4j

---

## 4. Recommended Next Steps

1. **Add herb copy/transform step:** Either copy `data/output/seed_herbs.json` → `src/data/` (after schema mapping) or create `07_build_alchemy_herbs.py` to transform SymMap → Alchemy schema for the app.
2. **Optional Neo4j export:** If offline/mobile needs graph-derived data, add `scripts/09_export_neo4j_to_seed.py` (or similar) to dump Neo4j → `src/data/` JSON.
3. **Document pipeline order:** Run in sequence: `07_build_master_herbs` → (new herb step) → `07_transform_formulas_for_alchemy` → `08_build_graph`.

---

## 5. Data Flow (Current vs. Intended)

```
CURRENT:
  SymMap XLSX/CSV → 07_build_master_herbs → data/output/seed_herbs.json → 08_build_graph → Neo4j
  Shanghan Lun TXT → 05_extract_formulas → data/output/seed_formulas.json → 08_build_graph → Neo4j

  src/data/seed_herbs.json    ← orphaned (hand-curated, ~18 herbs)
  src/data/seed_formulas.json ← 07_transform_formulas (reads src/data/seed_herbs for herb_id resolution)

INTENDED (post-fix):
  data/output/seed_herbs.json → [NEW] transform/copy → src/data/seed_herbs.json
  src/data/seed_formulas.json ← 07_transform_formulas (would resolve against full herb set)
```
