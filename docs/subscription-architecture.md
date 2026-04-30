# Subscription & account architecture

Current Almanac now uses a standard 2026 cross-platform subscription shape:

- **Identity**: Supabase Auth (`auth.users.id`)
- **Mobile billing**: RevenueCat + native store billing (App Store / Google Play)
- **Web + desktop billing**: RevenueCat Web Billing + Stripe
- **Backend subscription cache**: Supabase tables updated from RevenueCat webhooks and on-demand refreshes

## Canonical user id

The canonical application user id is the Supabase user UUID.

- Frontend signs in with email magic link / OTP.
- That UUID is used as the RevenueCat `appUserID`.
- The backend uses the authenticated Supabase bearer token to look up the user and sync profile/subscription state.

## Frontend model

Two Pinia stores back the account system:

- `authStore`
  - initializes Supabase auth
  - requests OTP email links
  - verifies OTP codes
  - exposes authenticated user/session state

- `subscriptionStore`
  - reads the backend subscription snapshot
  - starts purchase / restore / management flows
  - exposes a simple `paid` boolean
  - exposes `hasEntitlement("current_plus")`

### Gating convention

The primary entitlement key is:

- `current_plus`

App code should gate premium features through:

- `subscriptionStore.paid`
- `subscriptionStore.hasEntitlement("current_plus")`

That keeps feature checks simple while still preserving the richer metadata underneath.

## Backend model

The backend exposes:

- `POST /api/auth/email-otp`
- `GET /api/auth/session`
- `GET /api/me`
- `GET /api/subscription/state`
- `POST /api/revenuecat/webhook`

RevenueCat webhook handling follows RevenueCat's recommended pattern:

1. verify configured authorization header
2. use `event.id` for idempotency in `subscription_events`
3. fetch the latest subscriber payload from RevenueCat v1
4. normalize and persist the latest subscription snapshot in Supabase

## Supabase tables

The migration adds:

- `profiles`
- `subscription_customers`
- `subscription_state`
- `subscription_events`

### `subscription_state`

This is the main backend-friendly cache for entitlement checks.

Important fields:

- `is_paid`
- `active_entitlements`
- `active_products`
- `management_url`
- `store`
- `expires_at`
- `will_renew`
- `billing_issue_detected_at`
- `raw_customer_info`

If premium logic later moves server-side, backend enforcement should read this table instead of trusting only the client.

## Platform behavior

### iOS / Android

- RevenueCat Capacitor SDK is configured with the authenticated Supabase user id.
- Native purchase UI is presented through `@revenuecat/purchases-capacitor-ui`.
- Subscription management uses RevenueCat Customer Center when available.

### Web / Desktop

- RevenueCat Web SDK renders the paywall.
- Stripe handles checkout through RevenueCat Web Billing.
- Management opens the RevenueCat/Stripe management URL when available.

## Operational requirements

To make this fully production-ready, you still need to configure:

- Supabase auth project + redirect URLs
- RevenueCat public and secret keys
- RevenueCat offerings / entitlement definitions
- Stripe connection inside RevenueCat Web Billing
- RevenueCat webhook authorization header + webhook URL
- Apple and Google native products mapped to the same entitlement

## Security notes

- Mobile purchases must remain native in-app purchases.
- Web/desktop checkout should remain Stripe/RevenueCat web billing.
- Backend authorization must come from validated Supabase bearer tokens.
- Webhook requests should be authenticated using the configured RevenueCat authorization header.
