import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { CURRENT_PLUS_ENTITLEMENT, emptyEntitlementSnapshot, normalizeCustomerInfo, type EntitlementSnapshot } from "@/lib/entitlements";
import { toEntitlementSnapshot } from "@/lib/backendSubscription";
import { useAuthStore } from "@/stores/authStore";
import { fetchAuthSession, fetchSubscriptionState } from "@/services/apiClient";
import {
  getRevenueCatCustomerInfo,
  showSubscriptionManagement,
  purchaseCurrentPlus,
  restoreRevenueCatPurchases,
} from "@/services/revenueCatService";

export const useSubscriptionStore = defineStore("subscription", () => {
  const status = ref<EntitlementSnapshot>(emptyEntitlementSnapshot());
  const isLoading = ref(false);
  const isBusy = ref(false);
  const error = ref<string | null>(null);

  const paid = computed(() => status.value.isPaid);
  const managementUrl = computed(() => status.value.managementUrl);
  const monthlyPriceLabel = computed(() => "$13.31 / month");

  function applyBackendState(backendState: Parameters<typeof toEntitlementSnapshot>[0]) {
    status.value = toEntitlementSnapshot(backendState);
  }

  async function refreshSubscriptionState() {
    const authStore = useAuthStore();
    const accessToken = authStore.session?.access_token ?? null;
    if (!authStore.userId || !accessToken) {
      status.value = emptyEntitlementSnapshot();
      return null;
    }

    const backendState = await fetchSubscriptionState(accessToken);
    applyBackendState(backendState);
    return backendState;
  }

  async function initialize() {
    const authStore = useAuthStore();
    isLoading.value = true;
    error.value = null;

    try {
      if (!authStore.initialized) {
        await authStore.initialize();
      }

      if (!authStore.userId) {
        status.value = emptyEntitlementSnapshot();
        return;
      }

      const accessToken = authStore.session?.access_token ?? null;
      if (!accessToken) {
        status.value = emptyEntitlementSnapshot();
        return;
      }

      const sessionResponse = await fetchAuthSession(accessToken);
      if (sessionResponse.subscription) {
        applyBackendState(sessionResponse.subscription);
        return;
      }

      await refreshSubscriptionState();
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to initialize subscriptions.";
      status.value = emptyEntitlementSnapshot();
    } finally {
      isLoading.value = false;
    }
  }

  function hasEntitlement(identifier = CURRENT_PLUS_ENTITLEMENT) {
    return paid.value && status.value.activeEntitlementIds.includes(identifier);
  }

  async function presentSubscriptionPaywallAction() {
    const authStore = useAuthStore();
    if (!authStore.userId) {
      return "not-authenticated" as const;
    }

    isBusy.value = true;
    error.value = null;
    try {
      await purchaseCurrentPlus(authStore.userId);

      const customerInfo = await getRevenueCatCustomerInfo(authStore.userId);
      if (customerInfo) {
        status.value = normalizeCustomerInfo(customerInfo);
      }

      await refreshSubscriptionState();
      return "completed" as const;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Unable to start subscription purchase.";
      throw err;
    } finally {
      isBusy.value = false;
    }
  }

  async function restorePurchasesAction() {
    const authStore = useAuthStore();
    if (!authStore.userId) {
      return "not-authenticated" as const;
    }

    isBusy.value = true;
    error.value = null;
    try {
      const restored = await restoreRevenueCatPurchases(authStore.userId);
      if (restored) {
        status.value = normalizeCustomerInfo(restored);
      }

      await refreshSubscriptionState();
      return "completed" as const;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Unable to restore purchases.";
      throw err;
    } finally {
      isBusy.value = false;
    }
  }

  async function openManagementAction() {
    const authStore = useAuthStore();
    if (!authStore.userId) {
      return "not-authenticated" as const;
    }

    error.value = null;
    try {
      await showSubscriptionManagement(managementUrl.value ?? undefined);
      return "completed" as const;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Unable to open subscription management.";
      throw err;
    }
  }

  return {
    status,
    isLoading,
    isBusy,
    error,
    paid,
    managementUrl,
    monthlyPriceLabel,
    initialize,
    refreshSubscriptionState,
    hasEntitlement,
    presentSubscriptionPaywall: presentSubscriptionPaywallAction,
    restorePurchases: restorePurchasesAction,
    openManagement: openManagementAction,
  };
});
