<script setup lang="ts">
type PhilosophySystem =
  | "daoism"
  | "confucianism"
  | "buddhism"
  | "psychology"
  | "humandesign"
  | "genekeys";

defineProps<{
  system: PhilosophySystem;
}>();
</script>

<template>
  <svg
    v-if="system === 'daoism'"
    viewBox="0 0 24 24"
    aria-hidden="true"
    class="w-5 h-5"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
    <path d="M12 3a4.5 4.5 0 0 0 0 9a4.5 4.5 0 0 1 0 9" />
    <path d="M11.5 7.5a.5 .5 0 1 0 1 0a.5 .5 0 1 0 -1 0" fill="currentColor" />
    <path d="M11.5 16.5a.5 .5 0 1 0 1 0a.5 .5 0 1 0 -1 0" fill="currentColor" />
  </svg>

  <svg
    v-else-if="system === 'confucianism'"
    viewBox="0 0 24 24"
    aria-hidden="true"
    class="w-5 h-5"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <g transform="translate(1.1 1.1) scale(0.2)">
      <path d="M52.77,15.08c1.08,1.08,1.67,2.49,1.76,5.52c0.4,14.55-0.26,62.16-0.26,67.12c0,9.78-7.52,0.03-9.02-1.22" />
      <path d="M17.5,45.75c1.75,0.62,3.73,0.43,5.25,0C25.88,44.88,36.09,41,38.59,40s4.47,1.24,3.75,3.5C39,54,28.25,69,19,74.75" />
      <path d="M81.22,27.5c-0.22,1.25-0.72,2.25-1.52,2.97c-5.64,5.1-12.45,9.78-22.45,13.78" />
      <path d="M57,46c8.82,10.73,19.23,21.46,28.42,27.42c2.16,1.4,4.52,3,7.08,3.58" />
    </g>
  </svg>

  <svg
    v-else-if="system === 'buddhism'"
    viewBox="0 0 24 24"
    aria-hidden="true"
    class="w-5 h-5"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <path
      d="M337.8 205.7l48.6-42.5c13.8 19.3 23.4 41.9 27.4 66.2l-64.4 4.3c-2.4-10.1-6.4-19.5-11.6-28zm140.1 19.5c-5.3-38.8-20.6-74.5-43.2-104.3l.8-.7C449 108.4 449.7 87.6 437 75s-33.4-12-45.2 1.5l-.7 .8c-29.8-22.6-65.5-37.9-104.3-43.2l.1-1.1c1.2-17.9-13-33-30.9-33s-32.1 15.2-30.9 33l.1 1.1c-38.8 5.3-74.5 20.6-104.3 43.2l-.7-.8C108.4 63 87.6 62.3 75 75s-12 33.4 1.5 45.2l.8 .7c-22.6 29.8-37.9 65.5-43.2 104.3l-1.1-.1c-17.9-1.2-33 13-33 30.9s15.2 32.1 33 30.9l1.1-.1c5.3 38.8 20.6 74.5 43.2 104.3l-.8 .7C63 403.6 62.3 424.4 75 437s33.4 12 45.2-1.5l.7-.8c29.8 22.6 65.5 37.9 104.3 43.2l-.1 1.1c-1.2 17.9 13 33 30.9 33s32.1-15.2 30.9-33l-.1-1.1c38.8-5.3 74.5-20.6 104.3-43.2l.7 .8c11.8 13.5 32.5 14.2 45.2 1.5s12-33.4-1.5-45.2l-.8-.7c22.6-29.8 37.9-65.5 43.2-104.3l1.1 .1c17.9 1.2 33-13 33-30.9s-15.2-32.1-33-30.9l-1.1 .1zM163.2 125.6c19.3-13.8 41.9-23.4 66.2-27.5l4.3 64.4c-10 2.4-19.5 6.4-28 11.6l-42.5-48.6zm-65 103.8c4.1-24.4 13.7-46.9 27.5-66.2l48.6 42.5c-5.3 8.5-9.2 18-11.6 28l-64.4-4.3zm27.5 119.4c-13.8-19.3-23.4-41.9-27.5-66.2l64.4-4.3c2.4 10 6.4 19.5 11.6 28l-48.6 42.5zm103.8 65c-24.4-4.1-46.9-13.7-66.2-27.4l42.5-48.6c8.5 5.3 18 9.2 28 11.6l-4.3 64.4zm119.4-27.4c-19.3 13.8-41.9 23.4-66.2 27.4l-4.3-64.4c10-2.4 19.5-6.4 28-11.6l42.5 48.6zm65-103.8c-4.1 24.4-13.7 46.9-27.4 66.2l-48.6-42.5c5.3-8.5 9.2-18 11.6-28l64.4 4.3zm-65-156.9l-42.5 48.6c-8.5-5.3-18-9.2-28-11.6l4.3-64.4c24.4 4.1 46.9 13.7 66.2 27.5zM256 224a32 32 0 1 1 0 64 32 32 0 1 1 0-64z"
      transform="scale(0.046875)"
      fill="currentColor"
      stroke="none"
    />
  </svg>

  <svg
    v-else-if="system === 'psychology'"
    viewBox="0 0 24 24"
    aria-hidden="true"
    class="w-5 h-5"
    fill="none"
    stroke="currentColor"
    stroke-width="1"
  >
    <text
      x="12"
      y="15.3"
      text-anchor="middle"
      font-size="14"
      font-family="serif"
      font-weight="600"
      fill="currentColor"
      stroke="none"
    >
      &#936;&#968;
    </text>
  </svg>

  <svg
    v-else-if="system === 'humandesign'"
    viewBox="0 0 24 24"
    aria-hidden="true"
    class="w-5 h-5"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <rect x="16" y="16" width="6" height="6" rx="1" />
    <rect x="2" y="16" width="6" height="6" rx="1" />
    <rect x="9" y="2" width="6" height="6" rx="1" />
    <path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3" />
    <path d="M12 12V8" />
  </svg>

  <svg
    v-else
    viewBox="0 0 24 24"
    aria-hidden="true"
    class="w-5 h-5"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <path d="m10 16 1.5 1.5" />
    <path d="m14 8-1.5-1.5" />
    <path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993" />
    <path d="m16.5 10.5 1 1" />
    <path d="m17 6-2.891-2.891" />
    <path d="M2 15c6.667-6 13.333 0 20-6" />
    <path d="m20 9 .891.891" />
    <path d="M3.109 14.109 4 15" />
    <path d="m6.5 12.5 1 1" />
    <path d="m7 18 2.891 2.891" />
    <path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993" />
  </svg>
</template>
