<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useAppStore } from "@/stores/appStore";
import { usePantryStore } from "@/stores/pantryStore";
import JingBattery from "@/components/JingBattery.vue";
import {
  fetchFormula,
  checkOverride,
  mergeFormulas,
  type Prescription,
  type FormulaArchitectureEntry,
} from "@/services/alchemyApi";
import seedHerbs from "@/data/seed_herbs.json";
import seedFormulas from "@/data/seed_formulas.json";

type HerbRecord = {
  id: string;
  pinyin_name: string;
  common_name: string;
  safety_tier: number;
  [key: string]: unknown;
};

type FormulaOption = {
  id: string;
  pinyin_name: string;
  common_name?: string;
  english_name?: string;
  primary_pattern: string;
};

const store = useAppStore();
const pantryStore = usePantryStore();
const herbs = seedHerbs as HerbRecord[];
const formulaOptions = (seedFormulas as FormulaOption[]).map((f) => ({
  ...f,
  label: `${f.pinyin_name} (${f.primary_pattern})`,
  common_name: f.common_name ?? f.english_name ?? "",
}));

const currentPrescription = ref<Prescription | null>(null);
const activeCultivationTab = ref<"wei_dan" | "nei_dan">("wei_dan");
const mergedArchitecture = ref<FormulaArchitectureEntry[] | null>(null);
const formulaLoading = ref(false);
const formulaError = ref<string | null>(null);

const overrideSearch = ref("");
const overrideLoading = ref(false);
const overrideResult = ref<{ allowed: boolean; message: string } | null>(null);
const selectedHerbForOverride = ref<HerbRecord | null>(null);

const mergeModalOpen = ref(false);
const secondaryFormulaId = ref<string>("");
const mergeLoading = ref(false);
const mergeError = ref<string | null>(null);

const cabinetModalOpen = ref(false);
const cabinetSearch = ref("");

onMounted(() => {
  pantryStore.fetchInventory();
});

const displayArchitecture = computed(() => {
  return mergedArchitecture.value ?? currentPrescription.value?.wei_dan ?? currentPrescription.value?.architecture ?? [];
});

const architectureByRole = computed(() => {
  const arch = displayArchitecture.value;
  const groups: Record<string, FormulaArchitectureEntry[]> = {};
  for (const entry of arch) {
    const role = entry.role || "Other";
    if (!groups[role]) groups[role] = [];
    groups[role].push(entry);
  }
  const order = ["King (Jun)", "Minister (Chen)", "Assistant (Zuo)", "Envoy (Shi)"];
  return order.filter((r) => groups[r]).map((r) => ({ role: r, entries: groups[r]! }));
});

const filteredHerbs = computed(() => {
  const q = overrideSearch.value.trim().toLowerCase();
  if (!q) return herbs.slice(0, 20);
  return herbs.filter(
    (h) =>
      h.pinyin_name?.toLowerCase().includes(q) ||
      h.common_name?.toLowerCase().includes(q) ||
      h.id?.toLowerCase().includes(q)
  ).slice(0, 20);
});

const cabinetFilteredHerbs = computed(() => {
  const q = cabinetSearch.value.trim().toLowerCase();
  if (!q) return herbs;
  return herbs.filter(
    (h) =>
      h.pinyin_name?.toLowerCase().includes(q) ||
      h.common_name?.toLowerCase().includes(q) ||
      h.id?.toLowerCase().includes(q)
  );
});

function buildAstroState() {
  return {
    birthProfile: store.birthProfile,
    temporalHex: store.temporalHex,
    birthTemporalHex: store.birthTemporalHex,
    qimenChartHour: store.qimenChartHour,
    qimenChartDay: store.qimenChartDay,
    advanced_astro: {
      moment: store.advancedAstroMoment,
      birth: store.advancedAstroBirth,
    },
    zwds: store.zwdsMatrix,
  };
}

function buildUserState() {
  return {
    capacity_0_10: store.userCapacity,
    load_0_10: store.userLoad,
    sleep_quality_0_10: store.userSleepQuality,
    cognitive_noise_0_10: store.userCognitiveNoise,
    social_load_0_10: store.userSocialLoad,
    emotional_tone: store.userEmotionalTone,
    intent: {
      domain: store.intentDomain,
      goal_constraint: store.intentGoalConstraint,
    },
  };
}

async function loadFormula() {
  formulaLoading.value = true;
  formulaError.value = null;
  mergedArchitecture.value = null;
  try {
    const prescription = await fetchFormula(buildAstroState(), buildUserState());
    currentPrescription.value = prescription;
  } catch (e) {
    formulaError.value = e instanceof Error ? e.message : "Failed to load formula";
  } finally {
    formulaLoading.value = false;
  }
}

async function onSelectHerbForOverride(herb: HerbRecord) {
  if (!currentPrescription.value) return;
  selectedHerbForOverride.value = herb;
  overrideLoading.value = true;
  overrideResult.value = null;
  try {
    const res = await checkOverride(currentPrescription.value.id, herb.id);
    overrideResult.value = res;
  } catch (e) {
    overrideResult.value = {
      allowed: false,
      message: e instanceof Error ? e.message : "Safety check failed",
    };
  } finally {
    overrideLoading.value = false;
  }
}

function closeOverrideResult() {
  overrideResult.value = null;
  selectedHerbForOverride.value = null;
}

async function confirmMerge() {
  if (!currentPrescription.value || !secondaryFormulaId.value) return;
  mergeLoading.value = true;
  mergeError.value = null;
  try {
    const res = await mergeFormulas(
      currentPrescription.value.id,
      secondaryFormulaId.value,
      currentPrescription.value.id
    );
    mergedArchitecture.value = res.architecture;
    mergeModalOpen.value = false;
    secondaryFormulaId.value = "";
  } catch (e) {
    mergeError.value = e instanceof Error ? e.message : "Merge failed";
  } finally {
    mergeLoading.value = false;
  }
}

function clearMerge() {
  mergedArchitecture.value = null;
}
</script>

<template>
  <div class="alchemy-view">
    <div class="alchemy-header">
      <h1 class="alchemy-title">The Cauldron</h1>
      <p class="alchemy-subtitle">Alchemical formula from your Internal Weather</p>
      <div class="jing-row">
        <JingBattery />
      </div>
    </div>

    <div class="alchemy-actions">
      <button
        class="btn primary"
        :disabled="formulaLoading"
        @click="loadFormula"
      >
        {{ formulaLoading ? "Loading..." : "Brew Formula" }}
      </button>
      <button
        v-if="currentPrescription"
        class="btn"
        :disabled="mergeLoading"
        @click="mergeModalOpen = true"
      >
        Combine with Secondary Formula
      </button>
      <button
        v-if="mergedArchitecture"
        class="btn"
        @click="clearMerge"
      >
        Clear Merge
      </button>
      <button class="btn" @click="cabinetModalOpen = true">
        Manage Apothecary Cabinet
      </button>
    </div>

    <div v-if="formulaError" class="error-banner">{{ formulaError }}</div>

    <div v-if="currentPrescription" class="formula-card">
      <div class="formula-meta">
        <h2 class="formula-name">{{ currentPrescription.pinyin_name }}</h2>
        <p class="formula-common">{{ currentPrescription.common_name }}</p>
        <p class="formula-pattern">{{ currentPrescription.primary_pattern }}</p>
        <p v-if="currentPrescription.safety_note" class="formula-safety">{{ currentPrescription.safety_note }}</p>
      </div>

      <!-- Dual Cultivation Tabs -->
      <div class="cultivation-tabs">
        <button
          type="button"
          class="cultivation-tab"
          :class="{ active: activeCultivationTab === 'wei_dan' }"
          @click="activeCultivationTab = 'wei_dan'"
        >
          Wei Dan (The Cauldron)
        </button>
        <button
          type="button"
          class="cultivation-tab"
          :class="{ active: activeCultivationTab === 'nei_dan' }"
          @click="activeCultivationTab = 'nei_dan'"
        >
          Nei Dan (The Vessel)
        </button>
      </div>

      <!-- Wei Dan Tab: Herbal Hierarchy -->
      <div v-show="activeCultivationTab === 'wei_dan'" class="hierarchy">
        <div
          v-for="{ role, entries } in architectureByRole"
          :key="role"
          class="role-group"
          :class="{
            'role-king': role === 'King (Jun)',
            'role-minister': role === 'Minister (Chen)',
            'role-assistant': role === 'Assistant (Zuo)',
            'role-envoy': role === 'Envoy (Shi)',
          }"
        >
          <div class="role-label">{{ role }}</div>
          <div class="role-herbs">
            <div
              v-for="entry in entries"
              :key="entry.herb_id"
              class="herb-chip"
              :class="{ 'herb-chip-out-of-stock': !pantryStore.isHerbInStock(entry.herb_id) }"
            >
              <div class="herb-chip-main">
                <span class="herb-pinyin">{{ entry.pinyin_name }}</span>
                <span class="herb-dosage">{{ entry.dosage_percentage }}%</span>
                <span v-if="!pantryStore.isHerbInStock(entry.herb_id)" class="herb-badge-out">Out of Stock</span>
              </div>
              <span class="herb-purpose">{{ entry.purpose }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Nei Dan Tab: Internal Practice -->
      <div v-show="activeCultivationTab === 'nei_dan'" class="neidan-panel">
        <p class="neidan-hint">
          <em>Zhuang suggests performing this practice while your Wei Dan decoction simmers.</em>
        </p>
        <div v-if="currentPrescription.nei_dan" class="neidan-content">
          <h3 class="neidan-name">{{ currentPrescription.nei_dan.name }}</h3>
          <span class="neidan-type">{{ currentPrescription.nei_dan.type }}</span>
          <ol class="neidan-instructions">
            <li
              v-for="(step, i) in currentPrescription.nei_dan.instructions"
              :key="i"
              class="neidan-step"
            >
              {{ step }}
            </li>
          </ol>
          <div v-if="currentPrescription.nei_dan.safety_note" class="neidan-safety">
            {{ currentPrescription.nei_dan.safety_note }}
          </div>
        </div>
        <div v-else class="neidan-empty">
          No internal practice matched for this formula pattern.
        </div>
      </div>
    </div>

    <div v-else-if="!formulaLoading" class="empty-state">
      Click "Brew Formula" to generate a recommendation from your state.
    </div>

    <!-- Intuitive Override -->
    <div v-if="currentPrescription" class="override-section">
      <h3 class="override-title">Intuitive Override</h3>
      <p class="override-desc">Search and add an herb to check synergy</p>
      <input
        v-model="overrideSearch"
        type="text"
        class="override-input"
        placeholder="Search herbs (pinyin or common name)"
      />
      <div v-if="overrideLoading" class="override-loading">Checking safety...</div>
      <div v-else-if="overrideResult" class="override-result" :class="overrideResult.allowed ? 'allowed' : 'blocked'">
        <p>{{ overrideResult.message }}</p>
        <button class="btn small" @click="closeOverrideResult">Dismiss</button>
      </div>
      <div class="herb-list">
        <button
          v-for="herb in filteredHerbs"
          :key="herb.id"
          class="herb-option"
          :class="{ selected: selectedHerbForOverride?.id === herb.id }"
          @click="onSelectHerbForOverride(herb)"
        >
          {{ herb.pinyin_name }} · {{ herb.common_name }}
        </button>
      </div>
    </div>

    <!-- Apothecary Cabinet Modal -->
    <div v-if="cabinetModalOpen" class="modal-backdrop" @click.self="cabinetModalOpen = false">
      <div class="modal cabinet-modal">
        <h3>Manage Apothecary Cabinet</h3>
        <p class="modal-desc">Mark herbs you have in stock. Toggle each to add or remove from your inventory.</p>
        <input
          v-model="cabinetSearch"
          type="text"
          class="override-input"
          placeholder="Search herbs (pinyin or common name)"
        />
        <div v-if="pantryStore.loading" class="override-loading">Loading pantry...</div>
        <div v-else-if="pantryStore.error" class="error-banner">{{ pantryStore.error }}</div>
        <div class="cabinet-list">
          <div
            v-for="herb in cabinetFilteredHerbs"
            :key="herb.id"
            class="cabinet-row"
          >
            <span class="cabinet-herb-name">{{ herb.pinyin_name }} · {{ herb.common_name }}</span>
            <button
              type="button"
              class="cabinet-toggle"
              :class="{ active: pantryStore.isHerbInStock(herb.id) }"
              :aria-label="`${pantryStore.isHerbInStock(herb.id) ? 'Remove' : 'Add'} ${herb.pinyin_name} from stock`"
              @click="pantryStore.toggleHerb(herb.id)"
            >
              <span class="cabinet-toggle-knob" />
            </button>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="cabinetModalOpen = false">Done</button>
        </div>
      </div>
    </div>

    <!-- Merge Modal -->
    <div v-if="mergeModalOpen" class="modal-backdrop" @click.self="mergeModalOpen = false">
      <div class="modal">
        <h3>Combine with Secondary Formula</h3>
        <p class="modal-desc">Select a second pattern to merge using He Fang.</p>
        <select v-model="secondaryFormulaId" class="modal-select">
          <option value="">Choose formula...</option>
          <option
            v-for="f in formulaOptions"
            :key="f.id"
            :value="f.id"
            :disabled="f.id === currentPrescription?.id"
          >
            {{ f.label }}
          </option>
        </select>
        <div v-if="mergeError" class="error-banner">{{ mergeError }}</div>
        <div class="modal-actions">
          <button class="btn" @click="mergeModalOpen = false">Cancel</button>
          <button
            class="btn primary"
            :disabled="!secondaryFormulaId || mergeLoading"
            @click="confirmMerge"
          >
            {{ mergeLoading ? "Merging..." : "Merge" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.alchemy-view {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px;
  color: rgba(255, 255, 255, 0.9);
}

.alchemy-header {
  margin-bottom: 24px;
}

.alchemy-title {
  font-size: 24px;
  font-weight: 800;
  margin: 0 0 4px 0;
}

.alchemy-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.65);
  margin: 0 0 16px 0;
}

.jing-row {
  max-width: 200px;
}

.alchemy-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.btn {
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.08);
  color: inherit;
  cursor: pointer;
  font-size: 14px;
}

.btn.primary {
  background: rgba(255, 255, 255, 0.15);
  font-weight: 600;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.small {
  padding: 6px 12px;
  font-size: 12px;
}

.error-banner {
  padding: 12px;
  background: rgba(180, 50, 50, 0.3);
  border-radius: 10px;
  margin-bottom: 16px;
  font-size: 14px;
}

.formula-card {
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.15);
  margin-bottom: 24px;
}

.formula-meta {
  margin-bottom: 20px;
}

.formula-name {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.formula-common {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 4px 0;
}

.formula-pattern {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 8px 0;
}

.formula-safety {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.cultivation-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.cultivation-tab {
  flex: 1;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.65);
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}

.cultivation-tab:hover {
  color: rgba(255, 255, 255, 0.85);
}

.cultivation-tab.active {
  color: var(--color-daoist-jade);
  border-bottom-color: var(--color-daoist-jade);
}

.neidan-panel {
  padding-top: 8px;
}

.neidan-hint {
  font-size: 13px;
  font-style: italic;
  color: var(--color-daoist-muted);
  margin: 0 0 20px 0;
}

.neidan-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.neidan-name {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: var(--color-daoist-text);
}

.neidan-type {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-daoist-jade-muted);
}

.neidan-instructions {
  margin: 0;
  padding-left: 20px;
  padding-right: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.neidan-step {
  font-size: 15px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.88);
}

.neidan-safety {
  padding: 12px 14px;
  font-size: 13px;
  color: rgb(245 158 11);
  background: rgb(245 158 11 / 0.08);
  border: 1px solid rgb(245 158 11 / 0.5);
  border-radius: 8px;
}

.neidan-empty {
  padding: 24px;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

.hierarchy {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.role-group {
  padding: 12px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.role-king {
  background: rgba(180, 140, 60, 0.2);
  border-color: rgba(200, 160, 80, 0.4);
  transform: scale(1.02);
}

.role-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8px;
}

.role-herbs {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.herb-chip {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  font-size: 14px;
  border: 1px solid transparent;
}

.herb-chip-out-of-stock {
  border-color: rgb(245 158 11 / 0.5);
}

.herb-chip-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.herb-pinyin {
  font-weight: 600;
}

.herb-badge-out {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgb(245 158 11);
  padding: 2px 6px;
  border-radius: 4px;
  background: rgb(245 158 11 / 0.2);
}

.herb-dosage {
  color: rgba(255, 255, 255, 0.7);
}

.herb-purpose {
  grid-column: 1 / -1;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 15px;
}

.override-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.2);
}

.override-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.override-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 12px 0;
}

.override-input {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.25);
  background: rgba(0, 0, 0, 0.2);
  color: inherit;
  font-size: 14px;
  margin-bottom: 12px;
}

.override-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.override-loading {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 12px;
}

.override-result {
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 12px;
}

.override-result.allowed {
  background: rgba(50, 120, 80, 0.25);
  border: 1px solid rgba(80, 160, 100, 0.4);
}

.override-result.blocked {
  background: rgba(140, 50, 50, 0.25);
  border: 1px solid rgba(180, 80, 80, 0.4);
}

.herb-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.herb-option {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  background: rgba(0, 0, 0, 0.15);
  color: inherit;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
}

.herb-option:hover {
  background: rgba(0, 0, 0, 0.25);
}

.herb-option.selected {
  border-color: rgba(200, 160, 80, 0.5);
  background: rgba(180, 140, 60, 0.15);
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: rgb(30, 50, 90);
  border: 1px solid rgba(0, 0, 0, 0.3);
  border-radius: 16px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
}

.modal h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.modal-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 16px 0;
}

.modal-select {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.25);
  background: rgba(0, 0, 0, 0.2);
  color: inherit;
  font-size: 14px;
  margin-bottom: 16px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.cabinet-modal {
  max-width: 480px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.cabinet-modal .override-input {
  margin-bottom: 16px;
}

.cabinet-list {
  max-height: 320px;
  overflow-y: auto;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cabinet-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.cabinet-herb-name {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.cabinet-toggle {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
  padding: 2px;
  transition: background-color 0.2s, border-color 0.2s;
}

.cabinet-toggle:hover {
  border-color: rgba(255, 255, 255, 0.3);
}

.cabinet-toggle.active {
  background: var(--color-daoist-jade-muted);
  border-color: var(--color-daoist-jade);
}

.cabinet-toggle-knob {
  display: block;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  transition: transform 0.2s;
}

.cabinet-toggle.active .cabinet-toggle-knob {
  transform: translateX(22px);
}

@media (max-width: 640px) {
  .alchemy-view {
    padding: 16px;
  }

  .cultivation-tabs {
    flex-direction: column;
    gap: 0;
  }

  .cultivation-tab {
    text-align: left;
    border-bottom: none;
    border-left: 3px solid transparent;
  }

  .cultivation-tab.active {
    border-left-color: var(--color-daoist-jade);
    border-bottom-color: transparent;
  }

  .herb-chip {
    grid-template-columns: 1fr;
  }

  .neidan-instructions {
    padding-left: 18px;
  }
}

/* Mobile device widths (375px - 430px) */
@media (max-width: 430px) {
  .alchemy-view {
    padding: 16px;
    padding-left: calc(16px + env(safe-area-inset-left, 0px));
    padding-right: calc(16px + env(safe-area-inset-right, 0px));
  }

  .alchemy-actions {
    flex-direction: column;
  }

  .alchemy-actions .btn {
    width: 100%;
  }

  .herb-list {
    flex-direction: column;
  }

  .herb-option {
    width: 100%;
  }

  .modal {
    margin: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
    max-width: calc(100% - 32px);
  }
}
</style>
