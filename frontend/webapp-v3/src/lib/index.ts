// Main library exports
export * from './hooks';
export * from './types';
export * from './utils';

// Re-export stores for direct access if needed
export { agentsStore, greenAgents, opponentAgents, topAgents } from './stores/agents.store';
export { battlesStore, ongoingBattles, pastBattles } from './stores/battles.store';

// Re-export services for direct access if needed
export { agentsService } from './services/agents.service';
export { battlesService } from './services/battles.service';