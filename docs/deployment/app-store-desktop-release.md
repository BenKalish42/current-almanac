# App store and desktop release setup

This repo now has the first deployable shell for Current Almanac across web, desktop, iOS, and Android.

## Release command

Use GitHub Actions > Release Everywhere > Run workflow.

The workflow builds the existing Netlify web app, uploads desktop installers to a GitHub Release, and sends native builds through Fastlane lanes for TestFlight and Google Play.

## Required repository variables

- `APPLE_TEAM_ID`
- `APP_STORE_CONNECT_TEAM_ID`, if the App Store Connect team differs from `APPLE_TEAM_ID`
- `IOS_BUNDLE_ID`, optional; defaults to `com.current.almanac`
- `ANDROID_PACKAGE_NAME`, optional; defaults to `com.current.almanac`
- `GOOGLE_PLAY_TRACK`, optional; defaults to `internal`

## Required repository secrets

- `APP_STORE_CONNECT_KEY_ID`
- `APP_STORE_CONNECT_ISSUER_ID`
- `APP_STORE_CONNECT_KEY_CONTENT`
- `IOS_DISTRIBUTION_CERTIFICATE_BASE64`
- `IOS_DISTRIBUTION_CERTIFICATE_PASSWORD`
- `IOS_PROVISIONING_PROFILE_BASE64`
- `IOS_KEYCHAIN_PASSWORD`
- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_PASSWORD`
- `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON_BASE64`

## Optional repository variables

- `APP_STORE_CONNECT_KEY_IS_BASE64`, set to `true` if the key content is base64 encoded
- `IOS_PROVISIONING_PROFILE_NAME`, if the embedded profile name must be pinned

## Local checks

- `npm run build`
- `npm run build:mobile`
- `npm run desktop:package`
- `cd android && ./gradlew bundleRelease`

iOS archives require macOS with Xcode and CocoaPods. The GitHub workflow installs pods on the macOS runner.
