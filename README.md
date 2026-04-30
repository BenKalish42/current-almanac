# Current Almanac

Current Almanac is a Vue 3 + TypeScript app that now targets:

- Web via Netlify + PWA installability
- iOS via Capacitor
- Android via Capacitor
- Desktop via Tauri 2

## Core scripts

- `npm run dev:web` — web development server
- `npm run build:web` — production web build
- `npm run build:mobile` — mobile web assets + Capacitor sync
- `npm run build:desktop` — desktop release build through Tauri
- `npm run cap:add:ios` / `npm run cap:add:android` — create native projects
- `npm run cap:sync` — sync Capacitor assets/plugins
- `npm run dev:desktop` — run the Tauri desktop shell in development

## Platform notes

- The web build is now installable as a PWA.
- Capacitor OTA support is scaffolded with Capgo; production credentials still need to be supplied.
- RevenueCat and Supabase dependencies are installed as the subscription/account foundation for the next implementation stages.
- iOS was initialized with Swift Package Manager support so it can be synced in environments without CocoaPods.

## Release direction

This repository is being prepared for a unified release workflow:

- Netlify for web
- GitHub Actions + Fastlane for App Store / Play Store submission
- Tauri artifacts for desktop release downloads
- RevenueCat + Stripe + native stores for subscriptions

More detailed runbooks and setup docs will be added as the remaining implementation phases are completed.
