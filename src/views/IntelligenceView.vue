<script setup lang="ts">
/**
 * Pillar 3 — Sovereign Courtyard.
 *
 * Tier A (live):
 *   - Identity Forge (local Ed25519, glyph talisman)
 *   - Courtyard shell (lobby copy, lock-icon design system)
 *
 * Tier B/C (scaffolded; activate when VITE_MATRIX_HOMESERVER_URL is set
 * and matrix-js-sdk is dynamically loaded — slated for v1.1).
 */

import { computed } from "vue";
import CryptographicIdentity from "@/components/intelligence/CryptographicIdentity.vue";

const homeserverConfigured = computed(() => {
  return Boolean(
    (import.meta.env.VITE_MATRIX_HOMESERVER_URL as string | undefined)?.trim()
  );
});
</script>

<template>
  <div class="mx-auto max-w-3xl p-6 text-slate-100">
    <header class="mb-6">
      <h1 class="text-xl font-semibold tracking-tight">Sovereign Courtyard</h1>
      <p class="mt-1 text-sm text-slate-400">
        Local cryptographic identity. Direct, end-to-end encrypted exchange.
      </p>
    </header>

    <CryptographicIdentity />

    <section class="mt-6 rounded-lg border border-white/10 bg-white/[0.02] p-5">
      <header class="flex items-center gap-2">
        <span aria-hidden="true" class="text-amber-400">🔒</span>
        <h2 class="text-sm font-medium uppercase tracking-wider text-slate-400">
          Courtyard
        </h2>
      </header>

      <p v-if="homeserverConfigured" class="mt-2 text-sm text-slate-300">
        Homeserver is configured. Direct exchange will activate once a peer is
        discovered.
      </p>
      <p v-else class="mt-2 text-sm text-slate-300">
        Direct exchange between identified peers. No homeserver is configured.
      </p>
      <p v-if="!homeserverConfigured" class="mt-2 text-xs text-slate-500">
        Set <code class="rounded bg-black/40 px-1">VITE_MATRIX_HOMESERVER_URL</code> in
        your environment to enable connection. Disabled by default.
      </p>
    </section>

    <section class="mt-6 rounded-lg border border-white/10 bg-white/[0.02] p-5 opacity-60">
      <h2 class="text-sm font-medium uppercase tracking-wider text-slate-400">
        Encrypted Payload · Composite Reading · Mesh
      </h2>
      <p class="mt-2 text-sm text-slate-400">
        These surfaces are scaffolded; they activate once at least one peer is
        connected.
      </p>
    </section>
  </div>
</template>
