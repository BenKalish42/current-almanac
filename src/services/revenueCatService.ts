import { Browser } from "@capacitor/browser";
import { toRaw } from "vue";
import { Purchases } from "@revenuecat/purchases-capacitor";
import { RevenueCatUI, type PaywallResult } from "@revenuecat/purchases-capacitor-ui";
import { Purchases as WebPurchases, LogLevel, type CustomerInfo, type Offering } from "@revenuecat/purchases-js";
import { CURRENT_PLUS_ENTITLEMENT } from "@/lib/entitlements";
import { createAnonymousAppUserId } from "@/lib/auth";
import { isNativeMobilePlatform } from "@/lib/platform";

export type RevenueCatCustomerInfo =
  | CustomerInfo
  | Awaited<ReturnType<typeof Purchases.getCustomerInfo>>["customerInfo"];

let configuredAppUserId: string | null = null;
let configuredWebClient: InstanceType<typeof WebPurchases> | null = null;

function getRevenueCatApiKey() {
  return import.meta.env.VITE_REVENUECAT_PUBLIC_API_KEY as string | undefined;
}

function getRevenueCatWebApiKey() {
  return (import.meta.env.VITE_REVENUECAT_WEB_API_KEY as string | undefined) ?? getRevenueCatApiKey();
}

function ensureApiKey(value: string | undefined, label: string) {
  if (!value) {
    throw new Error(`${label} is not configured. Add it to .env before testing subscriptions.`);
  }
  return value;
}

function getFallbackAnonymousUserId() {
  try {
    const key = "current.subscription.anonAppUserId";
    const existing = localStorage.getItem(key);
    if (existing) return existing;
    const generated = createAnonymousAppUserId();
    localStorage.setItem(key, generated);
    return generated;
  } catch {
    return createAnonymousAppUserId();
  }
}

async function getWebClient(appUserId: string) {
  if (configuredWebClient && configuredAppUserId === appUserId) {
    return configuredWebClient;
  }

  const apiKey = ensureApiKey(getRevenueCatWebApiKey(), "VITE_REVENUECAT_WEB_API_KEY");
  WebPurchases.setLogLevel(LogLevel.Info);
  configuredWebClient = WebPurchases.configure({
    apiKey,
    appUserId,
  });
  configuredAppUserId = appUserId;
  return configuredWebClient;
}

export async function initializeRevenueCatForCurrentSession(appUserId?: string | null) {
  const resolvedUserId = appUserId ?? configuredAppUserId ?? getFallbackAnonymousUserId();
  await configureRevenueCat(resolvedUserId);
  return loadRevenueCatSnapshot(resolvedUserId);
}

export async function configureRevenueCat(appUserId: string) {
  if (!appUserId) return;

  if (isNativeMobilePlatform()) {
    const apiKey = ensureApiKey(getRevenueCatApiKey(), "VITE_REVENUECAT_PUBLIC_API_KEY");
    if (configuredAppUserId === appUserId) return;

    await Purchases.setLogLevel({ level: "DEBUG" as never });
    await Purchases.configure({
      apiKey,
      appUserID: appUserId,
      shouldShowInAppMessagesAutomatically: true,
    });
    configuredAppUserId = appUserId;
    return;
  }

  await getWebClient(appUserId);
}

export async function syncRevenueCatIdentity(appUserId: string) {
  if (!appUserId) {
    return initializeRevenueCatForCurrentSession(null);
  }

  await configureRevenueCat(appUserId);

  if (isNativeMobilePlatform()) {
    const result = await Purchases.logIn({ appUserID: appUserId });
    configuredAppUserId = appUserId;
    return result.customerInfo;
  }

  const client = await getWebClient(appUserId);
  const result = await client.identifyUser(appUserId);
  configuredAppUserId = appUserId;
  return result.customerInfo;
}

export async function loadRevenueCatSnapshot(appUserId?: string | null): Promise<CustomerInfo | null> {
  const resolvedUserId = appUserId ?? configuredAppUserId ?? null;
  if (!resolvedUserId) return null;
  return getRevenueCatCustomerInfo(resolvedUserId);
}

export async function getRevenueCatCustomerInfo(appUserId: string): Promise<CustomerInfo | null> {
  if (!appUserId) return null;
  await configureRevenueCat(appUserId);

  if (isNativeMobilePlatform()) {
    const result = await Purchases.getCustomerInfo();
    return result.customerInfo as unknown as CustomerInfo;
  }

  const client = await getWebClient(appUserId);
  return client.getCustomerInfo();
}

export async function presentNativePaywall(options?: {
  requiredEntitlementIdentifier?: string;
}): Promise<CustomerInfo | null> {
  if (!isNativeMobilePlatform()) return null;

  const result: PaywallResult = options?.requiredEntitlementIdentifier
    ? await RevenueCatUI.presentPaywallIfNeeded({
        requiredEntitlementIdentifier: options.requiredEntitlementIdentifier,
        displayCloseButton: true,
      })
    : await RevenueCatUI.presentPaywall({ displayCloseButton: true });

  if (result.result === "PURCHASED" || result.result === "RESTORED") {
    const snapshot = await Purchases.getCustomerInfo();
    return snapshot.customerInfo as unknown as CustomerInfo;
  }

  return null;
}

export async function presentWebPaywall(appUserId?: string | null): Promise<CustomerInfo> {
  const resolvedUserId = appUserId ?? configuredAppUserId ?? getFallbackAnonymousUserId();
  const client = await getWebClient(resolvedUserId);
  const result = await client.presentPaywall({});
  return result.customerInfo;
}

export async function restoreRevenueCatPurchases(appUserId?: string | null): Promise<CustomerInfo | null> {
  const resolvedUserId = appUserId ?? configuredAppUserId ?? getFallbackAnonymousUserId();
  await configureRevenueCat(resolvedUserId);

  if (isNativeMobilePlatform()) {
    const result = await Purchases.restorePurchases();
    return result.customerInfo as unknown as CustomerInfo;
  }

  const client = await getWebClient(resolvedUserId);
  return client.getCustomerInfo();
}

export async function presentCustomerCenter(appUserId?: string | null) {
  const resolvedUserId = appUserId ?? configuredAppUserId ?? getFallbackAnonymousUserId();
  await configureRevenueCat(resolvedUserId);

  if (isNativeMobilePlatform()) {
    await RevenueCatUI.presentCustomerCenter();
    return;
  }

  const customerInfo = await getRevenueCatCustomerInfo(resolvedUserId);
  const managementUrl = customerInfo?.managementURL;
  if (!managementUrl) {
    throw new Error("No subscription management URL is available for this account yet.");
  }

  await Browser.open({ url: managementUrl });
}

export async function getCurrentOffering(appUserId: string): Promise<Offering | null> {
  await configureRevenueCat(appUserId);

  if (isNativeMobilePlatform()) {
    const offerings = await Purchases.getOfferings();
    return offerings.current ? (toRaw(offerings.current) as unknown as Offering) : null;
  }

  const client = await getWebClient(appUserId);
  const offerings = await client.getOfferings();
  return offerings.current;
}

export async function purchaseCurrentPlus(appUserId?: string | null): Promise<CustomerInfo | null> {
  if (isNativeMobilePlatform()) {
    return presentNativePaywall({ requiredEntitlementIdentifier: CURRENT_PLUS_ENTITLEMENT });
  }

  return presentWebPaywall(appUserId);
}

export async function showSubscriptionManagement(preferredUrl?: string | null) {
  if (preferredUrl) {
    await Browser.open({ url: preferredUrl });
    return preferredUrl;
  }

  await presentCustomerCenter();
  const info = await loadRevenueCatSnapshot();
  return info?.managementURL ?? null;
}

export async function openRevenueCatManagement(appUserId?: string | null, preferredUrl?: string | null) {
  if (preferredUrl) {
    await Browser.open({ url: preferredUrl });
    return preferredUrl;
  }

  await presentCustomerCenter(appUserId);
  const info = await loadRevenueCatSnapshot(appUserId);
  return info?.managementURL ?? null;
}

export async function presentSubscriptionPaywall(appUserId?: string | null) {
  if (isNativeMobilePlatform()) {
    return presentNativePaywall({ requiredEntitlementIdentifier: CURRENT_PLUS_ENTITLEMENT });
  }

  return presentWebPaywall(appUserId);
}

export async function identifyRevenueCatUser(options: { appUserId: string; email?: string | null }) {
  return syncRevenueCatIdentity(options.appUserId);
}

export async function logOutRevenueCat() {
  configuredAppUserId = null;
  configuredWebClient = null;

  if (isNativeMobilePlatform()) {
    try {
      await Purchases.logOut();
    } catch {
      // ignore logout failures; anonymous fallback will re-configure on next launch
    }
  }
}
