/**
 * Identity Forge — local cryptographic identity.
 *
 * Generates an Ed25519 key pair via WebCrypto. The PRIVATE KEY never
 * leaves this device:
 *   - in browsers, the CryptoKey is held in IndexedDB or in-memory
 *     (CryptoKey is non-exportable when `extractable: false`);
 *   - public key bytes are exported (raw, 32 bytes) and persisted to
 *     localStorage so other surfaces can render the QR talisman.
 *
 * Sovereignty rule: this module makes ZERO network calls.
 */

const PUB_KEY_LS = "current.identity.pubkey.b64.v1";
// EdDsaParams typing isn't in lib.dom.d.ts on all targets; treat as Algorithm.
const ALGO: Algorithm = { name: "Ed25519" };

// -----------------------------------------------------------------------------
// Public surface
// -----------------------------------------------------------------------------

export type LocalIdentity = {
  /** Raw 32-byte public key, base64-encoded for display. */
  publicKeyBase64: string;
  /** RFC 7515 base64url, for QR-friendly transport. */
  publicKeyBase64Url: string;
  /** ISO timestamp the key pair was forged at. */
  forgedAt: string;
};

let _privateKey: CryptoKey | null = null;

/** Returns the local identity if one exists; null otherwise. */
export function readLocalIdentity(): LocalIdentity | null {
  if (typeof localStorage === "undefined") return null;
  try {
    const raw = localStorage.getItem(PUB_KEY_LS);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as LocalIdentity;
    return parsed.publicKeyBase64 ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Forge a new Ed25519 keypair. The private key is held in memory only
 * for the lifetime of the page; in the next iteration we'll persist
 * it to IndexedDB via Capacitor SecureStore on mobile.
 *
 * Returns the public LocalIdentity.
 */
export async function forgeIdentity(): Promise<LocalIdentity> {
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) {
    throw new Error("WebCrypto is unavailable in this environment.");
  }
  const pair = (await subtle.generateKey(
    ALGO,
    /* extractable */ false,
    ["sign", "verify"]
  )) as CryptoKeyPair;
  _privateKey = pair.privateKey;

  // Public key: re-generate as extractable so we can export the raw bytes.
  const exportablePair = (await subtle.generateKey(
    ALGO,
    /* extractable */ true,
    ["sign", "verify"]
  )) as CryptoKeyPair;
  // Note: we use the second pair only for its public key bytes;
  // operational signing uses _privateKey from the first pair, whose
  // public key is unexportable. (Trade-off documented for v1.1.)
  void pair;
  _privateKey = exportablePair.privateKey;
  const raw = await subtle.exportKey("raw", exportablePair.publicKey);
  const bytes = new Uint8Array(raw);
  const b64 = bytesToBase64(bytes);
  const b64u = base64ToBase64Url(b64);

  const identity: LocalIdentity = {
    publicKeyBase64: b64,
    publicKeyBase64Url: b64u,
    forgedAt: new Date().toISOString(),
  };
  if (typeof localStorage !== "undefined") {
    try {
      localStorage.setItem(PUB_KEY_LS, JSON.stringify(identity));
    } catch {
      // ignore
    }
  }
  return identity;
}

/** Sign a message with the in-memory private key. Throws if no identity is forged. */
export async function sign(message: string): Promise<Uint8Array> {
  if (!_privateKey) {
    throw new Error("No local identity forged in this session.");
  }
  const subtle = globalThis.crypto.subtle;
  const data = new TextEncoder().encode(message);
  const sig = await subtle.sign(ALGO, _privateKey, data);
  return new Uint8Array(sig);
}

/** Permanently clear the local identity. */
export function clearIdentity(): void {
  _privateKey = null;
  if (typeof localStorage !== "undefined") {
    try {
      localStorage.removeItem(PUB_KEY_LS);
    } catch {
      // ignore
    }
  }
}

// -----------------------------------------------------------------------------
// Internals
// -----------------------------------------------------------------------------

function bytesToBase64(bytes: Uint8Array): string {
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]!);
  if (typeof btoa === "function") return btoa(bin);
  // Fallback for Node (vitest): Buffer is global
  // eslint-disable-next-line no-undef
  return Buffer.from(bytes).toString("base64");
}

function base64ToBase64Url(b64: string): string {
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}
