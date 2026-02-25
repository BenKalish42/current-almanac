<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <div class="app-shell">
    <nav class="app-nav">
      <RouterLink to="/astrology" class="nav-link">Astrology</RouterLink>
      <RouterLink to="/alchemy" class="nav-link">Alchemy</RouterLink>
      <RouterLink to="/ai" class="nav-link">Intelligence</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>

<style>
:root {
  --b: rgba(0,0,0,0.12);
  --b2: rgba(0,0,0,0.18);
  --bg: rgba(0, 0, 0, 0.04);
  --txt: rgba(255, 255, 255, 0.88);
  --muted: rgba(255, 255, 255, 0.62);
}

#app {
  background-color: var(--color-daoist-bg);
}

.app-shell {
  min-height: 100vh;
  min-height: 100dvh;
}

.app-nav {
  display: flex;
  gap: 16px;
  padding: 12px 18px;
  padding-top: calc(12px + env(safe-area-inset-top, 0px));
  background: var(--color-daoist-surface);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-link {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

.nav-link:hover {
  color: white;
}

.nav-link.router-link-active {
  color: white;
  text-decoration: underline;
}

.wrap {
  display: flex;
  min-height: 100vh;
  gap: 18px;
  padding: 18px;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial,
    "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
  color: var(--txt);
}

.appRoot {
  display: grid;
  gap: 12px;
}

.appHeader {
  padding: 18px 18px 0 18px;
  display: grid;
  gap: 6px;
}

.appHeader .title {
  font-size: 20px;
  font-weight: 800;
  color: var(--txt);
}

.subtitle {
  font-size: 14px;
  color: var(--txt);
  opacity: 0.9;
}

.sub { font-size: 12px; color: var(--muted); margin-top: 6px; }

.side {
  width: 240px;
  border: 1px solid var(--b);
  border-radius: 12px;
  padding: 14px;
  overflow: auto;
}

.title { font-size: 16px; font-weight: 700; }

.controls { display: grid; gap: 10px; margin-top: 14px; }

.lbl { font-size: 12px; display: grid; gap: 6px; }
.input {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--b2);
  border-radius: 10px;
  outline: none;
  background: var(--color-daoist-surface);
  color: var(--color-daoist-text);
}

.btn {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--b2);
  background: transparent;
  cursor: pointer;
}
.btn.primary { background: var(--bg); font-weight: 700; }
.btn.small { padding: 8px 10px; font-size: 12px; }

.sectionHdr {
  margin-top: 16px;
  font-size: 12px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--muted);
}

.recent { margin-top: 10px; display: grid; gap: 8px; }
.empty { font-size: 13px; color: var(--muted); }

.item {
  text-align: left;
  padding: 10px;
  border-radius: 10px;
  border: 1px solid var(--b);
  background: transparent;
  cursor: pointer;
}
.item.active { border-color: rgba(0,0,0,0.35); background: var(--bg); }
.itemTitle { font-size: 13px; font-weight: 700; }
.itemSub, .itemMeta { font-size: 12px; color: var(--muted); margin-top: 4px; }

.main { flex: 1; display: flex; }
.card {
  border: 1px solid var(--b);
  border-radius: 12px;
  padding: 18px;
  max-width: 1200px;
  width: 100%;
}

.topSections {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.panel {
  border: 1px solid var(--b);
  border-radius: 12px;
  padding: 12px;
  background: rgba(255,255,255,0.02);
  display: grid;
  gap: 12px;
  overflow-x: auto;
}

.panelHeader {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  flex-wrap: wrap;
}

.panelControls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
}

.panelFooter {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--b2);
}

.organLine {
  font-size: 12px;
  color: var(--muted);
  margin-top: 4px;
}

.inlineLbl {
  display: grid;
  gap: 6px;
  font-size: 12px;
}

.inlineInput {
  min-width: 180px;
}

.inlineSelect {
  min-width: 110px;
}

.pillarGrid {
  display: grid;
  grid-template-columns: repeat(4, minmax(130px, 1fr));
  gap: 10px;
  min-width: 560px;
}

.pillarBox {
  border: 1px solid var(--b2);
  border-radius: 10px;
  padding: 8px;
  display: grid;
  gap: 8px;
  background: rgba(0,0,0,0.15);
}

.pillarLabel {
  font-size: 11px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--muted);
}

.pillarGz {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  white-space: pre-line;
  line-height: 1.25;
}

.pillarHex {
  display: grid;
  grid-template-columns: minmax(28px, auto) 1fr minmax(28px, auto);
  gap: 6px;
  align-items: center;
}

.pillarHex.clickable {
  cursor: pointer;
}
.pillarHex.clickable:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.6);
  outline-offset: 3px;
  border-radius: 8px;
}

.hexNum {
  font-size: 12px;
  color: var(--muted);
  min-width: 28px;
}

.hexName {
  font-size: 12px;
  color: var(--muted);
  text-align: right;
  min-width: 28px;
}

.cjkText {
  font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei",
    ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}

.destinyBox {
  width: 100%;
  min-height: 140px;
  background: rgba(0,0,0,0.15);
  border: 1px solid var(--b2);
  border-radius: 10px;
  padding: 10px;
  color: var(--txt);
  resize: vertical;
}

.interpretation-error {
  color: rgb(245 158 11);
}

.placeholder {
  font-size: 12px;
  color: var(--muted);
  padding: 8px 0;
}

.flowHeader {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.meta { font-size: 13px; color: var(--muted); margin-top: 4px; }
.topRight { display: flex; gap: 10px; align-items: center; }

.sec { margin-top: 14px; }
.secTitle {
  font-size: 14px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--muted);
}
.secBody { margin-top: 6px; font-size: 15px; line-height: 1.45; }
.secActions { margin-top: 10px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New",
    "Noto Sans Mono CJK SC", "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Noto Sans SC",
    "Microsoft YaHei", monospace;
}

@media (max-width: 980px) {
  .wrap {
    flex-direction: column;
  }

  .side {
    width: 100%;
  }

  .main {
    width: 100%;
  }

  .card {
    max-width: 100%;
  }
}

@media (max-width: 680px) {
  .wrap {
    padding: 12px;
    gap: 12px;
  }

  .appHeader {
    padding: 12px 12px 0 12px;
  }

  .panel {
    padding: 10px;
  }

  .panelHeader {
    align-items: flex-start;
  }

  .panelControls {
    width: 100%;
    justify-content: flex-start;
  }

  .inlineInput,
  .inlineSelect {
    min-width: 0;
    width: 100%;
  }

  .pillarGrid {
    grid-template-columns: repeat(2, minmax(120px, 1fr));
    min-width: 0;
  }

  .topRight {
    flex-wrap: wrap;
    justify-content: flex-start;
  }
}

/* Mobile device widths (375px - 430px) */
@media (max-width: 430px) {
  .wrap {
    padding: 12px;
    padding-left: calc(12px + env(safe-area-inset-left, 0px));
    padding-right: calc(12px + env(safe-area-inset-right, 0px));
    gap: 12px;
  }

  .app-nav {
    padding-left: calc(18px + env(safe-area-inset-left, 0px));
    padding-right: calc(18px + env(safe-area-inset-right, 0px));
  }

  .pillarGrid {
    grid-template-columns: 1fr;
    min-width: 0;
  }
}
</style>
