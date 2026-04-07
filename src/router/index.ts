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
      path: "/ai",
      name: "ai",
      component: () => import("@/views/AIChatView.vue"),
    },
    {
      path: "/community",
      name: "community",
      component: () => import("@/views/CommunityView.vue"),
    },
  ],
});

export default router;
