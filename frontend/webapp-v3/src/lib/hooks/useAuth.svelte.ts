import { user, loading, error, signInWithGitHub, signOut, signInWithSlack } from '$lib/auth/supabase';
import { signInWithEmail, signUpWithEmail, signInWithMagicLink } from '$lib/stores/auth';
import type { UseAuthReturn, User } from '$lib/types';

/**
 * Svelte 5 Runes-based useAuth hook
 * 
 * Usage in components:
 * 
 * <script>
 *   const auth = useAuth();
 *   
 *   // Reactive values - automatically update when auth state changes
 *   $effect(() => {
 *     console.log('User changed:', auth.user);
 *   });
 * </script>
 * 
 * {#if auth.isLoading}Loading...{/if}
 * {#if auth.user}Welcome {auth.user.email}!{/if}
 */
export function useAuth(): UseAuthReturn {
  // Reactive state synced with authentication stores
  const state = $state({
    user: null as any,
    isLoading: false,
    error: null as string | null
  });

  // Computed values that automatically update when state changes
  const computedUsername = $derived(state.user?.user_metadata?.name || state.user?.email || 'User');
  const computedIsAuthenticated = $derived(!!state.user);

  // Sync with authentication stores
  $effect(() => {
    const unsubUser = user.subscribe(u => state.user = u);
    const unsubLoading = loading.subscribe(l => state.isLoading = l);
    const unsubError = error.subscribe(e => state.error = e?.message || null);
    
    return () => {
      unsubUser();
      unsubLoading();
      unsubError();
    };
  });

  // Methods required by UseAuthReturn interface
  const signIn = async (email: string, password: string) => {
    try {
      await signInWithEmail(email, password);
    } catch (err) {
      throw new Error('Failed to sign in');
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      await signUpWithEmail(email, password);
    } catch (err) {
      throw new Error('Failed to sign up');
    }
  };

  const signOutMethod = async () => {
    try {
      await signOut();
    } catch (err) {
      throw new Error('Failed to sign out');
    }
  };

  const signInWithGitHubMethod = async () => {
    try {
      await signInWithGitHub();
    } catch (err) {
      throw new Error('Failed to sign in with GitHub');
    }
  };

  const signInWithSlackMethod = async () => {
    try {
      await signInWithSlack();
    } catch (err) {
      throw new Error('Failed to sign in with Slack');
    }
  };

  const getUsername = (): string => {
    return computedUsername;
  };

  const getUserAvatar = (): string | undefined => {
    return state.user?.avatar_url;
  };

  // Subscribe method for compatibility
  const subscribe = (callback: (value: any) => void) => {
    // Return current state immediately
    callback({
      user: state.user,
      isAuthenticated: computedIsAuthenticated,
      isLoading: state.isLoading,
      error: state.error
    });
    
    // Set up subscription for future updates
    let unsubscribed = false;
    const unsubUser = user.subscribe(u => {
      if (!unsubscribed) {
        callback({
          user: u,
          isAuthenticated: !!u,
          isLoading: state.isLoading,
          error: state.error
        });
      }
    });
    
    return () => {
      unsubscribed = true;
      unsubUser();
    };
  };

  return {
    // Subscribe method for store compatibility
    subscribe,
    
    // Reactive state - using getters to ensure current values
    get user() { return state.user; },
    get isAuthenticated() { return computedIsAuthenticated; },
    get isLoading() { return state.isLoading; },
    get error() { return state.error; },
    
    // Methods required by UseAuthReturn interface
    signIn,
    signOut: signOutMethod,
    signUp,
    signInWithGitHub: signInWithGitHubMethod,
    signInWithSlack: signInWithSlackMethod,
    getUsername,
    getUserAvatar
  };
}