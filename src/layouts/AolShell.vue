<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from "vue-router";
import ThemeSkinSelect from "@/components/theme/ThemeSkinSelect.vue";

const route = useRoute();
</script>

<template>
  <div class="skin-layout-aol-root">
    <div class="aol-shell">
      <div class="aol-menubar" aria-hidden="true">
        <span>File</span>
        <span>Edit</span>
        <span>View</span>
        <span>Go</span>
        <span>Favorites</span>
        <span>Help</span>
      </div>

      <header class="aol-brand-bar">
        <div class="aol-brand-title">Current Almanac Online</div>
        <div class="aol-brand-tagline">Charts, hexagrams, and flow — dial-up optional</div>
      </header>

      <nav class="aol-toolbar" aria-label="Main navigation">
        <RouterLink to="/astrology" class="aol-keyword" active-class="router-link-active">Astrology</RouterLink>
        <RouterLink to="/alchemy" class="aol-keyword" active-class="router-link-active">Alchemy</RouterLink>
        <RouterLink to="/ai" class="aol-keyword" active-class="router-link-active">Intelligence</RouterLink>
        <RouterLink to="/hexagrams" class="aol-keyword" active-class="router-link-active">Hexagrams</RouterLink>
        <RouterLink to="/community" class="aol-keyword" active-class="router-link-active">Community</RouterLink>
        <span class="aol-toolbar-spacer" />
        <ThemeSkinSelect v-if="route.name !== 'astrology'" class="aol-toolbar-skin" />
      </nav>

      <main class="aol-main">
        <div class="aol-main-inner">
          <RouterView />
        </div>
      </main>

      <footer class="aol-statusbar">
        <span class="aol-status-left">Connection: Online</span>
        <span class="aol-status-right">14.4 kbps (simulated)</span>
      </footer>
    </div>
  </div>
</template>

<style src="./aol-chrome.css"></style>
