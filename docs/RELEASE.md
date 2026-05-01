# Current — Release Checklist

This is the operator's checklist for cutting a release of Current Almanac.
Most of the actual store-publish steps are gated by repository secrets that
have **not** been set yet — the workflows exist; the publish steps are
`if: false`-gated until the Jun decides to ship to a store. See §6 below.

---

## 1. Pre-flight (every release)

- [ ] `npm install` clean (no lockfile drift).
- [ ] `npm run build` green.
- [ ] `npm test -- --run` green (`npm run test:math` + `npm run test:contracts` will be exercised by the suite).
- [ ] `tests/perf/bundle-budget.spec.ts` passes (run after `npm run build`).
- [ ] `rg -n "ancient wisdom|poetic|destiny|moralizing|karmic" src/ backend/ -g '!**/yiJingLines.json' -g '!**/seed_hexagrams*' -g '!**/data/chunked/**' -g '!**/contracts/**' -g '!**/tests/contracts/**'` → 0 hits.

## 2. Capacitor mobile sanity

- [ ] `npm run build:mobile` succeeds (runs `cap sync` against `android/` + `ios/`).
- [ ] `npx cap doctor` returns no errors.
- [ ] (Android) `cd android && ./gradlew bundleRelease` completes locally with the project's signing config — only if you have keystore credentials.

## 3. Desktop (Electron Forge) sanity

- [ ] `npm run desktop:package` produces a packaged app for the host platform.
- [ ] `npm run desktop:make` produces installers for the host platform's targets.

## 4. Backend health

- [ ] `python3.12 -m uvicorn backend.main:app --reload --port 8000` boots clean.
- [ ] `curl http://127.0.0.1:8000/health` returns `{"status":"ok"...}`.
- [ ] `curl http://127.0.0.1:8000/api/models` returns the four-family catalog with correct `keyConfigured` flags for whatever keys are set in `backend/.env`.

## 5. Tag

```bash
git tag v1.0.0-rc.1
git push origin v1.0.0-rc.1
```

## 6. Store publishing — DEFERRED

The following workflows are scaffolded but their publish steps are
`if: false`-gated until secrets are configured. **Do not enable any of
these in CI until the Jun explicitly approves:**

- `.github/workflows/android-release.yml` — needs `KEYSTORE_*`, Play service-account JSON.
- `.github/workflows/ios-release.yml` — needs Apple Developer account, signing certs, Provisioning Profile.
- `.github/workflows/desktop-release.yml` — needs Apple notarization (mac), code-signing certs (win).
- `.github/workflows/capgo-release.yml` — needs Capgo API token.
- `.github/workflows/release-everywhere.yml` — orchestrates the above.

When ready, populate the secrets in GitHub → Settings → Secrets & variables → Actions, then flip the `if: false` guards.

## 7. Sovereignty audit (ship-blocker)

- [ ] No new outbound endpoints introduced unless they are: DeepSeek (Oracle), Open-Meteo (weather/geocoding), Discourse (deferred), Matrix (homeserver — deferred).
- [ ] `data/contracts/forbidden.json` unchanged or expanded only.
- [ ] Auth/subscriptions branch (`defer/v1.1-accounts`) untouched.
