import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      redirect: "/astrology",
    },
    {
      path: "/astrology",
      name: "astrology",
      component: () => import("@/views/HomeView.vue"),
    },
    {
      path: "/hexagrams",
      name: "hexagrams",
      component: () => import("@/views/HexagramCenterView.vue"),
    },
    {
      path: "/alchemy",
      name: "alchemy",
      component: () => import("@/views/AlchemyView.vue"),
    },
    {
      // Legacy alias — redirect to the Workbench.
      path: "/ai",
      redirect: "/workbench",
    },
    {
      // Pillar 3 — Sovereign Courtyard (Matrix shell).
      path: "/intelligence",
      name: "intelligence",
      component: () => import("@/views/IntelligenceView.vue"),
    },
    {
      // Power-user Workbench — multi-family LLM + RAG.
      path: "/workbench",
      name: "workbench",
      component: () => import("@/views/WorkbenchView.vue"),
    },
  ],
});

export default router;
