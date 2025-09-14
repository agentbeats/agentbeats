// Centralized hooks export
// This provides a clean API for importing hooks throughout the application

export { useAgents } from './useAgents';
export { useBattles } from './useBattles';
export { useAuth } from './useAuth';

// Re-export types for convenience
export type {
  UseAgentsReturn,
  UseBattlesReturn,
  UseAuthReturn
} from '$lib/types';