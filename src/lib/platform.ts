import { Capacitor } from "@capacitor/core";

export type RuntimePlatform = "web" | "ios" | "android" | "desktop";

export function getRuntimePlatform(): RuntimePlatform {
  if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
    return "desktop";
  }

  if (Capacitor.isNativePlatform()) {
    const nativePlatform = Capacitor.getPlatform();
    if (nativePlatform === "ios" || nativePlatform === "android") {
      return nativePlatform;
    }
  }

  return "web";
}

export function isNativeMobilePlatform() {
  const platform = getRuntimePlatform();
  return platform === "ios" || platform === "android";
}

export function isDesktopPlatform() {
  return getRuntimePlatform() === "desktop";
}

export function isWebLikePlatform() {
  const platform = getRuntimePlatform();
  return platform === "web" || platform === "desktop";
}
