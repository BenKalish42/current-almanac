# Current Almanac

Current Almanac is a Vue 3 + TypeScript app scaffolded for a 2026 cross-platform release model:

- **Web** via Netlify + installable PWA
- **iOS** via Capacitor 7
- **Android** via Capacitor 7
- **Desktop** via Tauri 2 as the primary desktop shell
- **Optional desktop packaging workflow** via Electron Forge assets that were merged from the parallel deployment branch
- **Accounts** via Supabase Auth
- **Subscriptions** via RevenueCat
- **Web/Desktop billing** via RevenueCat Web Billing + Stripe
- **Native OTA updates** via Capgo

## Core scripts

- `npm run dev:web` — web development server
- `npm run dev:desktop` — run the Tauri desktop shell in development
- `npm run build:web` — production web/PWA build
- `npm run build:web:mobile` — embedded web build for native shells
- `npm run build:embedded` — alias for mobile-ready embedded web build
- `npm run build:mobile` — mobile web assets + Capacitor sync
- `npm run build:android:sync` — embedded web build + Android Capacitor sync
- `npm run build:ios:sync` — embedded web build + iOS Capacitor sync
- `npm run build:android` — build Android release bundle locally
- `npm run build:ios` — sync iOS project locally
- `npm run build:desktop` — desktop release build through Tauri
- `npm run desktop:package` — package Electron desktop shell
- `npm run desktop:make` — make Electron installers
- `npm run cap:sync` — sync Capacitor assets/plugins
- `npm run cap:ios` — open the iOS project in Xcode
- `npm run cap:android` — open the Android project in Android Studio
- `npm test -- --run` — run the focused Vitest suite

## Cross-platform architecture

### Delivery

- **Netlify** remains the web deploy target.
- **Capacitor** handles iOS and Android packaging.
- **Tauri 2** is the primary desktop packaging target in this repo.
- **Electron Forge** artifacts and workflow files were merged in from the parallel deployment branch so that desktop packaging work is preserved as an alternative path.
- **GitHub Actions + Fastlane** provide the release automation scaffolding.
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
- Electron desktop packaging config merged from the parallel deployment branch
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

The repo now includes two release automation shapes:

- **Primary Tauri/Capacitor flow**
  - `.github/workflows/release.yml`
  - `.github/workflows/android-release.yml`
  - `.github/workflows/ios-release.yml`
  - `.github/workflows/desktop-release.yml`
  - `.github/workflows/capgo-release.yml`

- **Merged parallel Electron/Capacitor flow**
  - `.github/workflows/release-everywhere.yml`

Read:

- `docs/release-runbook.md`
- `docs/subscription-architecture.md`
- `docs/deployment/app-store-desktop-release.md`
