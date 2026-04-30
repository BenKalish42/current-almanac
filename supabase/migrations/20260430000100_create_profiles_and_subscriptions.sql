-- Cross-platform account and subscription foundation
-- Canonical identity is auth.users.id; RevenueCat app_user_id mirrors this UUID.

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscription_customers (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    revenuecat_app_user_id TEXT NOT NULL UNIQUE,
    revenuecat_original_app_user_id TEXT,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscription_state (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
    active_entitlements JSONB NOT NULL DEFAULT '{}'::jsonb,
    active_products JSONB NOT NULL DEFAULT '[]'::jsonb,
    store TEXT,
    period_type TEXT,
    management_url TEXT,
    expires_at TIMESTAMPTZ,
    will_renew BOOLEAN,
    billing_issue_detected_at TIMESTAMPTZ,
    raw_customer_info JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscription_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    store TEXT,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_subscription_customers_revenuecat_app_user_id
    ON subscription_customers(revenuecat_app_user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_state_is_paid ON subscription_state(is_paid);
CREATE INDEX IF NOT EXISTS idx_subscription_state_updated_at ON subscription_state(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_subscription_events_user_id ON subscription_events(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_received_at ON subscription_events(received_at DESC);
