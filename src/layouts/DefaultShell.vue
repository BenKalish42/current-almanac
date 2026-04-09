<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from "vue-router";
import ThemeSkinSelect from "@/components/theme/ThemeSkinSelect.vue";

const route = useRoute();
</script>

<template>
  <div class="app-shell">
    <nav class="app-nav" aria-label="Main navigation">
      <RouterLink to="/astrology" class="nav-link">Astrology</RouterLink>
      <RouterLink to="/alchemy" class="nav-link">Alchemy</RouterLink>
      <RouterLink to="/ai" class="nav-link">Intelligence</RouterLink>
      <div style="flex: 1"></div>
      <ThemeSkinSelect v-if="route.name !== 'astrology'" class="nav-skin-slot" />
      <RouterLink to="/hexagrams" class="nav-link">Hexagrams</RouterLink>
      <RouterLink to="/community" class="nav-link">Community</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>

<style scoped>
.nav-skin-slot {
  flex-shrink: 0;
  margin-right: 8px;
}
</style>
