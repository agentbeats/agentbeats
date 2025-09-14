// Agent-related types and interfaces

export enum AgentCardStatus {
  LOADING = "loading",
  READY = "ready",
  ERROR = "error",
}

export interface AgentCard {
  name?: string;
  description?: string;
  version?: string;
  protocolVersion?: string;
  capabilities?: Record<string, any>;
  skills?: Array<{ name: string }>;
}

export interface Agent {
  agent_id: string;
  user_id: string;
  alias: string;
  is_hosted: boolean;
  is_green: boolean;
  avatar_url?: string;
  live?: boolean;
  livenessLoading?: boolean;
  agent_card_status: AgentCardStatus;
  agent_card?: AgentCard;
  elo?: {
    rating: number;
    stats?: {
      win_rate: number;
      games_played: number;
    };
  };
  created_at: string;
  batttle_description?: string;
  participant_requirements?: Array<{
    role: string;
    name: string;
    required: boolean;
  }>;
  battle_timeout?: number;

}

export interface LauncherStatus {
  online: boolean;
  message?: string;
}

export interface AgentCardAnalysis {
  is_green: boolean;
  battle_timeout?: number;
  participant_requirements?: Array<{
    role: string;
    name: string;
    required: boolean;
  }>;
}

export interface AgentCardUpdateResponse {
  //TODO
  message: string;
}

export interface AgentRegisterInfo {
  alias: string;
  agent_url?: string;
  launcher_url?: string;
  is_green: boolean;
  is_hosted: boolean;
  battle_description?: string;
  docker_image_link?: string;
  participant_requirements?: Array<{
    role: string;
    name: string;
    required: boolean;
  }>;
  battle_timeout?: number;
}

export interface AgentFilters {
  isGreen?: boolean;
  isLive?: boolean;
  search?: string;
}

export interface AgentsState {
  agents: Agent[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  filters: AgentFilters;
}

export interface UseAgentsReturn {
  subscribe: (callback: (value: any) => void) => () => void;
  agents: Agent[];
  greenAgents: Agent[];
  opponentAgents: Agent[];
  topAgents: Agent[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  loadMyAgents: () => Promise<void>;
  loadMyAgentsWithLiveness: (
    updateCallback?: (agents: Agent[]) => void
  ) => Promise<void>;
  loadAllAgents: () => Promise<void>;
  loadAllAgentsWithLiveness: (
    updateCallback?: (agents: Agent[]) => void
  ) => Promise<void>;
  deleteAgent: (agentId: string) => Promise<void>;
  registerAgent: (registerInfo: any) => Promise<Agent>;
  updateAgent: (agentId: string, updates: Partial<Agent>) => Promise<void>;
  getAgentById: (agentId: string) => Promise<Agent | null>;
}

// Agent Instance related types
export enum AgentInstanceDockerStatus {
  STARTING = "starting",
  RUNNING = "running",
  STOPPING = "stopping",
  STOPPED = "stopped",
}

export interface AgentInstance {
  agent_instance_id: string;
  agent_id: string;
  agent_url: string;
  launcher_url: string;
  is_locked: boolean;
  ready: boolean;
  docker_status: AgentInstanceDockerStatus;
  created_at: string;
}

export interface AgentInstanceUpdateRequest {
  ready: boolean;
}

export interface AgentInstanceUpdateResponse {
  agent_instance_id: string;
  message: string;
}

export interface AgentInstanceDeleteResponse {
  agent_instance_id: string;
  message: string;
  is_hosted: boolean;
  docker_stopping: boolean;
}

export interface AgentInstanceListResponse {
  instances: AgentInstance[];
}

export interface AgentInstanceLogResponse {
  agent_instance_id: string;
  log_type: string;
  log_content: string;
  is_hosted: boolean;
  log_exists?: boolean;
  container_name?: string;
  container_exists?: boolean;
}

export type LogType = "deployment" | "stop" | "live_output";
