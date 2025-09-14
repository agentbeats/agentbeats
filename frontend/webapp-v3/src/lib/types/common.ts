// Common types and interfaces shared across the application

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
}

import type { Battle } from './battles';
import type { Agent } from './agents';

export interface WebSocketMessage {
  type: 'battle_update' | 'battles_update' | 'agent_update' | 'agents_update';
  battle?: Battle;
  battles?: Battle[];
  agent?: Agent;
  agents?: Agent[];
}