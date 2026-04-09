<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";
import ThemeSkinSelect from "@/components/theme/ThemeSkinSelect.vue";

const route = useRoute();

const CRUMB_LABELS: Record<string, string> = {
  astrology: "Astrology",
  alchemy: "Alchemy",
  ai: "Intelligence",
  hexagrams: "Hexagrams",
  community: "Community",
};

const breadcrumbs = computed(() => {
  const name = route.name;
  const tail =
    typeof name === "string" && CRUMB_LABELS[name]
      ? CRUMB_LABELS[name]
      : typeof name === "string"
        ? name
        : "Home";
  return `Current Almanac » ${tail}`;
});
</script>

<template>
  <div class="skin-layout-forum-root">
  <div class="app-shell">
    <header class="app-top">
      <div class="app-nav">
        <RouterLink to="/astrology" class="app-wordmark forum-wordmark">Current Almanac</RouterLink>
        <div class="app-nav-links">
          <RouterLink to="/astrology" class="nav-link">Astrology</RouterLink>
          <RouterLink to="/alchemy" class="nav-link">Alchemy</RouterLink>
          <RouterLink to="/ai" class="nav-link">Intelligence</RouterLink>
          <RouterLink to="/hexagrams" class="nav-link">Hexagrams</RouterLink>
          <RouterLink to="/community" class="nav-link">Community</RouterLink>
        </div>
        <ThemeSkinSelect v-if="route.name !== 'astrology'" class="forum-nav-skin" />
      </div>
      <div class="app-breadcrumb" aria-label="Breadcrumb">{{ breadcrumbs }}</div>
    </header>
    <RouterView />
  </div>
  </div>
</template>

<style src="./forum-chrome.css"></style>

<style scoped>
.forum-nav-skin {
  margin-left: auto;
  flex-shrink: 0;
}
.app-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
}
</style>
