<script setup lang="ts">
/**
 * Pillar 3 — Sovereign Courtyard (placeholder).
 *
 * Tier A (Identity Forge + Courtyard shell) is wired in Stream 5b.
 * This file ships an empty-state surface so the route exists from RC1.
 */
</script>

<template>
  <div class="mx-auto max-w-3xl p-6 text-slate-100">
    <header class="mb-6">
      <h1 class="text-xl font-semibold tracking-tight">Sovereign Courtyard</h1>
      <p class="mt-1 text-sm text-slate-400">
        Local cryptographic identity. Direct, end-to-end encrypted exchange.
      </p>
    </header>

    <section class="rounded-lg border border-white/10 bg-white/[0.02] p-5">
      <h2 class="text-sm font-medium uppercase tracking-wider text-slate-400">
        Identity Forge
      </h2>
      <p class="mt-2 text-sm text-slate-300">
        A local Ed25519 key pair anchors this device. Public key is shareable;
        private key remains on-device.
      </p>
      <div class="mt-4 rounded border border-dashed border-white/10 p-4 text-sm text-slate-500">
        Identity is not yet generated. Generation tooling is wired in the next iteration.
      </div>
    </section>

    <section class="mt-6 rounded-lg border border-white/10 bg-white/[0.02] p-5">
      <h2 class="text-sm font-medium uppercase tracking-wider text-slate-400">
        Courtyard
      </h2>
      <p class="mt-2 text-sm text-slate-300">
        Direct exchange between identified peers. No homeserver is configured.
      </p>
      <p class="mt-2 text-xs text-slate-500">
        Set <code class="rounded bg-black/40 px-1">VITE_MATRIX_HOMESERVER_URL</code> to enable
        connection. Disabled by default.
      </p>
    </section>

    <section class="mt-6 rounded-lg border border-white/10 bg-white/[0.02] p-5 opacity-60">
      <h2 class="text-sm font-medium uppercase tracking-wider text-slate-400">
        Encrypted Payload · Composite Reading · Mesh
      </h2>
      <p class="mt-2 text-sm text-slate-400">
        These surfaces are scaffolded; they activate when at least one peer is connected.
      </p>
    </section>
  </div>
</template>
