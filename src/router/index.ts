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
      path: "/alchemy",
      name: "alchemy",
      component: () => import("@/views/AlchemyView.vue"),
    },
    {
      path: "/ai",
      name: "ai",
      component: () => import("@/views/AIChatView.vue"),
    },
  ],
});

export default router;
