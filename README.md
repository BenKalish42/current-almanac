# Current Almanac

Current Almanac is a Vue 3 + TypeScript app now scaffolded for a 2026 cross-platform release model:

- **Web** via Netlify + installable PWA
- **iOS** via Capacitor 7
- **Android** via Capacitor 7
- **Desktop** via Tauri 2
- **Accounts** via Supabase Auth
- **Subscriptions** via RevenueCat
- **Web/Desktop billing** via RevenueCat Web Billing + Stripe
- **Native OTA updates** via Capgo

## Core scripts

- `npm run dev:web` — web development server
- `npm run dev:desktop` — run the Tauri desktop shell in development
- `npm run build:web` — production web/PWA build
- `npm run build:mobile` — mobile web assets + Capacitor sync
- `npm run build:desktop` — desktop release build through Tauri
- `npm run cap:sync` — sync Capacitor assets/plugins
- `npm run cap:sync:ios` — sync iOS native project
- `npm run cap:sync:android` — sync Android native project
- `npm run cap:ios` — open the iOS project in Xcode
- `npm run cap:android` — open the Android project in Android Studio
- `npm test -- --run` — run the focused Vitest suite

## Cross-platform architecture

### Delivery

- **Netlify** remains the web deploy target.
- **Capacitor** handles iOS and Android packaging.
- **Tauri 2** handles desktop packaging and downloadable artifacts.
- **GitHub Actions + Fastlane** provide the one-release-fans-out-to-all-targets workflow.
- **Capgo** is wired as the OTA/update lane for shipped native apps.

### Identity

- **Supabase Auth** is the canonical account layer.
- Email magic link / OTP is the initial authentication method.
- The canonical user id is the Supabase auth user id and is reused as the RevenueCat app user id.

### Billing / entitlements

- **RevenueCat** is the subscription abstraction layer.
- **iOS / Android** use native store purchases.
- **Web / Desktop** use RevenueCat Web Billing with Stripe.
- Backend webhook + customer sync normalizes a simple `paid` state into Supabase for trusted app/backend gating.

## Current implementation status

Implemented in-repo:

- PWA manifest + service worker generation
- Capacitor iOS / Android projects
- Tauri desktop shell + generated icons
- Supabase auth store and settings panel
- RevenueCat service/store scaffolding
- Backend subscription sync + RevenueCat webhook endpoint
- Supabase migration for profiles + subscription state cache
- Example premium gating for Current Flow Analysis and AI chat
- Release workflow scaffolding in `.github/workflows/`
- Fastlane lane scaffolding in `fastlane/`

Still requires external setup:

- Supabase project + auth config
- RevenueCat products / offerings / entitlement setup
- Stripe connection to RevenueCat Web Billing
- Apple App Store Connect credentials
- Google Play service account + keystore
- Capgo project + API token
- Netlify environment variables

## Release workflow

The repo now includes a fan-out release workflow strategy:

- `.github/workflows/release.yml` — orchestrator
- `.github/workflows/android-release.yml` — Play internal/production lane
- `.github/workflows/ios-release.yml` — TestFlight/App Store lane
- `.github/workflows/desktop-release.yml` — Tauri desktop artifacts
- `.github/workflows/capgo-release.yml` — OTA bundle upload

Read `docs/release-runbook.md` for required secrets and release setup.
