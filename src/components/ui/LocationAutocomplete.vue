<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue';

const props = defineProps<{
  locationName: string;
  latitude: number | null;
  longitude: number | null;
}>();

const emit = defineEmits<{
  (e: 'update:locationName', value: string): void;
  (e: 'update:latitude', value: number | null): void;
  (e: 'update:longitude', value: number | null): void;
}>();

interface NominatimResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
}

const query = ref(props.locationName);
const suggestions = ref<NominatimResult[]>([]);
const isSearching = ref(false);
const showDropdown = ref(false);
let searchTimeout: ReturnType<typeof setTimeout> | null = null;

const searchLocation = async (text: string) => {
  if (!text || text.length < 3) {
    suggestions.value = [];
    return;
  }
  
  isSearching.value = true;
  try {
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(text)}&limit=5&featuretype=city`);
    if (!res.ok) throw new Error('Network error');
    const data = await res.json() as NominatimResult[];
    suggestions.value = data;
  } catch (err) {
    console.error('Location search error:', err);
    suggestions.value = [];
  } finally {
    isSearching.value = false;
  }
};

const onInput = (e: Event) => {
  const val = (e.target as HTMLInputElement).value;
  query.value = val;
  showDropdown.value = true;
  
  // Emit just the text so it updates but invalidates the longitude until a valid click
  emit('update:locationName', val);
  emit('update:latitude', null);
  emit('update:longitude', null);
  
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    searchLocation(val);
  }, 400);
};

const selectLocation = (item: NominatimResult) => {
  // Extract city/primary name from display_name
  const primaryName = item.display_name.split(',')[0] || '';
  query.value = primaryName;
  showDropdown.value = false;
  
  emit('update:locationName', primaryName);
  emit('update:latitude', parseFloat(item.lat));
  emit('update:longitude', parseFloat(item.lon));
};

const hideDropdown = () => {
  // Delay slightly to allow click event on suggestion to fire
  setTimeout(() => {
    showDropdown.value = false;
  }, 200);
};

onBeforeUnmount(() => {
  if (searchTimeout) clearTimeout(searchTimeout);
});

watch(() => props.locationName, (newVal) => {
  if (newVal !== query.value && !showDropdown.value) {
    query.value = newVal;
  }
});
</script>

<template>
  <div class="location-autocomplete">
    <input 
      type="text" 
      class="input inlineInput" 
      placeholder="Search city..." 
      :value="query"
      @input="onInput"
      @focus="showDropdown = true"
      @blur="hideDropdown"
    />
    <div v-if="showDropdown && suggestions.length > 0" class="dropdown">
      <div 
        v-for="item in suggestions" 
        :key="item.place_id" 
        class="suggestion-item"
        @click="selectLocation(item)"
      >
        {{ item.display_name }}
      </div>
    </div>
    <div v-else-if="showDropdown && isSearching" class="dropdown">
      <div class="suggestion-item loading">Searching...</div>
    </div>
  </div>
</template>

<style scoped>
.location-autocomplete {
  position: relative;
  display: inline-block;
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 50;
  background: var(--bg-card, #2c2c2c);
  border: 1px solid var(--border-color, #444);
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  min-width: 250px;
}

.suggestion-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 0.9em;
  color: var(--text-color, #eee);
  border-bottom: 1px solid var(--border-color, #444);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background: var(--bg-hover, #444);
}

.suggestion-item.loading {
  color: #888;
  cursor: default;
}

.suggestion-item.loading:hover {
  background: transparent;
}
</style>