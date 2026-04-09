<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from "vue-router";
import ThemeSkinSelect from "@/components/theme/ThemeSkinSelect.vue";

const route = useRoute();

function menuPlaceholder(e: Event) {
  e.preventDefault();
}
</script>

<template>
  <div class="skin-layout-frostwire-root">
  <div class="app-shell fw-shell">
    <header class="fw-titlebar">
      <div class="fw-titlebar-left">
        <span class="fw-app-name">Current Almanac</span>
        <span class="fw-tagline">Explore the flow</span>
      </div>
      <div class="fw-titlebar-controls" aria-hidden="true">
        <span class="fw-win-btn fw-win-min" title="" />
        <span class="fw-win-btn fw-win-max" title="" />
        <span class="fw-win-btn fw-win-close" title="" />
      </div>
    </header>

    <div class="fw-menubar" aria-label="Menu bar (placeholder)">
      <a href="#" class="fw-menu-item" @click="menuPlaceholder">File</a>
      <a href="#" class="fw-menu-item" @click="menuPlaceholder">View</a>
      <a href="#" class="fw-menu-item" @click="menuPlaceholder">Help</a>
      <span class="fw-menubar-spacer" />
      <ThemeSkinSelect v-if="route.name !== 'astrology'" class="fw-menubar-skin" />
    </div>

    <nav class="fw-tabstrip" aria-label="Main navigation">
      <RouterLink to="/astrology" class="fw-tab" active-class="fw-tab-active">Astrology</RouterLink>
      <RouterLink to="/alchemy" class="fw-tab" active-class="fw-tab-active">Alchemy</RouterLink>
      <RouterLink to="/ai" class="fw-tab" active-class="fw-tab-active">Intelligence</RouterLink>
      <RouterLink to="/hexagrams" class="fw-tab" active-class="fw-tab-active">Hexagrams</RouterLink>
      <RouterLink to="/community" class="fw-tab" active-class="fw-tab-active">Community</RouterLink>
    </nav>

    <main class="fw-content">
      <RouterView />
    </main>

    <footer class="fw-statusbar">
      <span class="fw-status-text">0 flows · ready</span>
      <span class="fw-signal" aria-hidden="true">
        <span class="fw-signal-bar" />
        <span class="fw-signal-bar" />
        <span class="fw-signal-bar" />
        <span class="fw-signal-bar" />
      </span>
    </footer>
  </div>
  </div>
</template>

<style src="./frostwire-chrome.css"></style>

<style scoped>
.fw-menubar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 18px;
}
.fw-menubar-spacer {
  flex: 1;
  min-width: 8px;
}
.fw-menubar-skin :deep(.skinLbl) {
  font-size: 11px;
}
.fw-menubar-skin :deep(.skinSelect) {
  font-size: 11px;
  padding: 2px 6px;
  max-width: 160px;
}
</style>
