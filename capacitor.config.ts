import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.current.almanac",
  appName: "Current Almanac",
  webDir: "dist",
  server: {
    // For local dev: use live server URL when testing on device
    // url: "http://localhost:5173",
    // cleartext: true
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 0,
      launchAutoHide: true,
    },
  },
};

export default config;
