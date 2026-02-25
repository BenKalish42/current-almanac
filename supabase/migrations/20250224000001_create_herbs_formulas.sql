-- Phase 3: Herbs and Formulas tables for GraphRAG
-- Run this migration in Supabase SQL Editor or via Supabase CLI

-- Herbs table (Tier 1 Food Grade, Tier 2 Apothecary)
CREATE TABLE IF NOT EXISTS herbs (
    id TEXT PRIMARY KEY,
    pinyin_name TEXT NOT NULL,
    common_name TEXT NOT NULL,
    safety_tier INTEGER NOT NULL CHECK (safety_tier IN (1, 2, 3)),
    properties JSONB NOT NULL DEFAULT '{}',
    actions TEXT[] NOT NULL DEFAULT '{}',
    contraindications TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Formulas table
CREATE TABLE IF NOT EXISTS formulas (
    id TEXT PRIMARY KEY,
    pinyin_name TEXT NOT NULL,
    common_name TEXT NOT NULL,
    primary_pattern TEXT NOT NULL,
    actions TEXT[] NOT NULL DEFAULT '{}',
    safety_note TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Formula architecture: links formulas to herbs (Jun-Chen-Zuo-Shi roles)
CREATE TABLE IF NOT EXISTS formula_architecture (
    id SERIAL PRIMARY KEY,
    formula_id TEXT NOT NULL REFERENCES formulas(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    herb_id TEXT NOT NULL REFERENCES herbs(id) ON DELETE RESTRICT,
    pinyin_name TEXT NOT NULL,
    dosage_percentage NUMERIC(5, 2) NOT NULL,
    purpose TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for GraphRAG traversal
CREATE INDEX IF NOT EXISTS idx_formula_architecture_formula_id ON formula_architecture(formula_id);
CREATE INDEX IF NOT EXISTS idx_formula_architecture_herb_id ON formula_architecture(herb_id);
CREATE INDEX IF NOT EXISTS idx_herbs_safety_tier ON herbs(safety_tier);
CREATE INDEX IF NOT EXISTS idx_formulas_primary_pattern ON formulas(primary_pattern);

-- Enable RLS (optional - disable if using service role for backend-only access)
-- ALTER TABLE herbs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE formulas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE formula_architecture ENABLE ROW LEVEL SECURITY;
