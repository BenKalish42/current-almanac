<script setup lang="ts">
import DiscourseForum from "@/components/community/DiscourseForum.vue";
</script>

<template>
  <div class="wrap">
    <main class="main">
      <div class="card">
        <header class="header">
          <h1 class="title">Community</h1>
          <p class="subtitle">
            Daoism &amp; Chinese medicine — discussion via Discourse.
          </p>
        </header>

        <div class="content">
          <DiscourseForum />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.wrap {
  display: flex;
  min-height: 100vh;
  padding: 18px;
  color: var(--txt);
}

.main {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.card {
  border: 1px solid var(--b);
  border-radius: 12px;
  padding: 24px;
  max-width: 1100px;
  width: 100%;
  background: rgba(0, 0, 0, 0.02);
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 120px);
}

.header {
  text-align: center;
  margin-bottom: 20px;
}

.title {
  font-size: 24px;
  font-weight: 800;
  color: var(--txt);
  margin: 0 0 6px;
}

.subtitle {
  font-size: 14px;
  color: var(--muted);
  margin: 0;
  max-width: 36rem;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.45;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
</style>
