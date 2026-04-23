import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./style.css";
import "./assets/themes/data-theme-tokens.css";
import "./assets/themes/cosmic-crawl-extras.css";
import "./assets/themes/zhang-zhung-extras.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");

// Capacitor native: Status Bar (dark style) + hide Splash Screen when mounted
(async () => {
  try {
    const { Capacitor } = await import("@capacitor/core");
    if (Capacitor.isNativePlatform()) {
      const { StatusBar, Style } = await import("@capacitor/status-bar");
      await StatusBar.setStyle({ style: Style.Dark });

      const { SplashScreen } = await import("@capacitor/splash-screen");
      await SplashScreen.hide();
    }
  } catch {
    // Capacitor not available (web-only build)
  }
})();
