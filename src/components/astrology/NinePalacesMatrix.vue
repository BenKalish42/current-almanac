<template>
  <div class="nine-palaces-matrix flex flex-col items-center">
    <!-- Tradition Toggles -->
    <div class="tradition-toggles flex flex-wrap justify-center gap-2 mb-4 bg-slate-100/50 p-1.5 rounded-lg border border-slate-200/50">
      <label 
        class="flex items-center cursor-pointer px-3 py-1.5 text-sm rounded-md transition-colors select-none"
        :class="activeTraditions.includes('loshu') ? 'bg-white shadow-sm font-medium text-slate-800' : 'text-slate-600 hover:text-slate-900'"
      >
        <input type="checkbox" v-model="activeTraditions" value="loshu" class="sr-only">
        <span class="mr-1.5">☯️</span> Chinese Lo Shu
      </label>
      
      <label 
        class="flex items-center cursor-pointer px-3 py-1.5 text-sm rounded-md transition-colors select-none"
        :class="activeTraditions.includes('mewa') ? 'bg-white shadow-sm font-medium text-slate-800' : 'text-slate-600 hover:text-slate-900'"
      >
        <input type="checkbox" v-model="activeTraditions" value="mewa" class="sr-only">
        <span class="mr-1.5">🏔️</span> Tibetan Mewa
      </label>

      <label 
        class="flex items-center cursor-pointer px-3 py-1.5 text-sm rounded-md transition-colors select-none"
        :class="activeTraditions.includes('ninestarki') ? 'bg-white shadow-sm font-medium text-slate-800' : 'text-slate-600 hover:text-slate-900'"
      >
        <input type="checkbox" v-model="activeTraditions" value="ninestarki" class="sr-only">
        <span class="mr-1.5">🌸</span> Japanese 9-Star
      </label>
    </div>

    <!-- 3x3 Grid -->
    <div class="grid grid-cols-3 gap-2 p-2 bg-slate-200/60 rounded-xl w-full max-w-[420px]">
      <div 
        v-for="dir in gridLayoutDirections" 
        :key="dir"
        @click="openSynthesis(palaceNumber(dir))"
        :class="[
          'palace-cell flex flex-col items-center justify-start p-3 rounded-lg border text-center transition-all shadow-sm cursor-pointer hover:border-slate-400 hover:shadow-md min-h-[110px]', 
          getCellClass(palaceNumber(dir))
        ]"
      >
        <!-- Direction Indicator (Subtle) -->
        <div class="absolute top-2 left-2 text-[10px] font-bold tracking-wider text-slate-400 opacity-60">{{ dir }}</div>
        
        <!-- Center Number -->
        <div class="text-3xl font-bold mt-1 mb-2 opacity-90 leading-none">
          {{ palaceNumber(dir) }}
        </div>
        
        <!-- Layered Data -->
        <div class="flex flex-col items-center justify-center gap-1.5 w-full">
          <div v-if="activeTraditions.includes('loshu')" class="text-[11px] leading-tight font-medium uppercase tracking-wider flex flex-col items-center w-full" :class="getData(palaceNumber(dir)).loshuTextClass">
            <span class="text-[9px] opacity-50 tracking-widest mb-0.5 text-slate-700">Lo Shu</span>
            {{ getData(palaceNumber(dir)).loshuLabel }}
          </div>
          
          <div v-if="activeTraditions.includes('mewa')" class="text-[11px] leading-tight font-medium uppercase tracking-wider flex flex-col items-center w-full" :class="activeTraditions.includes('mewa') && activeTraditions.length === 1 ? 'text-inherit' : getData(palaceNumber(dir)).mewaTextClass">
            <span class="text-[9px] opacity-50 tracking-widest mb-0.5" :class="activeTraditions.includes('mewa') && activeTraditions.length === 1 ? 'text-inherit' : 'text-slate-700'">Mewa</span>
            {{ getData(palaceNumber(dir)).mewaLabel }}
          </div>
          
          <div v-if="activeTraditions.includes('ninestarki')" class="text-[11px] leading-tight font-medium uppercase tracking-wider flex flex-col items-center w-full" :class="getData(palaceNumber(dir)).nineStarTextClass">
            <span class="text-[9px] opacity-50 tracking-widest mb-0.5 text-slate-700">9-Star Ki</span>
            <span class="max-w-[100px] truncate">{{ getData(palaceNumber(dir)).nineStarLabel }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Synthesis Modal -->
    <div v-if="selectedPalace" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm" @click.self="closeSynthesis">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[85vh] overflow-y-auto border border-slate-200 flex flex-col">
        <!-- Header -->
        <div class="sticky top-0 bg-white/95 backdrop-blur px-5 py-4 border-b border-slate-100 flex justify-between items-center z-10">
          <div class="flex items-center gap-3">
            <div class="flex items-center justify-center w-10 h-10 rounded-full bg-slate-100 text-xl font-bold text-slate-800">
              {{ selectedPalace.number }}
            </div>
            <div>
              <h3 class="font-bold text-lg text-slate-800 leading-tight">Palace Synthesis</h3>
              <p class="text-xs text-slate-500 font-medium">Click to dismiss</p>
            </div>
          </div>
          <button @click="closeSynthesis" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">
            ✕
          </button>
        </div>

        <!-- Content -->
        <div class="p-5 space-y-6">
          <section class="synthesis-section">
            <h4 class="flex items-center gap-2 font-bold text-slate-800 mb-2 pb-2 border-b border-slate-100">
              <span>☯️</span> Chinese Lo Shu
            </h4>
            <div class="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-1">
              {{ selectedPalace.loshuLabel }}
            </div>
            <p class="text-sm text-slate-600 leading-relaxed">
              {{ selectedPalace.synthesisText.loshu }}
            </p>
          </section>

          <section class="synthesis-section">
            <h4 class="flex items-center gap-2 font-bold text-slate-800 mb-2 pb-2 border-b border-slate-100">
              <span>🏔️</span> Tibetan Mewa
            </h4>
            <div class="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-1">
              {{ selectedPalace.mewaLabel }}
            </div>
            <p class="text-sm text-slate-600 leading-relaxed">
              {{ selectedPalace.synthesisText.mewa }}
            </p>
          </section>

          <section class="synthesis-section">
            <h4 class="flex items-center gap-2 font-bold text-slate-800 mb-2 pb-2 border-b border-slate-100">
              <span>🌸</span> Japanese Nine Star Ki
            </h4>
            <div class="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-1">
              {{ selectedPalace.nineStarLabel }}
            </div>
            <p class="text-sm text-slate-600 leading-relaxed">
              {{ selectedPalace.synthesisText.ninestarki }}
            </p>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  type TraditionType, 
  type NinePalaceData,
  ninePalacesDictionary, 
  getPalaceStars, 
  gridLayoutDirections 
} from '../../data/ninePalacesDictionary';

const props = defineProps<{
  /** Nine star engine returns digit as string; coerce for Lo Shu. */
  centerStar: number | string;
}>();

// Default to having Chinese Lo Shu active
const activeTraditions = ref<TraditionType[]>(['loshu']);

const centerStarN = computed(() => {
  const n = Number(props.centerStar);
  if (!Number.isFinite(n) || n < 1 || n > 9) return 1;
  return n;
});

const palaces = computed(() => getPalaceStars(centerStarN.value));

function palaceNumber(dir: (typeof gridLayoutDirections)[number]): number {
  return palaces.value[dir]!;
}

const selectedPalace = ref<NinePalaceData | null>(null);

function getData(starNumber: number): NinePalaceData {
  return ninePalacesDictionary[starNumber]!;
}

function getCellClass(starNumber: number) {
  // Apply Mewa background color ONLY if Mewa is the sole active tradition, 
  // otherwise keep a neutral background so the multiple texts are readable.
  if (activeTraditions.value.includes('mewa') && activeTraditions.value.length === 1) {
    return getData(starNumber).mewaBgClass;
  }
  return 'bg-white text-slate-800 border-slate-200';
}

function openSynthesis(starNumber: number) {
  selectedPalace.value = getData(starNumber);
}

function closeSynthesis() {
  selectedPalace.value = null;
}
</script>

<style scoped>
.palace-cell {
  position: relative;
}
</style>