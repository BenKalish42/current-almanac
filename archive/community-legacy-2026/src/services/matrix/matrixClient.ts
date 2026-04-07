import {
  createClient,
  type MatrixClient,
  IndexedDBStore,
  IndexedDBCryptoStore,
  ClientEvent,
  SyncState,
  EventType,
} from "matrix-js-sdk";

export interface MatrixClientOptions {
  baseUrl: string;
  accessToken: string;
  userId: string;
  deviceId?: string;
}

/**
 * Read Matrix credentials from Vite env. All three are required to start sync.
 */
export function getMatrixConfigFromEnv(): MatrixClientOptions | null {
  const baseUrl = (import.meta.env.VITE_MATRIX_HOMESERVER_URL as string | undefined)?.replace(/\/$/, "") ?? "";
  const accessToken = (import.meta.env.VITE_MATRIX_ACCESS_TOKEN as string | undefined) ?? "";
  const userId = (import.meta.env.VITE_MATRIX_USER_ID as string | undefined) ?? "";
  const deviceId = import.meta.env.VITE_MATRIX_DEVICE_ID as string | undefined;
  if (!baseUrl || !accessToken || !userId) return null;
  return { baseUrl, accessToken, userId, deviceId };
}

/**
 * Matrix client with IndexedDB sync store + legacy crypto store, then Rust crypto (WASM via matrix-js-sdk).
 */
export async function initializeMatrixClient(options: MatrixClientOptions): Promise<MatrixClient> {
  const { baseUrl, accessToken, userId, deviceId } = options;

  const store = new IndexedDBStore({
    indexedDB: window.indexedDB,
    localStorage: window.localStorage,
    dbName: "matrix-current-sync-store",
  });

  const cryptoStore = new IndexedDBCryptoStore(window.indexedDB, "matrix-current-crypto-store");

  const client = createClient({
    baseUrl,
    accessToken,
    userId,
    deviceId,
    store,
    cryptoStore,
    useAuthorizationHeader: true,
  });

  await store.startup();

  client.on(ClientEvent.Sync, (state: SyncState) => {
    if (state === SyncState.Prepared) {
      console.debug("[matrix] sync prepared; IndexedDB store hydrated.");
    } else if (state === SyncState.Error) {
      console.error("[matrix] sync error.");
    }
  });

  try {
    await client.initRustCrypto({ useIndexedDB: true });
  } catch (e) {
    console.warn("[matrix] initRustCrypto failed; encrypted rooms may not decrypt:", e);
  }

  await client.startClient({
    initialSyncLimit: 20,
    includeArchivedRooms: false,
  });

  return client;
}

/**
 * Enable encryption for a room (requires sufficient power level).
 */
export async function ensureRoomEncryption(client: MatrixClient, roomId: string): Promise<void> {
  if (client.getRoom(roomId)?.hasEncryptionStateEvent()) return;

  await client.sendStateEvent(roomId, EventType.RoomEncryption, {
    algorithm: "m.megolm.v1.aes-sha2",
  });
}
