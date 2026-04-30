# Release Runbook

## Goal

One release action should fan out to:

- Netlify web deploy
- Capgo OTA bundle upload for Capacitor apps
- Android Play pipeline
- iOS TestFlight / App Store pipeline
- Tauri desktop artifacts

## Branch + trigger model

- Development branch: `cursor/platform-deployment-subscriptions-faa8`
- Long-term release branch: your normal default branch after merge
- Main orchestration workflow: `.github/workflows/release.yml`

### Recommended usage

1. Merge reviewed work into your main branch.
2. Trigger the **Cross-platform Release Orchestrator** workflow manually from GitHub Actions.
3. Set:
   - `release_version` e.g. `0.2.0`
   - `release_channel` one of `production`, `staging`, `beta`
   - enable/disable mobile/desktop jobs as needed

This gives you the “one click” release surface from GitHub.

## Required GitHub secrets

### Shared app / backend

- `VITE_API_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_SUPABASE_AUTH_REDIRECT_TO`
- `VITE_REVENUECAT_PUBLIC_API_KEY`
- `VITE_REVENUECAT_WEB_API_KEY`
- `VITE_DEEPSEEK_API_KEY` or `VITE_LLM_API_KEY`

### Capgo

- `CAPGO_TOKEN`
- optional: `CAPGO_PRIVATE_KEY`

### Android / Play

- `ANDROID_KEYSTORE_FILE_BASE64`
- `ANDROID_KEYSTORE_ALIAS`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_PASSWORD`
- `PLAY_CONFIG_JSON`

### iOS / App Store Connect

- `APPLE_KEY_ID`
- `APPLE_ISSUER_ID`
- `APPLE_KEY_CONTENT`
- `APPLE_TEAM_ID`
- `APPLE_BUNDLE_IDENTIFIER`
- `APPLE_PROFILE_NAME`
- `BUILD_CERTIFICATE_BASE64`
- `BUILD_PROVISION_PROFILE_BASE64`
- `P12_PASSWORD`

### Desktop signing

- macOS signing/notarization secrets as needed later
- Windows signing secrets as needed later

## Required external dashboard setup

### Supabase

1. Enable email OTP / magic-link auth.
2. Add your production web URL and custom scheme / deep-link targets.
3. Run the subscription/profile migration:
   - `supabase/migrations/20260430000100_create_profiles_and_subscriptions.sql`

### RevenueCat

1. Create apps for iOS, Android, and Web.
2. Create the entitlement:
   - `current_plus`
3. Map products/packages to that entitlement.
4. Configure the webhook endpoint:
   - `POST /api/revenuecat/webhook`
5. Set a shared authorization header and copy the same value into:
   - `REVENUECAT_WEBHOOK_AUTHORIZATION`

### Stripe

1. Connect Stripe to RevenueCat Web Billing.
2. Create the monthly web product for:
   - `$13.31/month`
3. Configure the customer portal / management flow.

### Google Play

1. Create the subscription product and base plan.
2. Grant the service account access in Play Console.
3. Upload the base64 keystore and Play service account JSON to GitHub secrets.

### Apple

1. Create the auto-renewable subscription product in App Store Connect.
2. Enable In-App Purchase capability in the Xcode project before first submission.
3. Create App Store Connect API key, certificate, and provisioning profile.
4. Upload them to GitHub secrets.

## Local validation commands

### Web

```bash
npm run build
npm test -- --run
```

### Native sync

```bash
npm run cap:sync:android
npx cap sync ios
```

### Backend syntax check

```bash
python3 -m compileall backend
```

## Current limitations

- iOS store submission cannot be end-to-end validated from this Linux environment.
- Fastlane is scaffolded in-repo, but Ruby/Fastlane must run in CI or on a machine with Ruby installed.
- Desktop store submission is not included yet; current desktop target is downloadable Tauri artifacts.

## Recommended next release hardening

- Add store metadata / screenshots automation.
- Add semantic version bumping tied to releases.
- Add desktop signing + notarization.
- Add Android versionCode auto-incrementing sourced from GitHub run number or release metadata.
