<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import { useAlchemyStore } from "@/stores/alchemyStore";
import JingBattery from "@/components/alchemy/JingBattery.vue";
import HerbInventoryManager from "@/components/alchemy/HerbInventoryManager.vue";
import FormulaHierarchy from "@/components/alchemy/FormulaHierarchy.vue";
import MeridianVisualizer from "@/components/alchemy/MeridianVisualizer.vue";
import FormulaLibrary from "@/components/alchemy/FormulaLibrary.vue";

const alchemyStore = useAlchemyStore();
const route = useRoute();

// Dummy reactive state for JingBattery (placeholder until real cultivation metrics exist)
const yinLevel = ref(70);
const yangLevel = ref(45);
const activeTab = ref<"cauldron" | "library">("cauldron");

// Intelligence origin banner — shown when navigating from /ai with
// ?source=intelligence. We intentionally do NOT persist any custom-formula
// payload yet; future versions can read route.query.formulaId here.
const intelligenceBannerDismissed = ref(false);
const showIntelligenceBanner = computed(
  () => !intelligenceBannerDismissed.value && route.query.source === "intelligence"
);
</script>

<template>
  <div class="alchemy-view min-h-screen p-4 bg-daoist-bg">
    <!-- Intelligence-origin banner (handoff from /ai workbench) -->
    <div
      v-if="showIntelligenceBanner"
      class="mb-4 flex items-start gap-3 rounded-xl border border-daoist-jade/40 bg-daoist-jade/10 px-4 py-3"
      data-testid="intelligence-origin-banner"
    >
      <span aria-hidden="true" class="text-daoist-jade text-lg">◇</span>
      <div class="flex-1 min-w-0">
        <h3 class="text-sm font-semibold text-daoist-jade">Opened from Intelligence</h3>
        <p class="text-xs text-daoist-muted mt-0.5">
          Your alchemical context will land here. Custom-formula handoff from the Intelligence
          workbench is coming soon — for now, build or tune your formula manually in the Cauldron.
        </p>
      </div>
      <button
        type="button"
        class="text-daoist-muted hover:text-daoist-text text-xs px-2"
        aria-label="Dismiss banner"
        @click="intelligenceBannerDismissed = true"
      >
        ✕
      </button>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-2">
      <button
        type="button"
        class="rounded-lg px-3 py-1.5 text-sm border transition-colors"
        :class="
          activeTab === 'cauldron'
            ? 'border-daoist-jade/50 bg-daoist-jade/15 text-daoist-jade'
            : 'border-white/10 bg-daoist-surface text-daoist-muted hover:text-daoist-text'
        "
        @click="activeTab = 'cauldron'"
      >
        Cauldron
      </button>
      <button
        type="button"
        class="rounded-lg px-3 py-1.5 text-sm border transition-colors"
        :class="
          activeTab === 'library'
            ? 'border-daoist-jade/50 bg-daoist-jade/15 text-daoist-jade'
            : 'border-white/10 bg-daoist-surface text-daoist-muted hover:text-daoist-text'
        "
        @click="activeTab = 'library'"
      >
        Formula Library
      </button>
    </div>

    <!-- Top: NPDI Safety Banner -->
    <div
      v-if="alchemyStore.npdiWarnings.length > 0"
      class="mb-6 rounded-lg border-2 border-amber-500/60 bg-amber-950/40 px-4 py-3 shadow-lg"
    >
      <div class="flex items-start gap-2">
        <span class="text-amber-400 text-lg" aria-hidden="true">⚠</span>
        <div class="flex-1">
          <h3 class="font-semibold text-amber-200 mb-1">
            NPDI Safety: 18 Incompatibilities
          </h3>
          <ul class="text-sm text-amber-100/90 space-y-1">
            <li
              v-for="(w, i) in alchemyStore.npdiWarnings"
              :key="i"
              class="flex gap-2"
            >
              <span class="text-amber-400 shrink-0">•</span>
              <span>{{ w.message }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <FormulaLibrary v-if="activeTab === 'library'" />

    <!-- Main: Two-Column Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left Column: The Builder -->
      <div class="space-y-6">
        <section class="rounded-xl bg-daoist-surface border border-white/10 p-4">
          <h2 class="text-xs font-medium text-daoist-muted uppercase tracking-wider mb-3">
            Formula Builder
          </h2>
          <HerbInventoryManager />
        </section>

        <section class="rounded-xl bg-daoist-surface border border-white/10 p-4">
          <h2 class="text-xs font-medium text-daoist-muted uppercase tracking-wider mb-3">
            Jun–Chen–Zuo–Shi Hierarchy
          </h2>
          <FormulaHierarchy />
        </section>
      </div>

      <!-- Right Column: The Feedback Loop -->
      <div class="space-y-6">
        <section class="rounded-xl bg-daoist-surface border border-white/10 p-4">
          <h2 class="text-xs font-medium text-daoist-muted uppercase tracking-wider mb-3">
            Jing Reserves
          </h2>
          <JingBattery :yin-level="yinLevel" :yang-level="yangLevel" />
        </section>

        <section class="rounded-xl bg-daoist-surface border border-white/10 p-4">
          <h2 class="text-xs font-medium text-daoist-muted uppercase tracking-wider mb-3">
            Cultivation Analysis
          </h2>
          <div class="cultivation-analysis space-y-4">
            <div class="grid grid-cols-3 gap-4">
              <div class="rounded-lg bg-daoist-elevated/60 p-3 text-center">
                <span class="block text-2xl font-mono tabular-nums text-cyan-300">
                  {{ alchemyStore.formulaCultivationRating.jingScore }}
                </span>
                <span class="text-xs text-daoist-muted">Jing</span>
              </div>
              <div class="rounded-lg bg-daoist-elevated/60 p-3 text-center">
                <span class="block text-2xl font-mono tabular-nums text-amber-300">
                  {{ alchemyStore.formulaCultivationRating.qiScore }}
                </span>
                <span class="text-xs text-daoist-muted">Qi</span>
              </div>
              <div class="rounded-lg bg-daoist-elevated/60 p-3 text-center">
                <span class="block text-2xl font-mono tabular-nums text-rose-300">
                  {{ alchemyStore.formulaCultivationRating.shenScore }}
                </span>
                <span class="text-xs text-daoist-muted">Shen</span>
              </div>
            </div>
            <div class="rounded-lg bg-daoist-jade/10 border border-daoist-jade/30 px-3 py-2">
              <span class="text-sm text-daoist-jade font-medium">
                {{ alchemyStore.formulaCultivationRating.primaryEffect }}
              </span>
            </div>
          </div>
        </section>

        <section class="rounded-xl bg-daoist-surface border border-white/10 p-4">
          <h2 class="text-xs font-medium text-daoist-muted uppercase tracking-wider mb-3">
            Meridian Network
          </h2>
          <MeridianVisualizer />
        </section>
      </div>
    </div>
  </div>
</template>
