<script setup lang="ts">
import { computed } from "vue";
import { useSubscriptionStore } from "@/stores/subscriptionStore";

const props = withDefaults(
  defineProps<{
    entitlement?: string;
    title?: string;
    message?: string;
    ctaLabel?: string;
  }>(),
  {
    entitlement: "current_plus",
    title: "Current+ required",
    message: "Sign in and subscribe to unlock this feature on web, desktop, iOS, and Android.",
    ctaLabel: "Unlock Current+",
  }
);

const subscriptionStore = useSubscriptionStore();
const visible = computed(() => !subscriptionStore.hasEntitlement(props.entitlement));

async function openSubscriptionSettings() {
  await subscriptionStore.presentSubscriptionPaywall();
}
</script>

<template>
  <slot v-if="!visible" />
  <div v-else class="premiumGate">
    <div class="premiumGateBadge">{{ props.entitlement }}</div>
    <h3 class="premiumGateTitle">{{ props.title }}</h3>
    <p class="premiumGateText">{{ props.message }}</p>
    <button
      type="button"
      class="premiumGateButton"
      :disabled="subscriptionStore.isBusy"
      @click="openSubscriptionSettings"
    >
      {{ subscriptionStore.isBusy ? "Checking plan…" : props.ctaLabel }}
    </button>
  </div>
</template>

<style scoped>
.premiumGate {
  display: grid;
  gap: 10px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid rgba(90, 180, 140, 0.25);
  background: rgba(16, 30, 40, 0.55);
}

.premiumGateBadge {
  width: fit-content;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(52, 211, 153, 0.14);
  color: #9ff2d1;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.premiumGateTitle {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--txt);
}

.premiumGateText {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.premiumGateButton {
  justify-self: start;
  padding: 10px 14px;
  border: 1px solid rgba(52, 211, 153, 0.35);
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(52, 211, 153, 0.25), rgba(56, 189, 248, 0.2));
  color: var(--txt);
  font-weight: 700;
  cursor: pointer;
}

.premiumGateButton:disabled {
  opacity: 0.6;
  cursor: wait;
}
</style>
