-- Nei Dan (Internal Alchemy) practices for Dual Cultivation
-- target_pattern and instructions are arrays of text

CREATE TABLE IF NOT EXISTS nei_dan_practices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    target_pattern TEXT[] NOT NULL DEFAULT '{}',
    instructions TEXT[] NOT NULL DEFAULT '{}',
    safety_note TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nei_dan_target_pattern ON nei_dan_practices USING GIN(target_pattern);
