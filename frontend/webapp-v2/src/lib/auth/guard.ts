import { goto } from '$app/navigation';
import { user, loading } from '$lib/stores/auth';
import { supabase } from '$lib/auth/supabase';

const isDevMode = import.meta.env.VITE_DEV_LOGIN === "true";

export function requireAuth() {
  return new Promise<void>((resolve, reject) => {
    // In dev mode, always allow access
    if (isDevMode) {
      console.log('Auth guard: Dev mode enabled, allowing access');
      resolve();
      return;
    }
    
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
    // In dev mode, do nothing
    if (isDevMode) {
      console.log('Auth guard: Dev mode enabled, skipping guard');
      return;
    }
    
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
  let isAuthenticated = isDevMode; // Always authenticated in dev mode
  
  // In dev mode, skip user subscription
  if (isDevMode) {
    return {
      isAuthenticated: true,
      unsubscribe: () => {}
    };
  }
  
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
  // In dev mode, return mock user
  if (isDevMode) {
    return {
      id: 'dev-user-id',
      email: 'dev@agentbeats.org',
      user_metadata: { name: 'Dev User' }
    };
  }
  
  try {
    const { data: { user: currentUser } } = await supabase.auth.getUser();
    return currentUser;
  } catch (error) {
    console.error('Error getting current user:', error);
    return null;
  }
}

export async function isUserAuthenticated(): Promise<boolean> {
  // In dev mode, always return true
  if (isDevMode) {
    return true;
  }
  
  try {
    const { data: { session } } = await supabase.auth.getSession();
    return !!session;
  } catch (error) {
    console.error('Error checking authentication:', error);
    return false;
  }
} 