<script setup lang="ts">
/**
 * AlchemicalGraph — lightweight node-link viewer onto the local triplestore.
 *
 * Tailwind/SVG, no Cytoscape, no force-directed runtime libs.
 * The layout is a fixed radial: center node + spokes. For richer graphs
 * we'll hand off to a worker-based force layout in v1.1.
 *
 * Reads the active subgraph (Earth) for the most recent biometric state.
 * If the store is empty, renders a quiet empty-state.
 */

import { computed, onMounted, ref } from "vue";
import { getTriplestore } from "@/services/graph/triplestore";
import { traverseEarth } from "@/services/graph/ragTraversal";

type LayoutNode = {
  id: string;
  label: string;
  caption: string;
  x: number;
  y: number;
  ring: "center" | "inner" | "outer";
};

type LayoutEdge = {
  fromId: string;
  toId: string;
  type: string;
};

const SIZE = 420;
const CENTER = SIZE / 2;
const INNER_R = 90;
const OUTER_R = 175;

const layoutNodes = ref<LayoutNode[]>([]);
const layoutEdges = ref<LayoutEdge[]>([]);
const empty = ref(true);

function caption(label: string, props: Record<string, unknown>): string {
  if (label === "SovereignNode") return "User";
  if (label === "BiometricState") return "Now";
  if (label === "Pathology") return String(props.nature ?? "Pathology");
  if (label === "Botanical") return String(props.tcm_name ?? props.pinyin_name ?? "Herb");
  if (label === "Formula") return String(props.name ?? "Formula");
  if (label === "OntologyVector") return String(props.name ?? "Vector");
  if (label === "TemporalPillar") return String(props.ganzhi ?? "Pillar");
  return label;
}

function layout() {
  const store = getTriplestore();
  const sub = traverseEarth(store);
  if (!sub.user && !sub.biometric) {
    empty.value = true;
    return;
  }
  empty.value = false;

  const nodes: LayoutNode[] = [];
  const edges: LayoutEdge[] = [];

  // Center: biometric (or user if no biometric).
  const center = sub.biometric ?? sub.user;
  if (center) {
    nodes.push({
      id: center.id,
      label: center.label,
      caption: caption(center.label, center.properties),
      x: CENTER,
      y: CENTER,
      ring: "center",
    });
  }

  // Inner ring: pathologies.
  const inner = sub.pathologies;
  inner.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / Math.max(1, inner.length) - Math.PI / 2;
    nodes.push({
      id: n.id,
      label: n.label,
      caption: caption(n.label, n.properties),
      x: CENTER + INNER_R * Math.cos(angle),
      y: CENTER + INNER_R * Math.sin(angle),
      ring: "inner",
    });
    if (center) edges.push({ fromId: center.id, toId: n.id, type: "MATCHES_SYNDROME" });
  });

  // Outer ring: botanicals + formulas, distributed evenly around the full circle.
  const outer = [...sub.botanicals, ...sub.formulas];
  outer.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / Math.max(1, outer.length) + Math.PI / 4;
    nodes.push({
      id: n.id,
      label: n.label,
      caption: caption(n.label, n.properties),
      x: CENTER + OUTER_R * Math.cos(angle),
      y: CENTER + OUTER_R * Math.sin(angle),
      ring: "outer",
    });
    // Connect each treater to the first matching pathology (best-effort).
    if (inner[0]) {
      edges.push({ fromId: n.id, toId: inner[0].id, type: "TREATS" });
    }
  });

  layoutNodes.value = nodes;
  layoutEdges.value = edges;
}

const nodeById = computed(() => {
  const m: Record<string, LayoutNode> = {};
  for (const n of layoutNodes.value) m[n.id] = n;
  return m;
});

onMounted(layout);
</script>

<template>
  <section class="rounded-xl border border-white/10 p-4">
    <header class="mb-3 flex items-baseline justify-between">
      <div>
        <h3 class="text-xs font-medium uppercase tracking-wider text-slate-400">
          Alchemical Graph
        </h3>
        <p class="mt-1 text-xs text-slate-500">
          Local triplestore subgraph for the active configuration.
        </p>
      </div>
      <button
        type="button"
        class="rounded border border-white/10 px-2 py-1 text-xs text-slate-300 hover:bg-white/5"
        @click="layout"
      >
        Refresh
      </button>
    </header>

    <div v-if="empty" class="rounded border border-dashed border-white/10 p-6 text-center text-xs text-slate-500">
      No active subgraph. Triplestore is empty.
    </div>

    <svg
      v-else
      :viewBox="`0 0 ${SIZE} ${SIZE}`"
      role="img"
      aria-label="Alchemical Graph"
      class="h-auto w-full"
    >
      <!-- Edges -->
      <g stroke="currentColor" stroke-width="1" class="text-slate-500/40">
        <line
          v-for="(e, i) in layoutEdges"
          :key="i"
          :x1="nodeById[e.fromId]?.x"
          :y1="nodeById[e.fromId]?.y"
          :x2="nodeById[e.toId]?.x"
          :y2="nodeById[e.toId]?.y"
        />
      </g>

      <!-- Nodes -->
      <g>
        <g v-for="n in layoutNodes" :key="n.id">
          <circle
            :cx="n.x"
            :cy="n.y"
            :r="n.ring === 'center' ? 18 : n.ring === 'inner' ? 14 : 10"
            :class="
              n.ring === 'center'
                ? 'fill-amber-500/30 stroke-amber-400/80'
                : n.ring === 'inner'
                  ? 'fill-rose-500/20 stroke-rose-400/80'
                  : 'fill-emerald-500/15 stroke-emerald-400/80'
            "
            stroke-width="1.5"
          />
          <text
            :x="n.x"
            :y="n.y + (n.ring === 'center' ? 32 : 24)"
            text-anchor="middle"
            class="fill-slate-200 text-[10px]"
          >
            {{ n.caption }}
          </text>
        </g>
      </g>
    </svg>
  </section>
</template>
