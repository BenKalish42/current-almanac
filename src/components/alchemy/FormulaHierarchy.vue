<script setup lang="ts">
import { computed } from "vue";
import { useAlchemyStore } from "@/stores/alchemyStore";
import type { Herb } from "@/stores/alchemyStore";

const alchemyStore = useAlchemyStore();

const ROLE_TOOLTIPS: Record<string, string> = {
  "King (Jun)":
    "The King herb directly treats the primary pattern and has the strongest effect.",
  "Minister (Chen)":
    "The Minister supports the King and enhances its therapeutic direction.",
  "Assistant (Zuo)":
    "The Assistant moderates side effects and targets secondary symptoms.",
  "Envoy (Shi)":
    "The Envoy (Courier) guides the formula to the target meridian or tissue.",
  Unassigned:
    "Herbs not yet assigned a role. Assign roles to complete the Jun–Chen–Zuo–Shi structure.",
};

const tierConfig = [
  {
    role: "King (Jun)" as const,
    label: "King",
    sublabel: "Jun",
    classes:
      "bg-amber-500/10 border-amber-500/40 text-amber-200 font-bold",
    iconClasses: "text-amber-400",
  },
  {
    role: "Minister (Chen)" as const,
    label: "Minister",
    sublabel: "Chen",
    classes:
      "bg-amber-600/8 border-amber-600/30 text-amber-100/95 font-semibold",
    iconClasses: "text-amber-500/80",
  },
  {
    role: "Assistant (Zuo)" as const,
    label: "Assistant",
    sublabel: "Zuo",
    classes:
      "bg-daoist-elevated/60 border-white/10 text-daoist-text font-medium",
    iconClasses: "text-daoist-muted",
  },
  {
    role: "Envoy (Shi)" as const,
    label: "Envoy",
    sublabel: "Shi",
    classes:
      "bg-daoist-charcoal/50 border-white/5 text-daoist-muted text-sm",
    iconClasses: "text-daoist-subtle",
  },
  {
    role: "Unassigned" as const,
    label: "Unassigned",
    sublabel: "",
    classes:
      "bg-daoist-surface/40 border-dashed border-white/5 text-daoist-subtle text-sm italic",
    iconClasses: "text-daoist-subtle",
  },
];

const herbsByTier = computed(() => {
  const herbs = alchemyStore.activeFormula;
  const roles = alchemyStore.herbRoles;
  const groups: Record<string, Herb[]> = {
    "King (Jun)": [],
    "Minister (Chen)": [],
    "Assistant (Zuo)": [],
    "Envoy (Shi)": [],
    Unassigned: [],
  };

  for (const herb of herbs) {
    const role = roles[herb.id];
    const target = role && role in groups ? groups[role] : groups.Unassigned;
    if (target) target.push(herb);
  }

  return groups;
});

const showUnassigned = computed(() => (herbsByTier.value.Unassigned?.length ?? 0) > 0);

const ASSIGNABLE_ROLES = ["King (Jun)", "Minister (Chen)", "Assistant (Zuo)", "Envoy (Shi)"] as const;

function setRole(herbId: string, role: string | null) {
  alchemyStore.setHerbRole(herbId, role);
}

function displayPinyin(herb: Herb): string {
  if (herb.id.toLowerCase().includes("shadow")) return "Proprietary Ingredient";
  return herb.linguistics?.tonal_pinyin ?? herb.pinyin_name;
}

function displayCommonName(herb: Herb): string {
  if (herb.id.toLowerCase().includes("shadow")) return "Proprietary Ingredient";
  return herb.common_name;
}
</script>

<template>
  <div class="formula-hierarchy space-y-3">
    <template v-if="alchemyStore.activeFormula.length > 0">
      <div
        v-for="tier in tierConfig"
        :key="tier.role"
        v-show="tier.role === 'Unassigned' ? showUnassigned : true"
        class="rounded-lg border px-3 py-2 transition-colors"
        :class="tier.classes"
      >
        <div class="flex items-center justify-between gap-2 mb-2">
          <div class="flex items-center gap-1.5">
            <span v-if="tier.sublabel" class="text-daoist-subtle text-xs mr-1"
              >{{ tier.sublabel }}</span
            >
            <span>{{ tier.label }}</span>
            <div class="group relative inline-flex">
              <button
                type="button"
                class="p-0.5 rounded focus:outline-none focus:ring-1 focus:ring-daoist-jade/50"
                :class="tier.iconClasses"
                aria-label="Info"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </button>
              <div
                class="absolute left-0 bottom-full mb-1.5 hidden group-hover:block group-focus-within:block z-50 w-56 p-2.5 rounded-lg bg-daoist-elevated border border-white/10 text-xs text-daoist-text shadow-xl"
              >
                {{ ROLE_TOOLTIPS[tier.role] }}
              </div>
            </div>
          </div>
          <span
            v-if="herbsByTier[tier.role]?.length"
            class="text-xs text-daoist-subtle tabular-nums"
          >
            {{ (herbsByTier[tier.role] ?? []).length }}
          </span>
        </div>
        <ul v-if="(herbsByTier[tier.role] ?? []).length" class="space-y-1">
          <li
            v-for="herb in (herbsByTier[tier.role] ?? [])"
            :key="herb.id"
            class="flex items-center justify-between gap-2 py-1"
          >
            <div>
              <span class="font-medium">{{ displayPinyin(herb) }}</span>
              <span class="text-daoist-muted text-sm ml-2">{{ displayCommonName(herb) }}</span>
            </div>
            <select
              :value="alchemyStore.herbRoles[herb.id] ?? ''"
              class="text-xs rounded px-2 py-0.5 bg-daoist-charcoal/80 border border-white/10 text-daoist-muted focus:border-daoist-jade/50 focus:outline-none"
              @change="(e) => setRole(herb.id, (e.target as HTMLSelectElement).value || null)"
            >
              <option value="">Unassigned</option>
              <option
                v-for="r in ASSIGNABLE_ROLES"
                :key="r"
                :value="r"
              >
                {{ r }}
              </option>
            </select>
          </li>
        </ul>
        <p v-else class="text-daoist-subtle text-xs py-1">—</p>
      </div>
    </template>

    <p
      v-else
      class="text-daoist-subtle text-sm italic py-4 text-center"
    >
      No herbs in formula. Add herbs to see the hierarchy.
    </p>
  </div>
</template>
