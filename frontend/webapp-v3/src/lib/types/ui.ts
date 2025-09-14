// UI-related types and interfaces

export interface CartItem {
  agent: any;
  type: 'green' | 'opponent';
}

export interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'auto';
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  timestamp: Date;
}

export interface LoadingStateProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  centered?: boolean;
}

export interface ErrorStateProps {
  error: string | Error;
  onRetry?: () => void;
  showRetry?: boolean;
}

export interface EmptyStateProps {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: any;
}