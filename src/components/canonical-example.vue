<script setup lang="ts">
/**
 * Canonical Example Component
 * Serves as the architectural anchor for Vue 3 Composition API components.
 */

import { computed } from 'vue'

/**
 * Documented props interface
 */
export interface CanonicalExampleProps {
  /**
   * The primary title of the component
   */
  title: string
  /**
   * Optional description text
   */
  description?: string
  /**
   * Whether the component is in a loading state
   */
  isLoading?: boolean
}

const props = withDefaults(defineProps<CanonicalExampleProps>(), {
  description: 'Default description',
  isLoading: false
})

const emit = defineEmits<{
  (e: 'actionClick', id: string): void
}>()

const computedClasses = computed(() => {
  return [
    'rounded-xl',
    'p-6',
    'transition-all',
    'duration-300',
    props.isLoading ? 'opacity-50 cursor-wait' : 'hover:shadow-lg'
  ]
})

const handleAction = () => {
  if (!props.isLoading) {
    emit('actionClick', 'canonical-action-id')
  }
}
</script>

<template>
  <div 
    class="flex flex-col gap-4 border border-gray-200 bg-white shadow-sm"
    :class="computedClasses"
  >
    <header class="flex items-center justify-between">
      <h2 class="text-xl font-bold tracking-tight text-gray-900">
        {{ title }}
      </h2>
      <span v-if="isLoading" class="text-sm font-medium text-blue-500 animate-pulse">
        Loading...
      </span>
    </header>
    
    <main>
      <p class="text-base text-gray-600">
        {{ description }}
      </p>
    </main>
    
    <footer class="mt-4 border-t border-gray-100 pt-4">
      <button 
        class="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:bg-gray-400"
        :disabled="isLoading"
        @click="handleAction"
      >
        Perform Action
      </button>
    </footer>
  </div>
</template>
