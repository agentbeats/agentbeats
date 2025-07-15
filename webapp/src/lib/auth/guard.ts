import { goto } from '$app/navigation';
import { user, loading } from '$lib/stores/auth';
import { supabase } from '$lib/auth/supabase';

export function requireAuth() {
  return new Promise<void>((resolve, reject) => {
    const unsubscribe = loading.subscribe(($loading) => {
      if (!$loading) {
        unsubscribe();
        // Check authentication directly with Supabase
        supabase.auth.getSession().then(({ data: { session } }) => {
          if (!session) {
            console.log('Auth guard: No session found, redirecting to login');
            goto('/login');
            reject(new Error('Not authenticated'));
          } else {
            console.log('Auth guard: Session found, allowing access');
            resolve();
          }
        }).catch((error) => {
          console.error('Auth guard: Error checking session:', error);
          goto('/login');
          reject(error);
        });
      }
    });
  });
}

export function createAuthGuard() {
  let unsubscribe: (() => void) | null = null;
  
  const startGuard = () => {
    // Clean up existing subscription
    if (unsubscribe) {
      unsubscribe();
    }
    
    // Subscribe to auth state changes
    unsubscribe = loading.subscribe(($loading) => {
      if (!$loading) {
        // Check authentication directly with Supabase
        supabase.auth.getSession().then(({ data: { session } }) => {
          if (!session) {
            console.log('Auth guard: User logged out, redirecting to login');
            goto('/login');
          }
        }).catch((error) => {
          console.error('Auth guard: Error checking session:', error);
          goto('/login');
        });
      }
    });
  };
  
  const stopGuard = () => {
    if (unsubscribe) {
      unsubscribe();
      unsubscribe = null;
    }
  };
  
  return { startGuard, stopGuard };
}

// Simple auth guard for use in Svelte components
export function useAuthGuard() {
  let isAuthenticated = false;
  
  // Subscribe to user store
  const unsubscribe = user.subscribe(($user) => {
    isAuthenticated = !!$user;
    if (!isAuthenticated) {
      console.log('useAuthGuard: User not authenticated, redirecting to login');
      goto('/login');
    }
  });
  
  return {
    isAuthenticated,
    unsubscribe
  };
}

export async function getCurrentUser() {
  try {
    const { data: { user: currentUser } } = await supabase.auth.getUser();
    return currentUser;
  } catch (error) {
    console.error('Error getting current user:', error);
    return null;
  }
}

export async function isUserAuthenticated(): Promise<boolean> {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    return !!session;
  } catch (error) {
    console.error('Error checking authentication:', error);
    return false;
  }
} 