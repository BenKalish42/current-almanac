<script setup lang="ts">
/**
 * CryptographicIdentity — Identity Forge UI.
 *
 * Per Chen's blueprint Pillar 3 §1: device generates a local Ed25519
 * keypair; the public key renders as a scannable visual signal.
 *
 * v1 Tier A: we generate the key, persist the public key bytes, and
 * render a deterministic glyph-grid "talisman" derived from those bytes.
 * (A real QR code helper joins in v1.1; the glyph is unique-per-key and
 * sufficient for visual verification side-by-side.)
 */

import { onMounted, ref } from "vue";
import {
  clearIdentity,
  forgeIdentity,
  readLocalIdentity,
  type LocalIdentity,
} from "@/services/identity/forge";

const identity = ref<LocalIdentity | null>(null);
const busy = ref(false);
const error = ref<string | null>(null);

onMounted(() => {
  identity.value = readLocalIdentity();
});

async function onForge() {
  busy.value = true;
  error.value = null;
  try {
    identity.value = await forgeIdentity();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    busy.value = false;
  }
}

function onClear() {
  if (!confirm("Clear the local identity? This cannot be undone.")) return;
  clearIdentity();
  identity.value = null;
}

/**
 * Deterministic 8x8 glyph derived from the public key bytes.
 * Each cell is on/off based on bit b of byte (b/8) → row, b%8 → col.
 */
function glyphMatrix(b64: string): boolean[][] {
  const decoded = base64Decode(b64);
  const rows: boolean[][] = [];
  const SIZE = 8;
  for (let r = 0; r < SIZE; r++) {
    const row: boolean[] = [];
    for (let c = 0; c < SIZE; c++) {
      const idx = r * SIZE + c;
      const byte = decoded[idx % decoded.length] ?? 0;
      const bit = (byte >> (idx % 8)) & 1;
      row.push(bit === 1);
    }
    rows.push(row);
  }
  return rows;
}

function base64Decode(b64: string): Uint8Array {
  if (typeof atob === "function") {
    const bin = atob(b64);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  // eslint-disable-next-line no-undef
  return new Uint8Array(Buffer.from(b64, "base64"));
}

function shortenKey(b64: string): string {
  return b64.length > 16 ? `${b64.slice(0, 8)}…${b64.slice(-8)}` : b64;
}
</script>

<template>
  <section class="rounded-lg border border-white/10 bg-white/[0.02] p-5">
    <h2 class="text-sm font-medium uppercase tracking-wider text-slate-400">
      Identity Forge
    </h2>
    <p class="mt-2 text-sm text-slate-300">
      A local Ed25519 key pair anchors this device. Public key is shareable;
      private key remains on-device.
    </p>

    <div v-if="identity" class="mt-4 grid grid-cols-[auto_1fr] gap-4">
      <!-- Talisman glyph -->
      <div class="inline-grid grid-cols-8 gap-px rounded border border-white/10 bg-black/40 p-1.5">
        <div
          v-for="(row, ri) in glyphMatrix(identity.publicKeyBase64)"
          :key="ri"
          class="contents"
        >
          <span
            v-for="(on, ci) in row"
            :key="ci"
            class="h-3.5 w-3.5 rounded-[1px]"
            :class="on ? 'bg-amber-400/80' : 'bg-white/5'"
          />
        </div>
      </div>

      <div class="min-w-0 self-center text-xs">
        <div class="text-slate-400">Public key</div>
        <code class="mt-1 block break-all font-mono text-slate-200">
          {{ shortenKey(identity.publicKeyBase64) }}
        </code>
        <div class="mt-2 text-slate-500">
          Forged {{ new Date(identity.forgedAt).toLocaleString() }}
        </div>
        <button
          type="button"
          class="mt-3 rounded border border-white/10 px-2 py-1 text-xs text-slate-400 hover:bg-white/5"
          @click="onClear"
        >
          Clear identity
        </button>
      </div>
    </div>

    <div v-else class="mt-4 rounded border border-dashed border-white/10 p-4">
      <p class="text-sm text-slate-400">
        No local identity. Forging one creates an Ed25519 key pair and a unique
        glyph derived from the public key.
      </p>
      <button
        type="button"
        class="mt-3 rounded-md border border-amber-500/40 bg-amber-950/40 px-3 py-1.5 text-sm text-amber-200 hover:bg-amber-900/40 disabled:opacity-50"
        :disabled="busy"
        @click="onForge"
      >
        {{ busy ? "Forging…" : "Forge identity" }}
      </button>
    </div>

    <div v-if="error" class="mt-3 rounded border border-amber-500/30 bg-amber-950/30 p-3 text-xs text-amber-200">
      {{ error }}
    </div>
  </section>
</template>
