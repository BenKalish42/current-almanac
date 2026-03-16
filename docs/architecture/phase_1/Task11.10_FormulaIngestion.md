# Task 11.10 - HuggingFace Formula Ingestion (BATMAN-TCM 2.0)

## Objective

Ingest the BATMAN-TCM 2.0 corpus from HuggingFace and transform it into the local
formula graph payload (`src/data/formulas.json`) that powers:

- `ClassicalFormula` nodes
- `FormulaIngredient` edges (Jun/Chen/Zuo/Shi + dosage)
- `MarketVariant` nodes

## Script

File: `scripts/11_etl_huggingface_formulas.py`

### Dependencies

- `datasets`
- `pandas`

Install:

```bash
pip install datasets pandas
```

### Dataset loading

The ETL uses HuggingFace streaming/load path:

```python
dataset = load_dataset("insilicomedicine/batman2")
```

It selects `train` by preference (then `validation`, then `test`) and converts the
selected split to a DataFrame for schema-flexible row transforms.

## Transformation & Mapping

### Formula extraction

- Maps formula name fields into:
  - `name_pinyin`
  - `name_hanzi`
- Builds deterministic formula IDs:
  - `classical_<slugified_name>`

### Ingredient extraction

Supports both BATMAN row styles:

- nested ingredient payload columns (`herb_list`, `ingredients`, etc.)
- flat row-level ingredient columns (`herb_name`, `role_label`, `dosage`)

### Role mapping

Normalizes role labels to strict schema values:

- `Jun`
- `Chen`
- `Zuo`
- `Shi`

Synonyms like `King/Minister/Assistant/Envoy` are mapped to the canonical set.

### Dosage mapping

- Parses numeric dosage from structured values or free-text dosage strings.
- Writes dosage into:
  - `classical_dosage_ratio` for `FormulaIngredient`
  - `exact_dosage_grams` for `MarketVariant.actual_ingredients`

## ID Bridge and Local Herb Normalization

The ETL loads local herbs from:

1. `src/data/herbs.json` (preferred), else
2. `src/data/seed_herbs.json` (fallback)

`normalize_herb_id()` performs robust slug normalization and alias matching
against local herb IDs and names.

Strict inclusion rule:

- only ingredients that successfully map to local `herb_id` are included.
- unmatched BATMAN ingredient names are skipped.

## Output

Writes transformed payload to:

- `src/data/formulas.json`

Console summary format:

- `Successfully ingested X formulas and Y edges from BATMAN-TCM 2.0.`

This keeps the ingestion pipeline auditable and aligned with the frontend schema contract.
