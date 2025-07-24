import { createClient } from '@supabase/supabase-js'
import type { SupabaseClient, User, Session, AuthError } from '@supabase/supabase-js'
import { writable } from 'svelte/store'

// Environment variables with proper fallbacks
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables. Please check your .env file.')
}

// Create Supabase client with best practices
export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    // Auto refresh tokens
    autoRefreshToken: true,
    // Persist session in localStorage
    persistSession: true,
    // Detect session in URL (for OAuth callbacks)
    detectSessionInUrl: true,
    // Flow type for OAuth
    flowType: 'pkce'
  }
})

// Auth store with proper typing
export const user = writable<User | null>(null)
export const loading = writable(true)
export const error = writable<AuthError | null>(null)

// Initialize auth state safely
const initializeAuth = async () => {
  try {
    console.log('Initializing auth...')
    loading.set(true)
    error.set(null)
    
    // Add a timeout fallback to prevent infinite loading
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Auth initialization timeout')), 10000); // 10 second timeout
    });
    
    const sessionPromise = supabase.auth.getSession();
    
    const { data: { session }, error: sessionError } = await Promise.race([
      sessionPromise,
      timeoutPromise
    ]) as any;
    
    if (sessionError) {
      console.error('Error getting session:', sessionError)
      error.set(sessionError)
    } else {
      console.log('Session found:', session?.user?.email)
      user.set(session?.user ?? null)
    }
  } catch (err) {
    console.error('Auth initialization error:', err)
    error.set(err as AuthError)
  } finally {
    console.log('Auth initialization complete, setting loading to false')
    loading.set(false)
  }
}

// Listen for auth changes with proper error handling
supabase.auth.onAuthStateChange(async (event, session) => {
  console.log('Auth state changed:', event, session?.user?.email)
  
  try {
    error.set(null)
    
    switch (event) {
      case 'SIGNED_IN':
        console.log('User signed in, setting user and loading to false')
        user.set(session?.user ?? null)
        loading.set(false)
        break
      case 'SIGNED_OUT':
        console.log('User signed out, clearing user and setting loading to false')
        user.set(null)
        loading.set(false)
        // Clear any local storage
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_id')
        }
        break
      case 'TOKEN_REFRESHED':
        console.log('Token refreshed, updating user')
        user.set(session?.user ?? null)
        break
      case 'USER_UPDATED':
        console.log('User updated, updating user')
        user.set(session?.user ?? null)
        break
      case 'INITIAL_SESSION':
        console.log('Initial session, setting user and loading to false')
        user.set(session?.user ?? null)
        loading.set(false)
        break
      default:
        console.log('Unknown auth event:', event, 'ensuring loading is false')
        // For any other events, ensure loading is false
        loading.set(false)
        break
    }
  } catch (err) {
    console.error('Auth state change error:', err)
    error.set(err as AuthError)
    loading.set(false)
  }
})

// Initialize auth on module load
initializeAuth()

// Auth functions with proper error handling
export const signInWithGitHub = async () => {
  try {
    loading.set(true)
    error.set(null)
    
    const { data, error: signInError } = await supabase.auth.signInWithOAuth({
      provider: 'github',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent'
        }
      }
    })
    
    if (signInError) {
      console.error('Error signing in with GitHub:', signInError)
      error.set(signInError)
      throw signInError
    }
    
    return data
  } catch (err) {
    console.error('GitHub sign in error:', err)
    error.set(err as AuthError)
    throw err
  } finally {
    loading.set(false)
  }
}

export const signInWithSlack = async () => {
  try {
    loading.set(true)
    error.set(null)
    
    const { data, error: signInError } = await supabase.auth.signInWithOAuth({
      provider: 'slack',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent'
        }
      }
    })
    
    if (signInError) {
      console.error('Error signing in with Slack:', signInError)
      error.set(signInError)
      throw signInError
    }
    
    return data
  } catch (err) {
    console.error('Slack sign in error:', err)
    error.set(err as AuthError)
    throw err
  } finally {
    loading.set(false)
  }
}

export const signOut = async () => {
  try {
    console.log('Starting sign out...')
    error.set(null)
    
    const { error: signOutError } = await supabase.auth.signOut()
    
    if (signOutError) {
      console.error('Error signing out:', signOutError)
      error.set(signOutError)
      throw signOutError
    }
    
    console.log('Sign out successful')
    
    // Clear local storage safely
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_id')
    }
    
    // Ensure loading is false after logout
    loading.set(false)
    
    // Fallback: Set loading to false after a short delay in case auth state change doesn't fire
    setTimeout(() => {
      console.log('Fallback: Ensuring loading is false after logout')
      loading.set(false)
    }, 1000)
    
  } catch (err) {
    console.error('Sign out error:', err)
    error.set(err as AuthError)
    loading.set(false)
    throw err
  }
}

export const getAccessToken = async (): Promise<string | null> => {
  try {
    const { data: { session }, error: tokenError } = await supabase.auth.getSession()
    
    if (tokenError) {
      console.error('Error getting access token:', tokenError)
      error.set(tokenError)
      return null
    }
    
    return session?.access_token ?? null
  } catch (err) {
    console.error('Get access token error:', err)
    error.set(err as AuthError)
    return null
  }
}

export const refreshSession = async () => {
  try {
    loading.set(true)
    error.set(null)
    
    const { data: { session }, error: refreshError } = await supabase.auth.refreshSession()
    
    if (refreshError) {
      console.error('Error refreshing session:', refreshError)
      error.set(refreshError)
      throw refreshError
    }
    
    user.set(session?.user ?? null)
    return session
  } catch (err) {
    console.error('Refresh session error:', err)
    error.set(err as AuthError)
    throw err
  } finally {
    loading.set(false)
  }
}

export const isAuthenticated = async (): Promise<boolean> => {
  try {
    const { data: { session } } = await supabase.auth.getSession()
    return !!session
  } catch (err) {
    console.error('Authentication check error:', err)
    return false
  }
}

// Utility function to get current user safely
export const getCurrentUser = (): User | null => {
  let currentUser: User | null = null
  user.subscribe(value => {
    currentUser = value
  })()
  return currentUser
} 