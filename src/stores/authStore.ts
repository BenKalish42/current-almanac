import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { Session, User } from "@supabase/supabase-js";
import { getSupabaseClient, isSupabaseConfigured, sendMagicLink as sendMagicLinkEmail, signOut as signOutSession, verifyEmailOtp } from "@/lib/auth";

type AuthStatus = "idle" | "loading" | "authenticated" | "anonymous" | "error";

export const useAuthStore = defineStore("auth", () => {
  const status = ref<AuthStatus>("idle");
  const authError = ref<string | null>(null);
  const session = ref<Session | null>(null);
  const user = ref<User | null>(null);
  const isInitializing = ref(false);
  const isSendingOtp = ref(false);
  const isVerifyingOtp = ref(false);
  const initialized = ref(false);

  let unsubscribeAuthListener: (() => void) | null = null;

  const isAuthenticated = computed(() => !!user.value);
  const userId = computed(() => user.value?.id ?? null);

  function applySession(nextSession: Session | null) {
    session.value = nextSession;
    user.value = nextSession?.user ?? null;
    status.value = user.value ? "authenticated" : "anonymous";
  }

  async function initialize() {
    if (initialized.value) return;

    isInitializing.value = true;
    authError.value = null;

    if (!isSupabaseConfigured) {
      status.value = "anonymous";
      initialized.value = true;
      isInitializing.value = false;
      return;
    }

    try {
      const supabase = getSupabaseClient();
      const {
        data: { session: currentSession },
      } = await supabase.auth.getSession();
      applySession(currentSession);

      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange((_event, nextSession: Session | null) => {
        applySession(nextSession);
      });

      unsubscribeAuthListener = () => subscription.unsubscribe();
      initialized.value = true;
    } catch (error) {
      status.value = "error";
      authError.value = error instanceof Error ? error.message : "Failed to initialize authentication.";
      throw error;
    } finally {
      isInitializing.value = false;
    }
  }

  async function sendMagicLink(email: string) {
    isSendingOtp.value = true;
    authError.value = null;
    try {
      await sendMagicLinkEmail(email);
    } catch (error) {
      authError.value = error instanceof Error ? error.message : "Failed to send sign-in email.";
      throw error;
    } finally {
      isSendingOtp.value = false;
    }
  }

  async function verifyOtp(email: string, token: string) {
    isVerifyingOtp.value = true;
    authError.value = null;
    try {
      await verifyEmailOtp(email, token);
    } catch (error) {
      authError.value = error instanceof Error ? error.message : "Failed to verify code.";
      throw error;
    } finally {
      isVerifyingOtp.value = false;
    }
  }

  async function signOut() {
    authError.value = null;
    try {
      await signOutSession();
      applySession(null);
    } catch (error) {
      authError.value = error instanceof Error ? error.message : "Failed to sign out.";
      throw error;
    }
  }

  function dispose() {
    unsubscribeAuthListener?.();
    unsubscribeAuthListener = null;
  }

  return {
    status,
    authError,
    session,
    user,
    isInitializing,
    isSendingOtp,
    isVerifyingOtp,
    initialized,
    isAuthenticated,
    userId,
    initialize,
    sendMagicLink,
    verifyOtp,
    signOut,
    dispose,
  };
});
