<script setup lang="ts">
import type { UIMessage } from "ai";
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useChat } from "@/composables/useChat";
import {
  DEFAULT_INTELLIGENCE_OPTIONS,
  ENSEMBLE_STRATEGIES,
  INTELLIGENCE_FAMILIES,
  findStrategy,
  summarizeRouting,
  type FamilyId,
  type IntelligenceOptions,
  type StrategyId,
} from "@/services/intelligenceConfig";
import { fetchModels, type ModelsResponse } from "@/services/intelligenceApi";

const router = useRouter();
const { messages, status, error, sendMessage, stop } = useChat();
const input = ref("");

const STORAGE_KEY = "current.intelligence.options.v1";

function loadStoredOptions(): IntelligenceOptions {
  if (typeof window === "undefined") return { ...DEFAULT_INTELLIGENCE_OPTIONS };
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_INTELLIGENCE_OPTIONS };
    const parsed = JSON.parse(raw) as Partial<IntelligenceOptions>;
    return {
      ...DEFAULT_INTELLIGENCE_OPTIONS,
      ...parsed,
      selectedModelsByFamily: {
        ...DEFAULT_INTELLIGENCE_OPTIONS.selectedModelsByFamily,
        ...(parsed.selectedModelsByFamily ?? {}),
      },
    };
  } catch {
    return { ...DEFAULT_INTELLIGENCE_OPTIONS };
  }
}

const intelligence = ref<IntelligenceOptions>(loadStoredOptions());
const remoteModels = ref<ModelsResponse | null>(null);
const workbenchOpen = ref(true);

watch(
  intelligence,
  (next) => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // ignore storage errors (private browsing, quota, etc.)
    }
  },
  { deep: true }
);

onMounted(async () => {
  remoteModels.value = await fetchModels();
});

const families = computed(() =>
  remoteModels.value?.families ??
  INTELLIGENCE_FAMILIES.map((f) => ({ ...f, keyConfigured: false }))
);

const strategies = computed(() => remoteModels.value?.strategies ?? ENSEMBLE_STRATEGIES);

const ragStatus = computed(() => remoteModels.value?.rag ?? { available: false, backend: "seed" as const });

const configuredCount = computed(() => families.value.filter((f) => f.keyConfigured).length);

const selectedFamily = computed(() => families.value.find((f) => f.id === intelligence.value.family));

const selectedSubtype = computed(() => {
  const fam = selectedFamily.value;
  if (!fam) return undefined;
  return fam.subtypes.find((s) => s.id === intelligence.value.model);
});

const selectedStrategyMeta = computed(() => findStrategy(intelligence.value.strategy));

const routingSummary = computed(() => summarizeRouting(intelligence.value));

const isReady = computed(() => status.value === "ready");
const isStreaming = computed(
  () => status.value === "submitted" || status.value === "streaming"
);
const hasError = computed(() => !!error.value);

function selectFamily(id: FamilyId) {
  intelligence.value.family = id;
  // Snap subtype to whatever the user previously chose for this family.
  const preferred = intelligence.value.selectedModelsByFamily[id];
  const fam = families.value.find((f) => f.id === id);
  const fallback = fam?.subtypes[0]?.id ?? "";
  intelligence.value.model = preferred ?? fallback;
}

function selectSubtype(subtypeId: string) {
  intelligence.value.model = subtypeId;
  intelligence.value.selectedModelsByFamily = {
    ...intelligence.value.selectedModelsByFamily,
    [intelligence.value.family]: subtypeId,
  };
}

function selectStrategy(id: StrategyId) {
  intelligence.value.strategy = id;
}

function toggleRag() {
  intelligence.value.ragEnabled = !intelligence.value.ragEnabled;
}

function handleSubmit(e?: Event) {
  e?.preventDefault();
  const text = input.value.trim();
  if (!text || !isReady.value) return;
  input.value = "";
  sendMessage({ text, intelligence: intelligence.value });
}

function getMessageText(msg: UIMessage) {
  return msg.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("");
}

const HANDOFF_RE = /OPEN_IN_ALCHEMY|```formula/i;
function shouldShowHandoff(msg: UIMessage): boolean {
  if (msg.role !== "assistant") return false;
  return HANDOFF_RE.test(getMessageText(msg));
}

function openInAlchemy() {
  router.push({ path: "/alchemy", query: { source: "intelligence" } });
}

function familyHint(f: { keyConfigured: boolean; envKeys: string[]; label: string }) {
  if (f.keyConfigured) return "Configured";
  const envs = f.envKeys.join(" or ");
  return `Missing key — set ${envs} in backend/.env`;
}
</script>

<template>
  <div class="ai-chat-view min-h-[calc(100dvh-120px)] flex flex-col bg-daoist-bg">
    <!-- Top bar: title + active routing summary -->
    <header class="px-4 pt-4 pb-2 border-b border-white/10">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="text-lg font-semibold text-daoist-text">Intelligence</h1>
          <p class="text-xs text-daoist-muted">
            {{ configuredCount }} / {{ families.length }} provider keys configured
          </p>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <span
            class="rounded-md border border-white/10 bg-daoist-surface px-2 py-1 text-xs font-mono text-daoist-muted"
            data-testid="active-routing"
          >
            {{ routingSummary }}
          </span>
          <button
            type="button"
            class="rounded-md border border-white/10 bg-daoist-surface px-3 py-1 text-xs text-daoist-muted hover:text-daoist-text transition-colors"
            @click="workbenchOpen = !workbenchOpen"
          >
            {{ workbenchOpen ? "Hide workbench" : "Show workbench" }}
          </button>
        </div>
      </div>
    </header>

    <div
      v-if="workbenchOpen"
      class="workbench p-4 space-y-4 border-b border-white/10"
      data-testid="intelligence-workbench"
    >
      <!-- Provider cards -->
      <section>
        <h2 class="text-xs font-medium uppercase tracking-wider text-daoist-muted mb-2">
          Model family
        </h2>
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            v-for="fam in families"
            :key="fam.id"
            type="button"
            class="text-left rounded-xl border bg-daoist-surface p-3 transition-colors hover:bg-daoist-elevated"
            :class="
              intelligence.family === fam.id
                ? [fam.accent.border, fam.accent.bg]
                : 'border-white/10'
            "
            :data-testid="`family-card-${fam.id}`"
            @click="selectFamily(fam.id)"
          >
            <div class="flex items-center justify-between">
              <span
                class="text-sm font-semibold"
                :class="intelligence.family === fam.id ? fam.accent.text : 'text-daoist-text'"
              >
                {{ fam.label }}
              </span>
              <span
                class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider"
                :class="
                  fam.keyConfigured
                    ? 'bg-daoist-jade/20 text-daoist-jade'
                    : 'bg-amber-500/15 text-amber-300'
                "
              >
                {{ fam.keyConfigured ? "Live" : "No key" }}
              </span>
            </div>
            <p class="mt-1 text-xs text-daoist-muted">{{ fam.provider }}</p>
            <p class="mt-2 text-xs text-daoist-muted">
              {{ fam.subtypes.length }} subtype{{ fam.subtypes.length === 1 ? "" : "s" }}
            </p>
            <p
              class="mt-2 text-[11px]"
              :class="fam.keyConfigured ? 'text-daoist-jade' : 'text-amber-300/80'"
            >
              {{ familyHint(fam) }}
            </p>
          </button>
        </div>
      </section>

      <!-- Subtype selector -->
      <section v-if="selectedFamily">
        <h2 class="text-xs font-medium uppercase tracking-wider text-daoist-muted mb-2">
          Subtype · {{ selectedFamily.label }}
        </h2>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="st in selectedFamily.subtypes"
            :key="st.id"
            type="button"
            class="rounded-lg border bg-daoist-surface px-3 py-1.5 text-sm transition-colors"
            :class="
              intelligence.model === st.id
                ? [selectedFamily.accent.border, selectedFamily.accent.bg, selectedFamily.accent.text]
                : 'border-white/10 text-daoist-muted hover:text-daoist-text'
            "
            :data-testid="`subtype-${selectedFamily.id}-${st.id}`"
            @click="selectSubtype(st.id)"
          >
            {{ st.label }}
          </button>
        </div>
        <p v-if="selectedSubtype" class="mt-2 text-xs text-daoist-muted">
          {{ selectedSubtype.description }}
          <span class="font-mono text-[11px] text-daoist-subtle">
            ({{ selectedSubtype.model }})
          </span>
        </p>
      </section>

      <!-- Ensemble strategies -->
      <section>
        <h2 class="text-xs font-medium uppercase tracking-wider text-daoist-muted mb-2">
          Ensemble strategy
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          <button
            v-for="s in strategies"
            :key="s.id"
            type="button"
            class="text-left rounded-lg border bg-daoist-surface p-3 transition-colors"
            :class="
              intelligence.strategy === s.id
                ? 'border-daoist-jade/60 bg-daoist-jade/10'
                : 'border-white/10 hover:bg-daoist-elevated'
            "
            :data-testid="`strategy-${s.id}`"
            @click="selectStrategy(s.id as StrategyId)"
          >
            <div class="flex items-center justify-between">
              <span
                class="text-sm font-medium"
                :class="intelligence.strategy === s.id ? 'text-daoist-jade' : 'text-daoist-text'"
              >
                {{ s.label }}
              </span>
              <span
                v-if="s.needsMultipleProviders && configuredCount < 2"
                class="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] uppercase tracking-wider text-amber-300"
                title="Works best with 2+ providers configured."
              >
                Multi
              </span>
            </div>
            <p class="mt-1 text-xs text-daoist-muted leading-snug">{{ s.description }}</p>
          </button>
        </div>
      </section>

      <!-- KnowledgeRAG toggle + active routing summary -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div class="rounded-xl border border-white/10 bg-daoist-surface p-3">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-semibold text-daoist-text">KnowledgeRAG</h3>
              <p class="text-xs text-daoist-muted">
                Inject Neo4j herb / formula context into the system prompt.
              </p>
            </div>
            <button
              type="button"
              role="switch"
              :aria-checked="intelligence.ragEnabled"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              :class="intelligence.ragEnabled ? 'bg-daoist-jade' : 'bg-white/15'"
              data-testid="rag-toggle"
              @click="toggleRag"
            >
              <span
                class="inline-block h-4 w-4 rounded-full bg-white transition-transform"
                :class="intelligence.ragEnabled ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>
          <p class="mt-2 text-xs">
            <span
              class="rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider"
              :class="
                ragStatus.available
                  ? 'bg-daoist-jade/20 text-daoist-jade'
                  : 'bg-white/10 text-daoist-muted'
              "
            >
              {{ ragStatus.available ? "Neo4j connected" : "Seed fallback" }}
            </span>
            <span class="ml-2 text-daoist-muted">
              {{
                ragStatus.available
                  ? "Bolt connection alive — graph-grounded retrieval."
                  : "Neo4j unreachable; using seed herb / formula data instead."
              }}
            </span>
          </p>
        </div>

        <div class="rounded-xl border border-white/10 bg-daoist-surface p-3">
          <h3 class="text-sm font-semibold text-daoist-text">Active routing</h3>
          <pre
            class="mt-2 whitespace-pre-wrap break-words font-mono text-xs text-daoist-muted leading-relaxed"
data-testid="routing-summary"
          ><code>family   : {{ selectedFamily?.label ?? intelligence.family }}
subtype  : {{ selectedSubtype?.label ?? intelligence.model }}  ({{ selectedSubtype?.model ?? '—' }})
strategy : {{ selectedStrategyMeta?.label ?? intelligence.strategy }}
RAG      : {{ intelligence.ragEnabled ? 'on' : 'off' }} ({{ ragStatus.backend }})</code></pre>
        </div>
      </section>
    </div>

    <!-- Chat messages -->
    <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
      <div v-if="messages.length === 0" class="m-auto max-w-sm text-center text-daoist-muted">
        <p class="text-sm">
          Pick a model family and ensemble strategy above, then ask anything about
          Daoist astrology, the present moment, or your active formula.
        </p>
      </div>

      <div
        v-for="msg in messages"
        :key="msg.id"
        class="max-w-[88%] rounded-xl px-4 py-3 break-words"
        :class="
          msg.role === 'user'
            ? 'self-end bg-daoist-elevated/90 border border-white/10 text-daoist-text'
            : 'self-start bg-daoist-surface border-l-4 border-daoist-jade text-daoist-text'
        "
      >
        <span
          class="block text-[11px] font-semibold uppercase tracking-wider mb-1"
          :class="msg.role === 'user' ? 'text-daoist-muted' : 'text-daoist-jade-muted'"
        >
          {{ msg.role === "user" ? "You" : "Intelligence" }}
        </span>
        <div class="text-[15px] leading-relaxed whitespace-pre-wrap">
          {{ getMessageText(msg) }}
        </div>
        <div v-if="shouldShowHandoff(msg)" class="mt-3">
          <button
            type="button"
            class="rounded-lg border border-daoist-gold/60 bg-daoist-gold/10 px-3 py-1.5 text-xs font-medium text-daoist-gold hover:bg-daoist-gold/20 transition-colors"
            data-testid="open-in-alchemy"
            @click="openInAlchemy"
          >
            Open in Alchemy →
          </button>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="hasError"
      class="mx-4 mb-2 rounded-lg border border-rose-500/40 bg-rose-950/40 px-3 py-2 text-sm text-rose-200"
    >
      Something went wrong streaming the response. Try again.
    </div>

    <!-- Input -->
    <div
      class="sticky bottom-0 px-4 pt-3 pb-[calc(0.75rem+env(safe-area-inset-bottom,0px))] bg-daoist-bg border-t border-white/10"
    >
      <form class="flex flex-col gap-2" @submit="handleSubmit">
        <input
          v-model="input"
          type="text"
          class="w-full rounded-lg border border-white/10 bg-daoist-surface px-4 py-3 text-base text-daoist-text placeholder:text-daoist-muted focus:border-daoist-jade-muted focus:outline-none disabled:opacity-60"
          placeholder="Ask the workbench…"
          :disabled="!isReady"
          autocomplete="off"
        />
        <div class="flex justify-end gap-2">
          <button
            v-if="isStreaming"
            type="button"
            class="rounded-lg border border-daoist-gold-muted bg-transparent px-4 py-2 text-sm font-medium text-daoist-gold hover:bg-daoist-gold/10"
            @click="stop"
          >
            Stop
          </button>
          <button
            type="submit"
            class="rounded-lg bg-daoist-jade px-4 py-2 text-sm font-semibold text-[#0d1520] hover:bg-daoist-jade-muted disabled:opacity-50"
            :disabled="!input.trim() || !isReady"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
