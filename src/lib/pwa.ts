export async function registerPwaServiceWorker() {
  if (typeof window === "undefined") return;

  const { registerSW } = await import("virtual:pwa-register");
  registerSW({
    immediate: true,
    onRegisterError(error) {
      console.error("[pwa] service worker registration failed", error);
    },
  });
}
