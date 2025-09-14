import { getAccessToken } from '$lib/auth/supabase';
import type { 
  Agent, 
  ApiResponse, 
  AgentCard, 
  LauncherStatus, 
  AgentCardAnalysis, 
  AgentCardUpdateResponse,
  AgentRegisterInfo,
  AgentInstance,
  AgentInstanceUpdateRequest,
  AgentInstanceUpdateResponse,
  AgentInstanceDeleteResponse,
  AgentInstanceListResponse,
  AgentInstanceLogResponse,
  LogType
} from '$lib/types';

class AgentsService {
  private baseUrl = '/api/agents';

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const accessToken = await getAccessToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }
    
    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      return {
        success: false,
        error: errorData.detail || `HTTP ${response.status}: ${response.statusText}`
      };
    }

    try {
      const data = await response.json();
      return {
        success: true,
        data
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to parse response'
      };
    }
  }

  /**
   * Get all agents with optional filters
   */
  async getAllAgents(options: {
    scope?: 'all' | 'mine';
    checkLiveness?: boolean;
    isGreen?: boolean;
  } = {}): Promise<ApiResponse<Agent[]>> {
    try {
      const { scope = 'all', checkLiveness = false, isGreen } = options;
      const headers = await this.getAuthHeaders();
      
      const params = new URLSearchParams({ scope });
      if (checkLiveness) params.set('check_liveness', 'true');
      if (isGreen !== undefined) params.set('is_green', String(isGreen));

      const response = await fetch(`${this.baseUrl}?${params}`, { headers });
      const result = await this.handleResponse<{ agents: Agent[] }>(response);
      
      if (result.success && result.data) {
        return {
          success: true,
          data: result.data.agents
        };
      }
      
      return {
        success: false,
        error: result.error || 'Failed to fetch agents'
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch agents'
      };
    }
  }

  /**
   * Get user's agents only
   */
  async getMyAgents(checkLiveness: boolean = false): Promise<ApiResponse<Agent[]>> {
    return this.getAllAgents({ scope: 'mine', checkLiveness });
  }

  /**
   * Get agents with layered loading - returns basic info immediately, then updates with liveness
   */
  async getAgentsWithAsyncLiveness(
    options: { scope?: 'all' | 'mine' } = {},
    updateCallback: (agents: Agent[]) => void
  ): Promise<ApiResponse<Agent[]>> {
    const { scope = 'all' } = options;
    
    try {
      // 1. Get basic info first
      const basicResult = await this.getAllAgents({ scope, checkLiveness: false });
      
      if (!basicResult.success || !basicResult.data) {
        return basicResult;
      }

      // Add loading state
      const agentsWithLoading = basicResult.data.map(agent => ({
        ...agent,
        livenessLoading: true
      }));

      // 2. Start async liveness check
      setTimeout(async () => {
        const liveResult = await this.getAllAgents({ scope, checkLiveness: true });
        
        if (liveResult.success && liveResult.data) {
          const updatedAgents = liveResult.data.map(agent => ({
            ...agent,
            livenessLoading: false
          }));
          updateCallback(updatedAgents);
        } else {
          // On error, remove loading state
          const errorAgents = agentsWithLoading.map(agent => ({
            ...agent,
            livenessLoading: false,
            live: false
          }));
          updateCallback(errorAgents);
        }
      }, 0);   

      return {
        success: true,
        data: agentsWithLoading
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch agents with async liveness'
      };
    }
  }

  /**
   * Get agent by ID
   */
  async getAgentById(agentId: string): Promise<ApiResponse<Agent>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/${agentId}`, { headers });
      return this.handleResponse<Agent>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch agent'
      };
    }
  }

  /**
   * Register new agent
   */
  async registerAgent(registerInfo: AgentRegisterInfo): Promise<ApiResponse<Agent>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(registerInfo)
      });
      
      return this.handleResponse<Agent>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to register agent'
      };
    }
  }

  /**
   * Delete agent
   */
  async deleteAgent(agentId: string): Promise<ApiResponse<boolean>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/${agentId}`, {
        method: 'DELETE',
        headers
      });
      
      if (response.ok) {
        return { success: true, data: true };
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        return {
          success: false,
          error: errorData.detail || 'Failed to delete agent'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete agent'
      };
    }
  }

  /**
   * Update agent
   */
  async updateAgent(agentId: string, update: { ready?: boolean; [key: string]: any }): Promise<ApiResponse<Agent>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/${agentId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(update)
      });
      
      return this.handleResponse<Agent>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update agent'
      };
    }
  }

  /**
   * Fetch agent card from agent URL
   */
  async fetchAgentCard(agentUrl: string): Promise<ApiResponse<AgentCard>> {
    try {
      const params = new URLSearchParams({ agent_url: agentUrl });
      const response = await fetch(`/api/services/agent_card?${params.toString()}`);
      return this.handleResponse<AgentCard>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch agent card'
      };
    }
  }

  /**
   * Check launcher status
   */
  async checkLauncherStatus(launcherUrl: string): Promise<ApiResponse<LauncherStatus>> {
    try {
      const params = new URLSearchParams({ launcher_url: launcherUrl });
      const response = await fetch(`/api/services/launcher_status?${params.toString()}`);
      return this.handleResponse<LauncherStatus>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to check launcher status'
      };
    }
  }


  /**
   * Analyze agent card
   */
  async analyzeAgentCard(agentCard: AgentCard): Promise<ApiResponse<AgentCardAnalysis>> {
    try {
      const response = await fetch('/api/services/agent_card_analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(agentCard)
      });
      return this.handleResponse<AgentCardAnalysis>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to analyze agent card'
      };
    }
  }


  /**
   * Update agent card
   */
  async updateAgentCard(agentId: string): Promise<ApiResponse<AgentCardUpdateResponse>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`api/services/agent_card/${agentId}`, {
        method: 'PUT',
        headers
      });
      return this.handleResponse<AgentCardUpdateResponse>(response);
    }
    catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update agent card'
      };
    } 
  }


  // ===== AGENT INSTANCES API METHODS =====

  /**
   * List all agent instances with optional filters
   */
  async getAllAgentInstances(options: {
    isLocked?: boolean;
    ready?: boolean;
  } = {}): Promise<ApiResponse<AgentInstanceListResponse>> {
    try {
      const { isLocked, ready } = options;
      const headers = await this.getAuthHeaders();
      
      const params = new URLSearchParams();
      if (isLocked !== undefined) params.set('is_locked', String(isLocked));
      if (ready !== undefined) params.set('ready', String(ready));

      const url = `/api/agent_instances${params.toString() ? `?${params}` : ''}`;
      const response = await fetch(url, { headers });
      return this.handleResponse<AgentInstanceListResponse>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch agent instances'
      };
    }
  }

  /**
   * Get agent instance by ID
   */
  async getAgentInstanceById(agentInstanceId: string): Promise<ApiResponse<AgentInstance>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`/api/agent_instances/${agentInstanceId}`, { headers });
      return this.handleResponse<AgentInstance>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch agent instance'
      };
    }
  }

  // /**
  //  * Update agent instance ready status
  //  */
  // async updateAgentInstance(
  //   agentInstanceId: string, 
  //   updateData: AgentInstanceUpdateRequest
  // ): Promise<ApiResponse<AgentInstanceUpdateResponse>> {
  //   try {
  //     const headers = await this.getAuthHeaders();
  //     const response = await fetch(`/api/agent_instances/${agentInstanceId}`, {
  //       method: 'PUT',
  //       headers,
  //       body: JSON.stringify(updateData)
  //     });
      
  //     return this.handleResponse<AgentInstanceUpdateResponse>(response);
  //   } catch (error) {
  //     return {
  //       success: false,
  //       error: error instanceof Error ? error.message : 'Failed to update agent instance'
  //     };
  //   }
  // }

  // /**
  //  * Delete hosted agent instance
  //  */
  // async deleteHostedAgentInstance(agentInstanceId: string): Promise<ApiResponse<AgentInstanceDeleteResponse>> {
  //   try {
  //     const headers = await this.getAuthHeaders();
  //     const response = await fetch(`/api/agent_instances/hosted/${agentInstanceId}`, {
  //       method: 'DELETE',
  //       headers
  //     });
      
  //     return this.handleResponse<AgentInstanceDeleteResponse>(response);
  //   } catch (error) {
  //     return {
  //       success: false,
  //       error: error instanceof Error ? error.message : 'Failed to delete hosted agent instance'
  //     };
  //   }
  // }

  /**
   * Get logs for a hosted agent instance
   */
  async getAgentInstanceLogs(
    agentInstanceId: string,
    logType: LogType,
    lines: number = 100
  ): Promise<ApiResponse<AgentInstanceLogResponse>> {
    try {
      const headers = await this.getAuthHeaders();
      const params = new URLSearchParams({ lines: String(lines) });
      const url = `/api/agent_instances/hosted/${agentInstanceId}/logs/${logType}?${params}`;
      
      const response = await fetch(url, { headers });
      return this.handleResponse<AgentInstanceLogResponse>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : `Failed to fetch ${logType} logs`
      };
    }
  }

  /**
   * Get deployment logs for a hosted agent instance
   */
  async getAgentInstanceDeploymentLogs(agentInstanceId: string): Promise<ApiResponse<AgentInstanceLogResponse>> {
    return this.getAgentInstanceLogs(agentInstanceId, 'deployment');
  }

  /**
   * Get stop logs for a hosted agent instance
   */
  async getAgentInstanceStopLogs(agentInstanceId: string): Promise<ApiResponse<AgentInstanceLogResponse>> {
    return this.getAgentInstanceLogs(agentInstanceId, 'stop');
  }

  /**
   * Get live output logs for a hosted agent instance
   */
  async getAgentInstanceLiveOutputLogs(
    agentInstanceId: string, 
    lines: number = 100
  ): Promise<ApiResponse<AgentInstanceLogResponse>> {
    return this.getAgentInstanceLogs(agentInstanceId, 'live_output', lines);
  }

  /**
   * Get all agent instances for a specific agent
   */
  async getAgentInstancesByAgentId(agentId: string): Promise<ApiResponse<AgentInstanceListResponse>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/${agentId}/instances`, { headers });
      return this.handleResponse<AgentInstanceListResponse>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch agent instances'
      };
    }
  }
}

export const agentsService = new AgentsService();
