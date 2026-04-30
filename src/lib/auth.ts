import { createClient, type Session } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;
const redirectTo = import.meta.env.VITE_SUPABASE_AUTH_REDIRECT_TO as string | undefined;

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

let anonymousAppUserId: string | null = null;

export function createAnonymousAppUserId() {
  return `$RCAnonymousID:${crypto.randomUUID().replace(/-/g, "")}`;
}

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl!, supabaseAnonKey!, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    })
  : null;

export function getSupabaseClient() {
  if (!supabase) {
    throw new Error("Supabase auth is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.");
  }

  return supabase;
}

export async function sendMagicLink(email: string) {
  const client = getSupabaseClient();
  const normalizedEmail = email.trim();
  if (!normalizedEmail) {
    throw new Error("Email is required.");
  }

  const { error } = await client.auth.signInWithOtp({
    email: normalizedEmail,
    options: {
      emailRedirectTo: redirectTo || window.location.href,
      shouldCreateUser: true,
    },
  });

  if (error) throw error;
}

export async function verifyEmailOtp(email: string, token: string) {
  const client = getSupabaseClient();
  const { data, error } = await client.auth.verifyOtp({
    email: email.trim(),
    token: token.trim(),
    type: "email",
  });

  if (error) throw error;
  return data;
}

export async function signOut() {
  if (!supabase) return;
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}

export async function getSession() {
  if (!supabase) return null;
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session;
}

export function getAuthBearerToken(session: Session | null | undefined) {
  return session?.access_token ?? null;
}

export function getOrCreateAnonymousAppUserId() {
  if (!anonymousAppUserId) {
    anonymousAppUserId = createAnonymousAppUserId();
  }
  return anonymousAppUserId;
}
