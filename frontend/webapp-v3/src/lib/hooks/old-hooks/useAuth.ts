import { derived } from 'svelte/store';
import { user, loading, error, signInWithGitHub, signInWithSlack, signOut, getCurrentUser } from '$lib/auth/supabase';
import type { User, UseAuthReturn } from '$lib/types';

/**
 * Hook for managing authentication state and operations
 * Provides centralized access to auth state and actions
 * Consistent with other hooks design pattern
 */
export function useAuth(): UseAuthReturn {
  // Derived store that combines all auth data
  const authData = derived(
    [user, loading, error],
    ([$user, $loading, $error]) => ({
      user: $user,
      isLoading: $loading,
      error: $error?.message || null,
      isAuthenticated: !!$user
    })
  );

  // Actions
  const signIn = async (email: string, password: string): Promise<void> => {
    // This would need to be implemented if email/password auth is needed
    throw new Error('Email/password sign in not implemented. Use OAuth instead.');
  };

  const signInWithGitHubProvider = async (): Promise<void> => {
    await signInWithGitHub();
  };

  const signInWithSlackProvider = async (): Promise<void> => {
    await signInWithSlack();
  };

  const signOutUser = async (): Promise<void> => {
    await signOut();
  };

  const signUp = async (email: string, password: string): Promise<void> => {
    // This would need to be implemented if email/password auth is needed
    throw new Error('Email/password sign up not implemented. Use OAuth instead.');
  };

  const getUsername = (): string => {
    const currentUser = getCurrentUser();
    if (!currentUser) return 'User';
    
    return currentUser.user_metadata?.name || 
           currentUser.email?.split('@')[0] || 
           'User';
  };

  const getUserAvatar = (): string | undefined => {
    const currentUser = getCurrentUser();
    return currentUser?.user_metadata?.avatar_url;
  };

  // Return the hook interface - same pattern as useAgents and useBattles
  return {
    // Reactive data - use derived store for automatic reactivity
    subscribe: authData.subscribe,
    
    // Computed getters that work with current state - same pattern as other hooks
    get user() {
      let current: any;
      authData.subscribe(value => current = value)();
      return current?.user || null;
    },
    
    get isAuthenticated() {
      let current: any;
      authData.subscribe(value => current = value)();
      return current?.isAuthenticated || false;
    },
    
    get isLoading() {
      let current: any;
      authData.subscribe(value => current = value)();
      return current?.isLoading || false;
    },
    
    get error() {
      let current: any;
      authData.subscribe(value => current = value)();
      return current?.error || null;
    },

    // Actions
    signIn,
    signOut: signOutUser,
    signUp,
    signInWithGitHub: signInWithGitHubProvider,
    signInWithSlack: signInWithSlackProvider,
    
    // Helper methods
    getUsername,
    getUserAvatar
  };
}