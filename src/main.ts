import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./style.css";
import "./assets/themes/data-theme-tokens.css";
import "./assets/themes/cosmic-crawl-extras.css";
import { CapacitorUpdater } from "@capgo/capacitor-updater";
import { registerPwaServiceWorker } from "@/lib/pwa";
import { useAuthStore } from "@/stores/authStore";
import { useSubscriptionStore } from "@/stores/subscriptionStore";

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);
app.use(router);
app.mount("#app");
void registerPwaServiceWorker();

const authStore = useAuthStore(pinia);
const subscriptionStore = useSubscriptionStore(pinia);

void authStore.initialize().then(async () => {
  try {
    await subscriptionStore.initialize();
  } catch (error) {
    console.error("[subscriptionStore.initialize]", error);
  }
});

// Capacitor native: Status Bar (dark style) + hide Splash Screen when mounted
(async () => {
  try {
    const { Capacitor } = await import("@capacitor/core");
    if (Capacitor.isNativePlatform()) {
      await CapacitorUpdater.notifyAppReady();

      const { StatusBar, Style } = await import("@capacitor/status-bar");
      await StatusBar.setStyle({ style: Style.Dark });

      const { SplashScreen } = await import("@capacitor/splash-screen");
      await SplashScreen.hide();
    }
  } catch {
    // Capacitor not available (web-only build)
  }
})();
