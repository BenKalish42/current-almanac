-- Phase 8: Practitioner Pantry - user inventory for herbs
-- Links user (by session/device ID) to herbs they have in stock

CREATE TABLE IF NOT EXISTS user_pantry (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    herb_id TEXT NOT NULL REFERENCES herbs(id) ON DELETE CASCADE,
    in_stock BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, herb_id)
);

CREATE INDEX IF NOT EXISTS idx_user_pantry_user_id ON user_pantry(user_id);
CREATE INDEX IF NOT EXISTS idx_user_pantry_herb_id ON user_pantry(herb_id);
