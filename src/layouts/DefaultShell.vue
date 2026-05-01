<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
import ToolbarSettingsMenu from "@/components/toolbar/ToolbarSettingsMenu.vue";
</script>

<template>
  <div class="app-shell">
    <nav class="app-nav" aria-label="Main navigation">
      <RouterLink to="/astrology" class="nav-link">Astrology</RouterLink>
      <RouterLink to="/alchemy" class="nav-link">Alchemy</RouterLink>
      <RouterLink to="/intelligence" class="nav-link">Intelligence</RouterLink>
      <div style="flex: 1"></div>
      <ToolbarSettingsMenu trigger-class="nav-link" />
      <RouterLink to="/hexagrams" class="nav-link">Hexagrams</RouterLink>
      <RouterLink to="/workbench" class="nav-link">Workbench</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>
