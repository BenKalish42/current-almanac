import type { ApiSubscriptionState } from "@/services/apiClient";
import type { EntitlementSnapshot } from "@/lib/entitlements";

export function toEntitlementSnapshot(state: ApiSubscriptionState): EntitlementSnapshot {
  const entitlements = Object.fromEntries(
    Object.entries(state.active_entitlements ?? {}).map(([id, entitlement]) => [
      id,
      {
        id: entitlement.id,
        isActive: entitlement.is_active,
        productIdentifier: entitlement.product_identifier ?? "",
        store: entitlement.store,
        expiresAt: entitlement.expires_at,
        willRenew: entitlement.will_renew ?? false,
        billingIssueDetectedAt: entitlement.billing_issue_detected_at,
      },
    ])
  );

  const activeEntitlementIds = Object.values(entitlements)
    .filter((entitlement) => entitlement.isActive)
    .map((entitlement) => entitlement.id);

  return {
    isPaid: state.is_paid,
    managementUrl: state.management_url,
    entitlements,
    activeEntitlementIds,
    activeProductIds: state.active_products ?? [],
    store: state.store,
    expiresAt: state.expires_at,
    willRenew: state.will_renew,
    billingIssueDetectedAt: state.billing_issue_detected_at,
    originalAppUserId: null,
  };
}
