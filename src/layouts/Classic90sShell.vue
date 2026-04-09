<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from "vue-router";
import ThemeSkinSelect from "@/components/theme/ThemeSkinSelect.vue";

const route = useRoute();
</script>

<template>
  <div class="skin-layout-classic90s-root">
  <div class="app-shell os-bevel-out">
    <nav class="app-nav" aria-label="Main navigation">
      <RouterLink to="/astrology" class="nav-link">Astrology</RouterLink>
      <RouterLink to="/alchemy" class="nav-link">Alchemy</RouterLink>
      <RouterLink to="/ai" class="nav-link">Intelligence</RouterLink>
      <div class="app-nav-spacer" />
      <ThemeSkinSelect v-if="route.name !== 'astrology'" class="c90-skin" />
      <RouterLink to="/hexagrams" class="nav-link">Hexagrams</RouterLink>
      <RouterLink to="/community" class="nav-link">Community</RouterLink>
    </nav>
    <div class="app-client">
      <RouterView />
    </div>
  </div>
  </div>
</template>

<style src="./classic90s-chrome.css"></style>

<style scoped>
.c90-skin {
  flex-shrink: 0;
  margin: 0 6px;
}
</style>
