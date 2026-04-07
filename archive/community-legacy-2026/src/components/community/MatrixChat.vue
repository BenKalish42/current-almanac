<template>
  <div class="matrix-shell">
    <div v-if="!config" class="setup-card">
      <h2 class="setup-title">Matrix (E2EE)</h2>
      <p class="setup-copy">
        Add these to <code class="code">.env</code> and restart the dev server to sync rooms:
      </p>
      <ul class="setup-list">
        <li><code class="code">VITE_MATRIX_HOMESERVER_URL</code> — e.g. <code class="code">https://matrix.example.org</code></li>
        <li><code class="code">VITE_MATRIX_ACCESS_TOKEN</code></li>
        <li><code class="code">VITE_MATRIX_USER_ID</code> — e.g. <code class="code">@you:example.org</code></li>
        <li><code class="code">VITE_MATRIX_DEVICE_ID</code> (optional)</li>
      </ul>
      <p class="setup-note">Rust crypto (WASM) loads via <code class="code">@matrix-org/matrix-sdk-crypto-wasm</code>; encrypted rooms need a successful <code class="code">initRustCrypto</code>.</p>
    </div>

    <template v-else>
      <div v-if="initError" class="setup-card error">
        <h2 class="setup-title">Could not connect</h2>
        <p class="setup-copy">{{ initError }}</p>
      </div>

      <div v-else class="chat-layout">
        <aside class="sidebar">
          <div class="sidebar-head">Inner Sanctum</div>
          <div class="sidebar-body">
            <div v-if="loading" class="muted center-pad">Syncing…</div>
            <ul v-else class="room-list">
              <li
                v-for="room in rooms"
                :key="room.roomId"
                class="room-item"
                :class="{ selected: selectedRoom?.roomId === room.roomId }"
                @click="selectRoom(room)"
              >
                <span class="room-name">{{ room.name }}</span>
                <span v-if="room.isEncrypted" class="lock" title="Encrypted">🔒</span>
              </li>
            </ul>
          </div>
        </aside>

        <section class="main-pane">
          <template v-if="selectedRoom">
            <header class="thread-head">
              <h2 class="thread-title">{{ selectedRoom.name }}</h2>
              <span v-if="selectedRoom.isEncrypted" class="badge ok">Encrypted</span>
              <span v-else class="badge warn">Not encrypted</span>
            </header>

            <div class="messages">
              <div v-for="msg in messages" :key="msg.id" class="msg-row" :class="{ own: msg.isOwn }">
                <div class="msg-meta">{{ msg.sender }}</div>
                <div class="msg-bubble">{{ msg.body }}</div>
              </div>
            </div>

            <footer class="composer">
              <input
                v-model="newMessage"
                type="text"
                class="composer-input"
                placeholder="Speak your truth…"
                @keyup.enter="sendMessage"
              />
              <button type="button" class="composer-send" @click="sendMessage">Send</button>
            </footer>
          </template>
          <div v-else class="muted empty-main">Select a room</div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import {
  initializeMatrixClient,
  getMatrixConfigFromEnv,
  type MatrixClientOptions,
} from "@/services/matrix/matrixClient";
import {
  ClientEvent,
  EventType,
  RoomEvent,
  SyncState,
  MsgType,
  type MatrixClient,
  type MatrixEvent,
  type Room,
} from "matrix-js-sdk";

const config = ref<MatrixClientOptions | null>(getMatrixConfigFromEnv());
const client = ref<MatrixClient | null>(null);
const loading = ref(!!config.value);
const initError = ref<string | null>(null);
const rooms = ref<{ roomId: string; name: string; isEncrypted: boolean }[]>([]);
const selectedRoom = ref<{ roomId: string; name: string; isEncrypted: boolean } | null>(null);
const messages = ref<{ id: string; sender: string; body: string; isOwn: boolean }[]>([]);
const newMessage = ref("");

function loadRooms() {
  const c = client.value;
  if (!c) return;
  rooms.value = c.getRooms().map((room: Room) => ({
    roomId: room.roomId,
    name: room.name || "Unnamed room",
    isEncrypted: room.hasEncryptionStateEvent(),
  }));
}

function formatMessage(event: MatrixEvent) {
  const content = event.getContent() as { body?: string };
  return {
    id: event.getId() ?? `local-${Math.random().toString(36).slice(2)}`,
    sender: event.getSender() ?? "Unknown",
    body: typeof content.body === "string" ? content.body : "",
    isOwn: event.getSender() === client.value?.getUserId(),
  };
}

function selectRoom(room: { roomId: string; name: string; isEncrypted: boolean }) {
  selectedRoom.value = room;
  messages.value = [];
  const c = client.value;
  if (!c) return;
  const matrixRoom = c.getRoom(room.roomId);
  if (!matrixRoom) return;
  const timeline = matrixRoom.getLiveTimeline().getEvents();
  messages.value = timeline
    .filter((e: MatrixEvent) => e.getType() === EventType.RoomMessage)
    .map(formatMessage);
}

onMounted(async () => {
  if (!config.value) {
    loading.value = false;
    return;
  }
  try {
    client.value = await initializeMatrixClient(config.value);
    client.value.on(ClientEvent.Sync, (state: SyncState) => {
      if (state === SyncState.Prepared) {
        loading.value = false;
        loadRooms();
      }
    });
    client.value.on(
      RoomEvent.Timeline,
      (event: MatrixEvent, room: Room | undefined, toStartOfTimeline: boolean | undefined) => {
        if (!room || !selectedRoom.value || room.roomId !== selectedRoom.value.roomId) return;
        if (toStartOfTimeline) return;
        if (event.getType() !== EventType.RoomMessage) return;
        messages.value.push(formatMessage(event));
      },
    );
  } catch (err) {
    initError.value = err instanceof Error ? err.message : String(err);
    loading.value = false;
  }
});

onUnmounted(() => {
  client.value?.stopClient();
});

async function sendMessage() {
  const text = newMessage.value.trim();
  const c = client.value;
  const room = selectedRoom.value;
  if (!text || !c || !room) return;
  try {
    await c.sendEvent(room.roomId, EventType.RoomMessage, {
      msgtype: MsgType.Text,
      body: text,
    });
    newMessage.value = "";
  } catch (e) {
    console.error("[matrix] send failed", e);
  }
}
</script>

<style scoped>
.matrix-shell {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 420px;
  border: 1px solid var(--b2);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.12);
}

.setup-card {
  padding: 24px;
  max-width: 40rem;
  margin: 0 auto;
  text-align: left;
}
.setup-card.error {
  border-bottom: 1px solid rgba(239, 68, 68, 0.35);
}
.setup-title {
  margin: 0 0 12px;
  font-size: 18px;
  color: var(--txt);
}
.setup-copy,
.setup-note {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--muted);
  line-height: 1.5;
}
.setup-list {
  margin: 0 0 16px;
  padding-left: 1.25rem;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
}
.code {
  font-size: 12px;
  background: rgba(0, 0, 0, 0.35);
  padding: 2px 6px;
  border-radius: 6px;
  color: var(--txt);
}

.chat-layout {
  display: flex;
  flex: 1;
  min-height: 420px;
}

.sidebar {
  width: 32%;
  max-width: 280px;
  border-right: 1px solid var(--b2);
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}
.sidebar-head {
  padding: 14px;
  font-weight: 700;
  text-align: center;
  border-bottom: 1px solid var(--b2);
  color: var(--txt);
}
.sidebar-body {
  flex: 1;
  overflow-y: auto;
}
.center-pad {
  padding: 20px;
  text-align: center;
}
.room-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.room-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--b);
  color: var(--txt);
  font-size: 14px;
}
.room-item:hover {
  background: rgba(255, 255, 255, 0.04);
}
.room-item.selected {
  background: rgba(255, 255, 255, 0.08);
}
.room-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.lock {
  flex-shrink: 0;
  font-size: 12px;
}

.main-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: rgba(0, 0, 0, 0.08);
}
.thread-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--b2);
  background: rgba(0, 0, 0, 0.15);
}
.thread-title {
  margin: 0;
  flex: 1;
  font-size: 17px;
  color: var(--txt);
}
.badge {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
}
.badge.ok {
  color: #4ade80;
  border: 1px solid rgba(74, 222, 128, 0.45);
}
.badge.warn {
  color: #f87171;
  border: 1px solid rgba(248, 113, 113, 0.45);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.msg-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 85%;
}
.msg-row.own {
  align-self: flex-end;
  align-items: flex-end;
}
.msg-meta {
  font-size: 11px;
  color: var(--muted);
  margin-bottom: 4px;
}
.msg-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.45;
  background: var(--b2);
  color: var(--txt);
}
.msg-row.own .msg-bubble {
  background: rgba(74, 155, 122, 0.35);
  border: 1px solid rgba(74, 155, 122, 0.45);
}

.composer {
  display: flex;
  gap: 0;
  padding: 12px 14px;
  border-top: 1px solid var(--b2);
  background: rgba(0, 0, 0, 0.2);
}
.composer-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--b2);
  border-right: none;
  border-radius: 10px 0 0 10px;
  background: rgba(0, 0, 0, 0.25);
  color: var(--txt);
  font-size: 14px;
  outline: none;
}
.composer-input:focus {
  border-color: rgba(74, 155, 122, 0.5);
}
.composer-send {
  padding: 10px 18px;
  border: 1px solid rgba(74, 155, 122, 0.55);
  border-radius: 0 10px 10px 0;
  background: rgba(74, 155, 122, 0.25);
  color: var(--txt);
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}
.composer-send:hover {
  background: rgba(74, 155, 122, 0.4);
}

.muted {
  color: var(--muted);
  font-size: 14px;
}
.empty-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 720px) {
  .chat-layout {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    max-width: none;
    max-height: 200px;
    border-right: none;
    border-bottom: 1px solid var(--b2);
  }
}
</style>
