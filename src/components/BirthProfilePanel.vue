<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { formatGanZhiDisplay, formatStemDisplay, getBranchInfo } from '@/core/ganzhi'
import { computeBirthProfile, parseDatetimeLocal, type BirthProfileResult, type Sect } from '@/lib/personal/baziNineStar'

const STORAGE_KEY_DT = 'current.birth.datetimeLocal'
const STORAGE_KEY_SECT = 'current.birth.sect'

const emit = defineEmits<{
  (e: 'profile-change', profile: BirthProfileResult | null): void
}>()

const birthDatetimeLocal = ref<string>(
  localStorage.getItem(STORAGE_KEY_DT) ?? '1990-01-01T12:00'
)

const sect = ref<Sect>(
  (Number(localStorage.getItem(STORAGE_KEY_SECT)) as Sect) || 2
)

watch(birthDatetimeLocal, (v) => localStorage.setItem(STORAGE_KEY_DT, v))
watch(sect, (v) => localStorage.setItem(STORAGE_KEY_SECT, String(v)))

const profile = computed(() => {
  try {
    const input = parseDatetimeLocal(birthDatetimeLocal.value)
    return computeBirthProfile(input, sect.value)
  } catch {
    return null
  }
})

watch(profile, (v) => emit('profile-change', v), { immediate: true })

const showNineStar = ref(true)

const WUXING_MAP: Record<string, string> = {
  '木': 'Wood',
  '火': 'Fire',
  '土': 'Earth',
  '金': 'Metal',
  '水': 'Water',
}

const NINE_STAR_NUMBER_MAP: Record<string, string> = {
  '一': '1',
  '二': '2',
  '三': '3',
  '四': '4',
  '五': '5',
  '六': '6',
  '七': '7',
  '八': '8',
  '九': '9',
}

const BAGUA_MAP: Record<string, string> = {
  '坎': 'Kan',
  '坤': 'Kun',
  '震': 'Zhen',
  '巽': 'Xun',
  '中': 'Center',
  '乾': 'Qian',
  '兑': 'Dui',
  '艮': 'Gen',
  '离': 'Li',
}

const XUAN_KONG_MAP: Record<string, string> = {
  '贪狼': 'Greedy Wolf',
  '巨门': 'Huge Gate',
  '禄存': 'Lu Cun',
  '文曲': 'Literary Arts',
  '廉贞': 'Integrity',
  '武曲': 'Military Arts',
  '破军': 'Army Breaker',
  '左辅': 'Left Assistant',
  '右弼': 'Right Assistant',
}

function translateNineStar(value: string, map: Record<string, string>) {
  const translated = map[value]
  return translated ? `${value} ${translated}` : value
}

function formatBranchPillarDisplay(zhi: string) {
  const info = getBranchInfo(zhi)
  if (!info) return zhi
  return `${info.char} ${info.animal} ${info.animalEmoji}\n(${info.element} ${info.elementEmoji})`
}

</script>

<template>
  <section class="birth-panel">
    <div class="birth-header">
      <div class="title">Birth Profile</div>

      <div class="controls">
        <label class="control">
          <div class="label">Birth datetime</div>
          <input type="datetime-local" v-model="birthDatetimeLocal" />
        </label>

        <label class="control">
          <div class="label">BaZi sect</div>
          <select v-model.number="sect">
            <option :value="1">sect 1</option>
            <option :value="2">sect 2</option>
          </select>
        </label>
      </div>
    </div>

    <div v-if="profile" class="grid">
      <div class="card">
        <div class="card-title">Four Pillars (BaZi)</div>

        <table class="table">
          <thead>
            <tr>
              <th>Pillar</th>
              <th>Heavenly Stem</th>
              <th>Earthly Branch</th>
              <th>Stem-Branch (GanZhi)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Year</td>
              <td>{{ formatStemDisplay(profile.bazi.pillars.year.gan) }}</td>
              <td class="branchDisplay">{{ formatBranchPillarDisplay(profile.bazi.pillars.year.zhi) }}</td>
              <td>{{ formatGanZhiDisplay(profile.bazi.pillars.year.ganZhi) }}</td>
            </tr>
            <tr>
              <td>Month</td>
              <td>{{ formatStemDisplay(profile.bazi.pillars.month.gan) }}</td>
              <td class="branchDisplay">{{ formatBranchPillarDisplay(profile.bazi.pillars.month.zhi) }}</td>
              <td>{{ formatGanZhiDisplay(profile.bazi.pillars.month.ganZhi) }}</td>
            </tr>
            <tr>
              <td>Day</td>
              <td>{{ formatStemDisplay(profile.bazi.pillars.day.gan) }}</td>
              <td class="branchDisplay">{{ formatBranchPillarDisplay(profile.bazi.pillars.day.zhi) }}</td>
              <td>{{ formatGanZhiDisplay(profile.bazi.pillars.day.ganZhi) }}</td>
            </tr>
            <tr>
              <td>Hour</td>
              <td>{{ formatStemDisplay(profile.bazi.pillars.hour.gan) }}</td>
              <td class="branchDisplay">{{ formatBranchPillarDisplay(profile.bazi.pillars.hour.zhi) }}</td>
              <td>{{ formatGanZhiDisplay(profile.bazi.pillars.hour.ganZhi) }}</td>
            </tr>
          </tbody>
        </table>

      </div>

      <div v-if="showNineStar" class="card">
        <div class="card-title">Nine Star</div>

        <table class="table">
          <thead>
            <tr>
              <th>Scope</th>
              <th>#</th>
              <th>Element</th>
              <th>Position</th>
              <th>Name (XK)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Year</td>
              <td>{{ translateNineStar(profile.nineStar.year.number, NINE_STAR_NUMBER_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.year.element, WUXING_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.year.position, BAGUA_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.year.nameXuanKong, XUAN_KONG_MAP) }}</td>
            </tr>
            <tr>
              <td>Month</td>
              <td>{{ translateNineStar(profile.nineStar.month.number, NINE_STAR_NUMBER_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.month.element, WUXING_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.month.position, BAGUA_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.month.nameXuanKong, XUAN_KONG_MAP) }}</td>
            </tr>
            <tr>
              <td>Day</td>
              <td>{{ translateNineStar(profile.nineStar.day.number, NINE_STAR_NUMBER_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.day.element, WUXING_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.day.position, BAGUA_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.day.nameXuanKong, XUAN_KONG_MAP) }}</td>
            </tr>
            <tr>
              <td>Time</td>
              <td>{{ translateNineStar(profile.nineStar.time.number, NINE_STAR_NUMBER_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.time.element, WUXING_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.time.position, BAGUA_MAP) }}</td>
              <td>{{ translateNineStar(profile.nineStar.time.nameXuanKong, XUAN_KONG_MAP) }}</td>
            </tr>
          </tbody>
        </table>

      </div>
    </div>

    <div v-else class="hint">Enter a valid birth datetime.</div>
  </section>
</template>

<style scoped>
.birth-panel {
  padding: 12px;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 12px;
  margin-bottom: 12px;
}

.birth-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.title {
  font-size: 14px;
  font-weight: 600;
  opacity: 0.9;
}

.controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.control .label {
  font-size: 11px;
  opacity: 0.7;
  margin-bottom: 4px;
}

.control input,
.control select {
  height: 32px;
  padding: 0 10px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.12);
  background: transparent;
  color: inherit;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; }
}

.card {
  padding: 10px;
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 12px;
}

.card-title {
  font-size: 12px;
  font-weight: 600;
  opacity: 0.9;
  margin-bottom: 8px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.table th,
.table td {
  border: 1px solid rgba(255,255,255,0.10);
  padding: 6px 8px;
  text-align: left;
}

.branchDisplay {
  white-space: pre-line;
}

.mono {
  margin-top: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 11px;
  opacity: 0.85;
  line-height: 1.45;
}

.mono .k {
  opacity: 0.65;
  margin-right: 6px;
}

.hint {
  font-size: 12px;
  opacity: 0.7;
}
</style>