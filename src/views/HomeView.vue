<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import HexagramLines from "@/components/HexagramLines.vue";
import HexagramModal from "@/components/HexagramModal.vue";
import QimenChart from "@/components/QimenChart.vue";
import { parseGanZhi } from "@/core/ganzhi";
import { useAppStore } from "@/stores/appStore";
import hexagramSummaries from "@/data/hexagramSummaries.json";

type HexagramSummary = {
  daoist: string;
  buddhist: string;
  confucian: string;
  humanDesign: string;
  geneKeys: string;
};
type HexagramSummaryMap = Record<string, HexagramSummary>;

const store = useAppStore();
const hexSummaryMap = hexagramSummaries as HexagramSummaryMap;

const qimenScope = ref<"hour" | "day">("hour");
const qimenChart = computed(() =>
  qimenScope.value === "hour" ? store.qimenChartHour : store.qimenChartDay
);

const isHexModalOpen = ref(false);
const selectedHexNum = ref<number | null>(null);
const selectedHexNameCn = ref<string | null>(null);
const selectedHexSummary = computed(() => {
  const num = selectedHexNum.value;
  if (!num) return null;
  return hexSummaryMap[String(num)] ?? null;
});
const selectedHexDisplayName = computed(
  () => hexNameShort(selectedHexNum.value, selectedHexNameCn.value) || "—"
);

const HEX_NAME_CN_SHORT: string[] = [
  "", "乾", "坤", "屯", "蒙", "需", "讼", "师", "比", "小畜", "履", "泰", "否",
  "同人", "大有", "谦", "豫", "随", "蛊", "临", "观", "噬嗑", "贲", "剥", "复",
  "无妄", "大畜", "颐", "大过", "坎", "离", "咸", "恒", "遯", "大壮", "晋", "明夷",
  "家人", "睽", "蹇", "解", "损", "益", "夬", "姤", "萃", "升", "困", "井", "革",
  "鼎", "震", "艮", "渐", "归妹", "丰", "旅", "巽", "兑", "涣", "节", "中孚",
  "小过", "既济", "未济",
];

function hexNameShort(num: number | null, fallback: string | null) {
  if (!num || num < 1 || num >= HEX_NAME_CN_SHORT.length) return fallback ?? "—";
  return HEX_NAME_CN_SHORT[num];
}

function openHexModal(hex: { num: number | null; nameCn: string | null }) {
  if (!hex?.num) return;
  selectedHexNum.value = hex.num;
  selectedHexNameCn.value = hex.nameCn ?? null;
  isHexModalOpen.value = true;
}

function closeHexModal() {
  isHexModalOpen.value = false;
}

function formatGanZhiLines(gz: string | null) {
  const parsed = parseGanZhi(gz ?? "");
  if (!parsed.stem || !parsed.branch) return gz ?? "—";
  const chars = `${parsed.stem.char}${parsed.branch.char}`;
  const english = `${parsed.stem.element} ${parsed.stem.yinYang} ${parsed.branch.animal}`;
  const emojis = `${parsed.stem.elementEmoji}${parsed.stem.yinYangEmoji}${parsed.branch.animalEmoji}`;
  return `${chars}\n${english}\n${emojis}`;
}

function getLocalTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "unknown";
}

async function copyInterpretation() {
  const text = store.interpretationPlaceholder;
  if (!text) return;
  await navigator.clipboard.writeText(text);
}

let localSyncTimer: number | null = null;

onMounted(() => {
  store.loadFromStorage();
  store.syncLocalTimeNow(true);
  store.timezoneLabel = getLocalTimezone();
  void store.hydrateFromGeolocation();
  localSyncTimer = window.setInterval(() => {
    store.syncLocalTimeNow();
    store.timezoneLabel = getLocalTimezone();
  }, 60_000);
});

onUnmounted(() => {
  if (localSyncTimer) window.clearInterval(localSyncTimer);
});
</script>

<template>
  <div class="appRoot">
    <div class="appHeader">
      <div class="title">Current (v0)</div>
      <div class="subtitle">You're in the Present... Would you like to get in the Current?</div>
      <div class="sub">Stored locally. No accounts. Descriptive only.</div>
    </div>

    <div class="wrap">
      <aside class="side">
        <div class="controls">
          <label class="lbl">
            Location (auto)
            <input class="input" type="text" :value="store.location || 'unknown'" readonly />
          </label>
          <button class="btn" @click="store.hydrateFromGeolocation">Use current location</button>
          <label class="lbl">
            Timezone
            <input class="input" type="text" :value="store.timezoneLabel" readonly />
          </label>
          <button class="btn primary" @click="store.generate">Generate Reading</button>
          <button class="btn" @click="store.clearLog">Clear Log</button>
        </div>

        <div class="sectionHdr">User Intent</div>
        <div class="controls">
          <label class="lbl">
            Domain
            <input class="input" type="text" placeholder="e.g., work, relationships" v-model="store.intentDomain" />
          </label>
          <label class="lbl">
            Goal Constraint
            <input class="input" type="text" placeholder="One sentence" v-model="store.intentGoalConstraint" />
          </label>
        </div>

        <div class="sectionHdr">User State (Optional)</div>
        <div class="controls">
          <label class="lbl">
            Capacity (0-10)
            <input class="input" type="number" min="0" max="10" step="1" v-model.number="store.userCapacity" />
          </label>
          <label class="lbl">
            Load (0-10)
            <input class="input" type="number" min="0" max="10" step="1" v-model.number="store.userLoad" />
          </label>
          <label class="lbl">
            Sleep Quality (0-10)
            <input class="input" type="number" min="0" max="10" step="1" v-model.number="store.userSleepQuality" />
          </label>
          <label class="lbl">
            Cognitive Noise (0-10)
            <input class="input" type="number" min="0" max="10" step="1" v-model.number="store.userCognitiveNoise" />
          </label>
          <label class="lbl">
            Social Load (0-10)
            <input class="input" type="number" min="0" max="10" step="1" v-model.number="store.userSocialLoad" />
          </label>
          <label class="lbl">
            Emotional Tone
            <input class="input" type="text" placeholder="One sentence" v-model="store.userEmotionalTone" />
          </label>
        </div>

        <div class="sectionHdr">Recent</div>
        <div class="recent">
          <div v-if="store.sortedLog.length === 0" class="empty">No readings yet.</div>
          <button
            v-for="r in store.sortedLog"
            :key="r.id"
            class="item"
            :class="{ active: store.activeReading?.id === r.id }"
            @click="store.setActiveReading(r)"
          >
            <div class="itemTitle">{{ r.inputs.dateISO }} {{ r.inputs.timeHHMM }}</div>
            <div class="itemSub">{{ r.inputs.location || "—" }}</div>
            <div class="itemMeta">{{ r.meta.silence ? "Silence" : `Signal: ${r.meta.signalStrength}` }}</div>
          </button>
        </div>
      </aside>

      <main class="main">
        <div class="card">
          <div class="topSections">
            <section class="panel">
              <div class="panelHeader">
                <div class="secTitle">Past (Birth)</div>
                <div class="panelControls">
                  <label class="inlineLbl">
                    Birth datetime
                    <input class="input inlineInput" type="datetime-local" v-model="store.birthDatetimeLocal" />
                  </label>
                  <label class="inlineLbl">
                    BaZi sect
                    <select class="input inlineInput inlineSelect" v-model.number="store.birthSect">
                      <option :value="1">sect 1</option>
                      <option :value="2">sect 2</option>
                    </select>
                  </label>
                </div>
              </div>
              <div v-if="store.birthTemporalHex" class="pillarGrid">
                <div class="pillarBox">
                  <div class="pillarLabel">Year</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.birthTemporalHex.year.ganzhi) }}</div>
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.birthTemporalHex.year.hex.num }"
                    role="button"
                    :tabindex="store.birthTemporalHex.year.hex.num ? 0 : -1"
                    :aria-disabled="!store.birthTemporalHex.year.hex.num"
                    @click="openHexModal(store.birthTemporalHex.year.hex)"
                    @keydown.enter.prevent="openHexModal(store.birthTemporalHex.year.hex)"
                    @keydown.space.prevent="openHexModal(store.birthTemporalHex.year.hex)"
                  >
                    <div class="hexNum">#{{ store.birthTemporalHex.year.hex.num ?? "—" }}</div>
                    <HexagramLines :binary="store.birthTemporalHex.year.hex.binary" size="sm" />
                    <div class="hexName cjkText">{{ hexNameShort(store.birthTemporalHex.year.hex.num ?? null, store.birthTemporalHex.year.hex.nameCn) }}</div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Month</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.birthTemporalHex.month.ganzhi) }}</div>
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.birthTemporalHex.month.hex.num }"
                    role="button"
                    :tabindex="store.birthTemporalHex.month.hex.num ? 0 : -1"
                    :aria-disabled="!store.birthTemporalHex.month.hex.num"
                    @click="openHexModal(store.birthTemporalHex.month.hex)"
                    @keydown.enter.prevent="openHexModal(store.birthTemporalHex.month.hex)"
                    @keydown.space.prevent="openHexModal(store.birthTemporalHex.month.hex)"
                  >
                    <div class="hexNum">#{{ store.birthTemporalHex.month.hex.num ?? "—" }}</div>
                    <HexagramLines :binary="store.birthTemporalHex.month.hex.binary" size="sm" />
                    <div class="hexName cjkText">{{ hexNameShort(store.birthTemporalHex.month.hex.num ?? null, store.birthTemporalHex.month.hex.nameCn) }}</div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Day</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.birthTemporalHex.day.ganzhi) }}</div>
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.birthTemporalHex.day.hex.num }"
                    role="button"
                    :tabindex="store.birthTemporalHex.day.hex.num ? 0 : -1"
                    :aria-disabled="!store.birthTemporalHex.day.hex.num"
                    @click="openHexModal(store.birthTemporalHex.day.hex)"
                    @keydown.enter.prevent="openHexModal(store.birthTemporalHex.day.hex)"
                    @keydown.space.prevent="openHexModal(store.birthTemporalHex.day.hex)"
                  >
                    <div class="hexNum">#{{ store.birthTemporalHex.day.hex.num ?? "—" }}</div>
                    <HexagramLines :binary="store.birthTemporalHex.day.hex.binary" size="sm" />
                    <div class="hexName cjkText">{{ hexNameShort(store.birthTemporalHex.day.hex.num ?? null, store.birthTemporalHex.day.hex.nameCn) }}</div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Hour</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.birthTemporalHex.hour.ganzhi) }}</div>
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.birthTemporalHex.hour.hex.num }"
                    role="button"
                    :tabindex="store.birthTemporalHex.hour.hex.num ? 0 : -1"
                    :aria-disabled="!store.birthTemporalHex.hour.hex.num"
                    @click="openHexModal(store.birthTemporalHex.hour.hex)"
                    @keydown.enter.prevent="openHexModal(store.birthTemporalHex.hour.hex)"
                    @keydown.space.prevent="openHexModal(store.birthTemporalHex.hour.hex)"
                  >
                    <div class="hexNum">#{{ store.birthTemporalHex.hour.hex.num ?? "—" }}</div>
                    <HexagramLines :binary="store.birthTemporalHex.hour.hex.binary" size="sm" />
                    <div class="hexName cjkText">{{ hexNameShort(store.birthTemporalHex.hour.hex.num ?? null, store.birthTemporalHex.hour.hex.nameCn) }}</div>
                  </div>
                </div>
              </div>
              <div v-else class="meta">Enter a valid birth datetime.</div>
              <div v-if="store.birthTemporalHex" class="panelFooter">
                <button
                  v-if="store.interpretationNeedsRefresh"
                  class="btn small"
                  :disabled="store.interpretationLoading"
                  @click="store.requestInterpretation()"
                >
                  {{ store.interpretationLoading ? "Loading…" : "Past" }}
                </button>
              </div>
            </section>

            <section class="panel">
              <div class="panelHeader">
                <div>
                  <div class="secTitle">Present (Moment)</div>
                  <div class="organLine">Organ: <strong>{{ store.presentOrgan }}</strong></div>
                </div>
                <div class="panelControls">
                  <input class="input inlineInput" type="datetime-local" v-model="store.presentDatetimeLocal" />
                  <button class="btn small" :class="{ primary: store.presentAuto }" @click="store.togglePresentAuto">Auto {{ store.presentAuto ? "On" : "Off" }}</button>
                  <button class="btn small" @click="store.shiftPresentHours(-2)">◀</button>
                  <button class="btn small" @click="store.shiftPresentHours(2)">▶</button>
                </div>
              </div>
              <div class="pillarGrid">
                <div class="pillarBox">
                  <div class="pillarLabel">Year</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.temporalHex.year.ganzhi) }}</div>
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.temporalHex.year.hex.num }"
                    role="button"
                    :tabindex="store.temporalHex.year.hex.num ? 0 : -1"
                    :aria-disabled="!store.temporalHex.year.hex.num"
                    @click="openHexModal(store.temporalHex.year.hex)"
                    @keydown.enter.prevent="openHexModal(store.temporalHex.year.hex)"
                    @keydown.space.prevent="openHexModal(store.temporalHex.year.hex)"
                  >
                    <div class="hexNum">#{{ store.temporalHex.year.hex.num ?? "—" }}</div>
                    <HexagramLines :binary="store.temporalHex.year.hex.binary" size="sm" />
                    <div class="hexName cjkText">{{ hexNameShort(store.temporalHex.year.hex.num ?? null, store.temporalHex.year.hex.nameCn) }}</div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Month</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.temporalHex.month.ganzhi) }}</div>
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.temporalHex.month.hex.num }"
                    role="button"
                    :tabindex="store.temporalHex.month.hex.num ? 0 : -1"
                    :aria-disabled="!store.temporalHex.month.hex.num"
                    @click="openHexModal(store.temporalHex.month.hex)"
                    @keydown.enter.prevent="openHexModal(store.temporalHex.month.hex)"
                    @keydown.space.prevent="openHexModal(store.temporalHex.month.hex)"
                  >
                    <div class="hexNum">#{{ store.temporalHex.month.hex.num ?? "—" }}</div>
                    <HexagramLines :binary="store.temporalHex.month.hex.binary" size="sm" />
                    <div class="hexName cjkText">{{ hexNameShort(store.temporalHex.month.hex.num ?? null, store.temporalHex.month.hex.nameCn) }}</div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Day</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.temporalHex.day.ganzhi) }}</div>
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.temporalHex.day.hex.num }"
                    role="button"
                    :tabindex="store.temporalHex.day.hex.num ? 0 : -1"
                    :aria-disabled="!store.temporalHex.day.hex.num"
                    @click="openHexModal(store.temporalHex.day.hex)"
                    @keydown.enter.prevent="openHexModal(store.temporalHex.day.hex)"
                    @keydown.space.prevent="openHexModal(store.temporalHex.day.hex)"
                  >
                    <div class="hexNum">#{{ store.temporalHex.day.hex.num ?? "—" }}</div>
                    <HexagramLines :binary="store.temporalHex.day.hex.binary" size="sm" />
                    <div class="hexName cjkText">{{ hexNameShort(store.temporalHex.day.hex.num ?? null, store.temporalHex.day.hex.nameCn) }}</div>
                  </div>
                </div>
                <div class="pillarBox">
                  <div class="pillarLabel">Hour</div>
                  <div class="pillarGz cjkText">{{ formatGanZhiLines(store.temporalHex.hour.ganzhi) || "—" }}</div>
                  <div
                    class="pillarHex"
                    :class="{ clickable: !!store.temporalHex.hour.hex.num }"
                    role="button"
                    :tabindex="store.temporalHex.hour.hex.num ? 0 : -1"
                    :aria-disabled="!store.temporalHex.hour.hex.num"
                    @click="openHexModal(store.temporalHex.hour.hex)"
                    @keydown.enter.prevent="openHexModal(store.temporalHex.hour.hex)"
                    @keydown.space.prevent="openHexModal(store.temporalHex.hour.hex)"
                  >
                    <div class="hexNum">#{{ store.temporalHex.hour.hex.num ?? "—" }}</div>
                    <HexagramLines :binary="store.temporalHex.hour.hex.binary" size="sm" />
                    <div class="hexName cjkText">{{ hexNameShort(store.temporalHex.hour.hex.num ?? null, store.temporalHex.hour.hex.nameCn) }}</div>
                  </div>
                </div>
              </div>
              <div v-if="store.birthProfile" class="panelFooter">
                <button
                  v-if="store.interpretationNeedsRefresh"
                  class="btn small"
                  :disabled="store.interpretationLoading"
                  @click="store.requestInterpretation()"
                >
                  {{ store.interpretationLoading ? "Loading…" : "Present" }}
                </button>
              </div>
            </section>
          </div>

          <div class="sec">
            <div class="secTitle">Current (Flow)</div>
            <div class="flowHeader">
              <div class="meta">
                {{ store.presentDatetimeLocal }} • {{ store.location || "location unspecified" }}
              </div>
              <div class="topRight" v-if="store.interpretationPlaceholder && !store.interpretationNeedsRefresh">
                <button class="btn small" @click="copyInterpretation">Copy</button>
              </div>
            </div>
            <div class="secBody">
              <div v-if="store.interpretationLoading">Generating interpretation...</div>
              <div v-else-if="store.interpretationPlaceholder && !store.interpretationNeedsRefresh" class="mono">
                {{ store.interpretationPlaceholder }}
              </div>
              <div v-else-if="store.interpretationPlaceholder" class="mono interpretation-error">
                {{ store.interpretationPlaceholder }}
              </div>
              <div v-else-if="store.interpretationNeedsRefresh" class="placeholder">
                BaZi has changed. Use Past or Present above to generate a new interpretation.
              </div>
              <div v-else class="placeholder">
                Enter birth datetime, then use Past or Present to interpret.
              </div>
            </div>
            <div class="secBody" style="margin-top: 10px;">
              <div class="qimenScope">
                <button class="btn small" :class="{ primary: qimenScope === 'hour' }" @click="qimenScope = 'hour'">Hour Chart</button>
                <button class="btn small" :class="{ primary: qimenScope === 'day' }" @click="qimenScope = 'day'">Day Chart</button>
              </div>
              <QimenChart :chart="qimenChart" />
            </div>
          </div>

          <div class="sec">
            <div class="secTitle">Future (Destiny)</div>
            <div class="secBody">
              <textarea class="destinyBox" placeholder="Destiny is yours to write."></textarea>
            </div>
          </div>
        </div>
      </main>

      <HexagramModal
        :open="isHexModalOpen"
        :hex-num="selectedHexNum"
        :hex-name="selectedHexDisplayName"
        :summaries="selectedHexSummary"
        @close="closeHexModal"
      />
    </div>
  </div>
</template>

