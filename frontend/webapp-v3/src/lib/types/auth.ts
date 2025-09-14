// Authentication-related types and interfaces

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  user_metadata?: {
    name?: string;
    [key: string]: any;
  };
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface UseAuthReturn {
  subscribe: (callback: (value: any) => void) => () => void;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signInWithGitHub: () => Promise<void>;
  signInWithSlack: () => Promise<void>;
  getUsername: () => string;
  getUserAvatar: () => string | undefined;
}