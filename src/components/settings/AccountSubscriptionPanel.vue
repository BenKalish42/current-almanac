<script setup lang="ts">
import { computed, ref } from "vue";
import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/authStore";
import { useSubscriptionStore } from "@/stores/subscriptionStore";

const authStore = useAuthStore();
const subscriptionStore = useSubscriptionStore();

const email = ref("");
const otpToken = ref("");
const signInNotice = ref<string | null>(null);
const verifyNotice = ref<string | null>(null);
const actionError = ref<string | null>(null);

const {
  user,
  isAuthenticated,
  isInitializing: authInitializing,
  isSendingOtp,
  isVerifyingOtp,
} = storeToRefs(authStore);

const {
  status,
  isLoading: subscriptionLoading,
  isBusy,
  managementUrl,
  monthlyPriceLabel,
  paid,
} = storeToRefs(subscriptionStore);

const isWorking = computed(
  () =>
    authInitializing.value ||
    isSendingOtp.value ||
    isVerifyingOtp.value ||
    subscriptionLoading.value ||
    isBusy.value
);

const subscriptionSummary = computed(() => {
  if (paid.value) {
    const storeLabel = status.value.store ? ` via ${status.value.store}` : "";
    return `Current Plus active${storeLabel}.`;
  }

  return `Free tier. Upgrade to Current Plus for ${monthlyPriceLabel.value}.`;
});

async function requestMagicLink() {
  signInNotice.value = null;
  verifyNotice.value = null;
  actionError.value = null;

  try {
    await authStore.sendMagicLink(email.value);
    signInNotice.value = "Check your email for a magic link and one-time code.";
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : "Failed to send sign-in link.";
  }
}

async function verifyCode() {
  verifyNotice.value = null;
  actionError.value = null;

  try {
    await authStore.verifyOtp(email.value, otpToken.value);
    otpToken.value = "";
    verifyNotice.value = "You're signed in and your subscription status is syncing.";
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : "Failed to verify the sign-in code.";
  }
}

async function restorePurchases() {
  actionError.value = null;

  try {
    const result = await subscriptionStore.restorePurchases();
    if (result === "not-authenticated") {
      actionError.value = "Sign in first so purchases can attach to your account.";
      return;
    }
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : "Failed to restore purchases.";
  }
}

async function subscribe() {
  actionError.value = null;

  try {
    const result = await subscriptionStore.presentSubscriptionPaywall();
    if (result === "not-authenticated") {
      actionError.value = "Sign in first so a subscription can unlock all platforms.";
    }
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : "Failed to open subscription checkout.";
  }
}

async function openManagement() {
  actionError.value = null;

  try {
    const result = await subscriptionStore.openManagement();
    if (result === "not-authenticated") {
      actionError.value = "Sign in first to manage your subscription.";
    }
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : "Failed to open subscription management.";
  }
}

async function signOut() {
  actionError.value = null;
  signInNotice.value = null;
  verifyNotice.value = null;

  try {
    await authStore.signOut();
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : "Failed to sign out.";
  }
}
</script>

<template>
  <section class="accountPanel">
    <header class="accountPanelHeader">
      <div>
        <div class="accountPanelEyebrow">Account</div>
        <h3 class="accountPanelTitle">Identity + subscription sync</h3>
      </div>
      <span class="accountPanelBadge" :class="{ 'accountPanelBadge--paid': paid }">
        {{ paid ? "Paid" : "Free" }}
      </span>
    </header>

    <p class="accountPanelCopy">
      Sign in with email so your subscription can follow you across web, desktop, iOS, and Android.
    </p>

    <div v-if="isAuthenticated" class="accountPanelSection">
      <div class="accountRow">
        <span class="accountLabel">Signed in as</span>
        <span class="accountValue">{{ user?.email || "Authenticated user" }}</span>
      </div>
      <div class="accountRow">
        <span class="accountLabel">Plan</span>
        <span class="accountValue">{{ subscriptionSummary }}</span>
      </div>
      <div v-if="managementUrl" class="accountRow">
        <span class="accountLabel">Management</span>
        <span class="accountValue accountValue--subtle">Available for your active billing source</span>
      </div>

      <div class="accountActions">
        <button type="button" class="accountButton accountButton--primary" :disabled="isWorking" @click="subscribe">
          {{ paid ? "Open customer center / offers" : `Subscribe for ${monthlyPriceLabel}` }}
        </button>
        <button type="button" class="accountButton" :disabled="isWorking" @click="restorePurchases">
          Restore purchases
        </button>
        <button type="button" class="accountButton" :disabled="isWorking" @click="openManagement">
          Manage subscription
        </button>
        <button type="button" class="accountButton" :disabled="isWorking" @click="signOut">
          Sign out
        </button>
      </div>
    </div>

    <div v-else class="accountPanelSection accountPanelSection--auth">
      <label class="accountField">
        <span class="accountLabel">Email</span>
        <input
          v-model="email"
          class="accountInput"
          type="email"
          placeholder="you@example.com"
          autocomplete="email"
        />
      </label>

      <div class="accountActions">
        <button
          type="button"
          class="accountButton accountButton--primary"
          :disabled="!email || isWorking"
          @click="requestMagicLink"
        >
          {{ isSendingOtp ? "Sending…" : "Email me a magic link" }}
        </button>
      </div>

      <label class="accountField">
        <span class="accountLabel">One-time code</span>
        <input
          v-model="otpToken"
          class="accountInput"
          inputmode="numeric"
          type="text"
          placeholder="123456"
          autocomplete="one-time-code"
        />
      </label>

      <div class="accountActions">
        <button
          type="button"
          class="accountButton"
          :disabled="!email || !otpToken || isWorking"
          @click="verifyCode"
        >
          {{ isVerifyingOtp ? "Verifying…" : "Verify code" }}
        </button>
      </div>
    </div>

    <p v-if="signInNotice" class="accountNotice">{{ signInNotice }}</p>
    <p v-if="verifyNotice" class="accountNotice accountNotice--success">{{ verifyNotice }}</p>
    <p v-if="actionError" class="accountNotice accountNotice--error">{{ actionError }}</p>
  </section>
</template>

<style scoped>
.accountPanel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--b2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
}

.accountPanelHeader {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.accountPanelEyebrow {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.accountPanelTitle {
  margin: 4px 0 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--txt);
}

.accountPanelBadge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 54px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--b2);
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.accountPanelBadge--paid {
  border-color: rgba(74, 155, 122, 0.45);
  color: #b9f0ce;
  background: rgba(74, 155, 122, 0.16);
}

.accountPanelCopy {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: var(--muted);
}

.accountPanelSection {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.accountPanelSection--auth {
  padding-top: 4px;
}

.accountRow,
.accountField {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.accountLabel {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--muted);
}

.accountValue {
  font-size: 13px;
  line-height: 1.4;
  color: var(--txt);
}

.accountValue--subtle {
  color: var(--muted);
}

.accountInput {
  width: 100%;
  box-sizing: border-box;
  min-height: 40px;
  padding: 10px 12px;
  border: 1px solid var(--b2);
  border-radius: 10px;
  background: var(--color-daoist-surface);
  color: var(--color-daoist-text);
  font-size: 14px;
}

.accountActions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.accountButton {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--b2);
  background: transparent;
  color: var(--txt);
  cursor: pointer;
  font-size: 13px;
}

.accountButton:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.accountButton--primary {
  background: rgba(74, 155, 122, 0.18);
  border-color: rgba(74, 155, 122, 0.35);
}

.accountNotice {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--muted);
}

.accountNotice--success {
  color: #b9f0ce;
}

.accountNotice--error {
  color: #f1b6b6;
}
</style>
