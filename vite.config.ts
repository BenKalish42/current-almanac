/// <reference types="vitest" />
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const netlifyTarget = env.VITE_NETLIFY_PROXY_TARGET || "http://localhost:8888";
  const tauriHost = process.env.TAURI_DEV_HOST;

  return {
    base: "/",
    clearScreen: false,
    plugins: [
      vue(),
      tailwindcss(),
      VitePWA({
        registerType: "autoUpdate",
        includeAssets: ["favicon.svg", "pwa-192x192.png", "pwa-512x512.png", "apple-touch-icon.png"],
        manifest: {
          name: "Current Almanac",
          short_name: "Current",
          description: "Offline-first Daoist astrology, alchemy, and Current Flow companion.",
          theme_color: "#0b1020",
          background_color: "#0b1020",
          display: "standalone",
          orientation: "portrait",
          start_url: "/",
          scope: "/",
          icons: [
            {
              src: "/pwa-192x192.png",
              sizes: "192x192",
              type: "image/png",
            },
            {
              src: "/pwa-512x512.png",
              sizes: "512x512",
              type: "image/png",
            },
            {
              src: "/maskable-512x512.png",
              sizes: "512x512",
              type: "image/png",
              purpose: "maskable",
            },
          ],
        },
        workbox: {
          globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
          navigateFallbackDenylist: [/^\/api\//, /^\/\.netlify\//],
        },
        devOptions: {
          enabled: false,
        },
      }),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 5173,
      strictPort: true,
      host: tauriHost || false,
      hmr: tauriHost
        ? {
            protocol: "ws",
            host: tauriHost,
            port: 1421,
          }
        : undefined,
      watch: {
        ignored: ["**/src-tauri/**"],
      },
      proxy: {
        "/.netlify/functions": {
          target: netlifyTarget,
          changeOrigin: true,
        },
        "/api": {
          target: env.VITE_API_URL || "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
    build: {
      target: process.env.TAURI_ENV_PLATFORM === "windows" ? "chrome111" : "safari16.4",
      minify: !process.env.TAURI_ENV_DEBUG ? "esbuild" : false,
      sourcemap: !!process.env.TAURI_ENV_DEBUG,
    },
    test: {
      globals: true,
      environment: "node",
    },
  };
});
