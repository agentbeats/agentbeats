// Battle-related types and interfaces

export type BattleState = 'pending' | 'queued' | 'running' | 'finished' | 'cancelled' | 'error';

export interface Battle {
  battle_id: string;
  green_agent_id?: string;
  red_agent_id?: string;
  blue_agent_id?: string;
  state: BattleState;
  scenario?: string;
  result?: {
    winner: 'red' | 'blue' | 'draw';
    reason: string;
  };
  created_at: string;
  updated_at: string;
  started_at?: string;
  finished_at?: string;
}

export interface BattleOpponent {
  name: string;
  agent_id: string;
}

export interface BattleCreateRequest {
  green_agent_id: string;
  opponents: BattleOpponent[];
  config?: Record<string, any>;
  created_by?: string;
}

export interface BattleUpdateRequest {
  state?: BattleState;
  interact_history?: any[];
  result?: any;
  error?: string;
  finished_at?: Date;
}

export interface BattleFilters {
  state?: BattleState[];
  agentId?: string;
  scenario?: string;
  dateRange?: {
    from: Date;
    to: Date;
  };
}

export interface BattlesState {
  battles: Battle[];
  ongoingBattles: Battle[];
  pastBattles: Battle[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  filters: BattleFilters;
  wsConnected: boolean;
}

export interface UseBattlesReturn {
  subscribe: (callback: (value: any) => void) => () => void;
  battles: Battle[];
  ongoingBattles: Battle[];
  pastBattles: Battle[];
  isLoading: boolean;
  error: string | null;
  wsConnected: boolean;
  refresh: () => Promise<void>;
  loadBattles: (userId?: string) => Promise<void>;
  loadMyBattles: (userId: string) => Promise<void>;
  createBattle: (battleInfo: any) => Promise<Battle>;
  startBattle: (battleInfo: any) => Promise<Battle>;
  updateBattle: (battleId: string, updates: any) => Promise<Battle>;
  getBattleById: (battleId: string) => Promise<Battle>;
  getAgentBattlesLast24Hours: (agentId: string) => Promise<Battle[]>;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  filterOngoingBattles: (battles: Battle[]) => Battle[];
  filterFinishedBattles: (battles: Battle[]) => Battle[];
  sortBattlesByDate: (battles: Battle[], ascending?: boolean) => Battle[];
}