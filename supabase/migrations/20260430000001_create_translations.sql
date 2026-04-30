-- Task 12.5 — Pan-Asian language engine
-- Side tables for per-language { script, roman } translations of every
-- term that today is rendered in Chinese (Hanzi) or Pinyin in the app.
--
-- Frontend (`src/data/seed_*.json`) remains the canonical source of truth;
-- these tables let server-side queries (GraphRAG, future user-facing
-- search, etc.) read the same translations Neo4j receives from
-- `scripts/08_build_graph.py`.
--
-- Schema mirrors the Neo4j (:Translation) node shape:
--   (parent_id, lang) PK, plus (script, roman) string fields.

CREATE TABLE IF NOT EXISTS herb_translations (
    herb_id TEXT NOT NULL REFERENCES herbs(id) ON DELETE CASCADE,
    lang TEXT NOT NULL,
    script TEXT NOT NULL DEFAULT '',
    roman TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (herb_id, lang)
);

CREATE INDEX IF NOT EXISTS idx_herb_translations_lang
    ON herb_translations(lang);

CREATE INDEX IF NOT EXISTS idx_herb_translations_script_trgm
    ON herb_translations USING gin (script gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_herb_translations_roman_trgm
    ON herb_translations USING gin (roman gin_trgm_ops);


CREATE TABLE IF NOT EXISTS formula_translations (
    formula_id TEXT NOT NULL REFERENCES formulas(id) ON DELETE CASCADE,
    lang TEXT NOT NULL,
    script TEXT NOT NULL DEFAULT '',
    roman TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (formula_id, lang)
);

CREATE INDEX IF NOT EXISTS idx_formula_translations_lang
    ON formula_translations(lang);

CREATE INDEX IF NOT EXISTS idx_formula_translations_script_trgm
    ON formula_translations USING gin (script gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_formula_translations_roman_trgm
    ON formula_translations USING gin (roman gin_trgm_ops);


-- Hexagram translations are not currently stored in Postgres (the
-- frontend reads them statically from seed_hexagrams.json), but the
-- table is created so that server-side endpoints can adopt the same
-- pattern without a future schema migration.
CREATE TABLE IF NOT EXISTS hexagram_translations (
    hex_id INTEGER NOT NULL CHECK (hex_id BETWEEN 1 AND 64),
    lang TEXT NOT NULL,
    script TEXT NOT NULL DEFAULT '',
    roman TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (hex_id, lang)
);

CREATE INDEX IF NOT EXISTS idx_hexagram_translations_lang
    ON hexagram_translations(lang);


-- Comments for self-documentation in the Supabase UI / SQL inspector.
COMMENT ON TABLE herb_translations IS
    'Task 12.5: per-language { script, roman } cells for herb names. lang is a LanguageCode from src/lib/languages.ts.';
COMMENT ON TABLE formula_translations IS
    'Task 12.5: per-language { script, roman } cells for classical formula names.';
COMMENT ON TABLE hexagram_translations IS
    'Task 12.5: per-language { script, roman } cells for the 64 Yi-Jing hexagrams.';
