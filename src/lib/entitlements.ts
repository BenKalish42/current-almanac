import type { CustomerInfo, EntitlementInfo } from "@revenuecat/purchases-js";

export const CURRENT_PLUS_ENTITLEMENT = "current_plus";
export const DEFAULT_ENTITLEMENT_KEY = CURRENT_PLUS_ENTITLEMENT;

export type EntitlementSnapshot = {
  isPaid: boolean;
  managementUrl: string | null;
  entitlements: Record<string, EntitlementState>;
  activeEntitlementIds: string[];
  activeProductIds: string[];
  store: string | null;
  expiresAt: string | null;
  willRenew: boolean | null;
  billingIssueDetectedAt: string | null;
  originalAppUserId: string | null;
};

export type EntitlementState = {
  id: string;
  isActive: boolean;
  productIdentifier: string;
  store: string | null;
  expiresAt: string | null;
  willRenew: boolean;
  billingIssueDetectedAt: string | null;
};

export type BackendEntitlementSnapshot = {
  user_id: string;
  revenuecat_app_user_id: string | null;
  is_paid: boolean;
  management_url: string | null;
  active_entitlements: Record<string, BackendEntitlementState>;
  active_product_ids: string[];
  store: string | null;
  expires_at: string | null;
  will_renew: boolean | null;
  billing_issue_detected_at: string | null;
  original_app_user_id: string | null;
  updated_at: string | null;
};

export type BackendEntitlementState = {
  id: string;
  is_active: boolean;
  product_identifier: string;
  store: string | null;
  expires_at: string | null;
  will_renew: boolean | null;
  billing_issue_detected_at: string | null;
};

export type NormalizedSubscriptionState = {
  paid: boolean;
  entitlementIds: string[];
  entitlements: Record<string, EntitlementState>;
  productIds: string[];
  managementUrl: string | null;
  store: string | null;
  expiresAt: string | null;
  willRenew: boolean | null;
  billingIssueDetectedAt: string | null;
  originalAppUserId: string | null;
  updatedAt: string | null;
};

function toIsoOrNull(value: Date | string | null | undefined) {
  if (!value) return null;
  if (value instanceof Date) return value.toISOString();

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function normalizeEntitlementState(id: string, entitlement: EntitlementInfo): EntitlementState {
  return {
    id,
    isActive: entitlement.isActive,
    productIdentifier: entitlement.productIdentifier,
    store: entitlement.store ?? null,
    expiresAt: toIsoOrNull(entitlement.expirationDate),
    willRenew: entitlement.willRenew,
    billingIssueDetectedAt: toIsoOrNull(entitlement.billingIssueDetectedAt),
  };
}

export function normalizeCustomerInfo(customerInfo: CustomerInfo): EntitlementSnapshot {
  const entitlements = Object.entries(customerInfo.entitlements.all).reduce<Record<string, EntitlementState>>(
    (acc, [id, entitlement]) => {
      acc[id] = normalizeEntitlementState(id, entitlement);
      return acc;
    },
    {}
  );

  const activeEntitlements = Object.values(entitlements).filter((entitlement) => entitlement.isActive);
  const currentPlus = entitlements[CURRENT_PLUS_ENTITLEMENT] ?? null;

  return {
    isPaid: Boolean(currentPlus?.isActive ?? activeEntitlements.length > 0),
    managementUrl: customerInfo.managementURL ?? null,
    entitlements,
    activeEntitlementIds: activeEntitlements.map((entitlement) => entitlement.id),
    activeProductIds: [...customerInfo.activeSubscriptions],
    store: currentPlus?.store ?? activeEntitlements[0]?.store ?? null,
    expiresAt: currentPlus?.expiresAt ?? activeEntitlements[0]?.expiresAt ?? null,
    willRenew:
      currentPlus?.willRenew ??
      (activeEntitlements.length > 0 ? activeEntitlements.some((entitlement) => entitlement.willRenew) : null),
    billingIssueDetectedAt:
      currentPlus?.billingIssueDetectedAt ??
      activeEntitlements.find((entitlement) => entitlement.billingIssueDetectedAt)?.billingIssueDetectedAt ??
      null,
    originalAppUserId: customerInfo.originalAppUserId ?? null,
  };
}

export function emptyEntitlementSnapshot(): EntitlementSnapshot {
  return {
    isPaid: false,
    managementUrl: null,
    entitlements: {},
    activeEntitlementIds: [],
    activeProductIds: [],
    store: null,
    expiresAt: null,
    willRenew: null,
    billingIssueDetectedAt: null,
    originalAppUserId: null,
  };
}

export function emptySubscriptionState(): NormalizedSubscriptionState {
  return {
    paid: false,
    entitlementIds: [],
    entitlements: {},
    productIds: [],
    managementUrl: null,
    store: null,
    expiresAt: null,
    willRenew: null,
    billingIssueDetectedAt: null,
    originalAppUserId: null,
    updatedAt: null,
  };
}

export function subscriptionStateFromSnapshot(
  snapshot: BackendEntitlementSnapshot | null,
  entitlementKey = DEFAULT_ENTITLEMENT_KEY
): NormalizedSubscriptionState {
  if (!snapshot) {
    return emptySubscriptionState();
  }

  const entitlements = Object.entries(snapshot.active_entitlements ?? {}).reduce<Record<string, EntitlementState>>(
    (acc, [id, entitlement]) => {
      acc[id] = {
        id: entitlement.id,
        isActive: entitlement.is_active,
        productIdentifier: entitlement.product_identifier ?? "",
        store: entitlement.store,
        expiresAt: entitlement.expires_at,
        willRenew: entitlement.will_renew ?? false,
        billingIssueDetectedAt: entitlement.billing_issue_detected_at,
      };
      return acc;
    },
    {}
  );

  const activeIds = Object.values(entitlements)
    .filter((entitlement) => entitlement.isActive)
    .map((entitlement) => entitlement.id);

  const preferredEntitlement = entitlements[entitlementKey] ?? Object.values(entitlements)[0] ?? null;

  return {
    paid: snapshot.is_paid,
    entitlementIds: activeIds,
    entitlements,
    productIds: snapshot.active_product_ids ?? [],
    managementUrl: snapshot.management_url ?? null,
    store: preferredEntitlement?.store ?? snapshot.store ?? null,
    expiresAt: preferredEntitlement?.expiresAt ?? snapshot.expires_at ?? null,
    willRenew: preferredEntitlement?.willRenew ?? snapshot.will_renew ?? null,
    billingIssueDetectedAt:
      preferredEntitlement?.billingIssueDetectedAt ?? snapshot.billing_issue_detected_at ?? null,
    originalAppUserId: snapshot.original_app_user_id ?? null,
    updatedAt: snapshot.updated_at ?? null,
  };
}
