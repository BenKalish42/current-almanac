# Archived community stack (2026)

This folder preserves the **Mastodon + LayerBB + Matrix** Community tab implementation before migration to **Discourse**.

## Layout (mirrors former `src/` paths)

- `src/composables/useMastodon.ts` — Mastodon REST via `masto`
- `src/composables/useLayerBB.ts` — generic forum REST client
- `src/components/community/MastodonFeed.vue`
- `src/components/community/LayerBBForum.vue`
- `src/components/community/MatrixChat.vue`
- `src/services/matrix/matrixClient.ts` — `matrix-js-sdk` + Rust crypto init

## Restore

Copy files back into the main `src/` tree, re-add npm deps (`masto`, `matrix-js-sdk`, `@matrix-org/matrix-sdk-crypto-wasm`), and restore `CommunityView.vue` imports from git history if needed.

## Why archived

Single-platform community (Discourse) reduces ops and API surface while keeping forum + chat patterns in one product.
