import { createClient } from "@supabase/supabase-js";
import { w as writable } from "./index2.js";
const supabaseUrl = "https://tzaqdnswbrczijajcnks.supabase.co";
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6YXFkbnN3YnJjemlqYWpjbmtzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI0NTM1NTUsImV4cCI6MjA2ODAyOTU1NX0.VexF6qS_T_6EOBFjPJzHdw1UggbsG_oPdBOmGqkeREk";
const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    // Auto refresh tokens
    autoRefreshToken: true,
    // Persist session in localStorage
    persistSession: true,
    // Detect session in URL (for OAuth callbacks)
    detectSessionInUrl: true,
    // Flow type for OAuth
    flowType: "pkce"
  }
});
const user = writable(null);
const loading = writable(true);
const error = writable(null);
const initializeAuth = async () => {
  try {
    console.log("Initializing auth...");
    loading.set(true);
    error.set(null);
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error("Auth initialization timeout")), 1e4);
    });
    const sessionPromise = supabase.auth.getSession();
    const { data: { session }, error: sessionError } = await Promise.race([
      sessionPromise,
      timeoutPromise
    ]);
    if (sessionError) {
      console.error("Error getting session:", sessionError);
      error.set(sessionError);
    } else {
      console.log("Session found:", session?.user?.email);
      user.set(session?.user ?? null);
    }
  } catch (err) {
    console.error("Auth initialization error:", err);
    error.set(err);
  } finally {
    console.log("Auth initialization complete, setting loading to false");
    loading.set(false);
  }
};
supabase.auth.onAuthStateChange(async (event, session) => {
  console.log("Auth state changed:", event, session?.user?.email);
  try {
    error.set(null);
    switch (event) {
      case "SIGNED_IN":
        console.log("User signed in, setting user and loading to false");
        user.set(session?.user ?? null);
        loading.set(false);
        break;
      case "SIGNED_OUT":
        console.log("User signed out, clearing user and setting loading to false");
        user.set(null);
        loading.set(false);
        if (typeof window !== "undefined") {
          localStorage.removeItem("auth_token");
          localStorage.removeItem("user_id");
        }
        break;
      case "TOKEN_REFRESHED":
        console.log("Token refreshed, updating user");
        user.set(session?.user ?? null);
        break;
      case "USER_UPDATED":
        console.log("User updated, updating user");
        user.set(session?.user ?? null);
        break;
      case "INITIAL_SESSION":
        console.log("Initial session, setting user and loading to false");
        user.set(session?.user ?? null);
        loading.set(false);
        break;
      default:
        console.log("Unknown auth event:", event, "ensuring loading is false");
        loading.set(false);
        break;
    }
  } catch (err) {
    console.error("Auth state change error:", err);
    error.set(err);
    loading.set(false);
  }
});
initializeAuth();
export {
  error as e,
  loading as l,
  user as u
};
