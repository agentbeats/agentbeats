import { getAccessToken } from '$lib/auth/supabase';
import type { Battle, ApiResponse, BattleState, BattleOpponent, BattleCreateRequest, BattleUpdateRequest } from '$lib/types';

class BattlesService {
  private baseUrl = '/api/battles';

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
   * Get all battles with optional user filter
   */
  async getAllBattles(userId?: string): Promise<ApiResponse<Battle[]>> {
    try {
      const params = new URLSearchParams();
      if (userId) {
        params.append('user_id', userId);
      }

      const response = await fetch(`${this.baseUrl}?${params}`);
      const result = await this.handleResponse<{ battles?: Battle[] } | Battle[]>(response);
      
      if (result.success && result.data) {
        // Handle both new and legacy response formats
        const battles = Array.isArray(result.data) ? result.data : result.data.battles || [];
        return {
          success: true,
          data: battles
        };
      }
      
      return result as ApiResponse<Battle[]>;
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch battles'
      };
    }
  }

  /**
   * Get battle by ID
   */
  async getBattleById(battleId: string): Promise<ApiResponse<Battle>> {
    try {
      const response = await fetch(`${this.baseUrl}/${battleId}`);
      return this.handleResponse<Battle>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch battle'
      };
    }
  }

  /**
   * Create new battle
   */
  async createBattle(battleInfo: BattleCreateRequest): Promise<ApiResponse<Battle>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(battleInfo)
      });
      
      return this.handleResponse<Battle>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create battle'
      };
    }
  }

  /**
   * Update battle
   */
  async updateBattle(battleId: string, updateData: BattleUpdateRequest): Promise<ApiResponse<Battle>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/${battleId}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(updateData)
      });
      
      return this.handleResponse<Battle>(response);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update battle'
      };
    }
  }

  /**
   * Get battles for specific agent in last 24 hours
   */
  async getAgentBattlesLast24Hours(agentId: string): Promise<ApiResponse<Battle[]>> {
    try {
      const allBattlesResult = await this.getAllBattles();
      
      if (!allBattlesResult.success || !allBattlesResult.data) {
        return allBattlesResult;
      }

      const now = new Date();
      const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      
      const filteredBattles = allBattlesResult.data.filter((battle: Battle) => {
        // Check if agent participated in this battle
        const isGreenAgent = battle.green_agent_id === agentId;
        const isOpponent = battle.red_agent_id === agentId || battle.blue_agent_id === agentId;
        
        if (!isGreenAgent && !isOpponent) return false;
        
        // Check if battle was created in last 24 hours
        const battleDate = new Date(battle.created_at);
        return battleDate >= twentyFourHoursAgo;
      });

      return {
        success: true,
        data: filteredBattles
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch agent battles'
      };
    }
  }

  /**
   * Filter battles by state
   */
  filterBattlesByState(battles: Battle[], states: BattleState[]): Battle[] {
    return battles.filter(battle => states.includes(battle.state));
  }

  /**
   * Get ongoing battles (pending, queued, running)
   */
  getOngoingBattles(battles: Battle[]): Battle[] {
    return this.filterBattlesByState(battles, ['pending', 'queued', 'running']);
  }

  /**
   * Get finished battles (finished, cancelled, error)
   */
  getFinishedBattles(battles: Battle[]): Battle[] {
    return this.filterBattlesByState(battles, ['finished', 'cancelled', 'error']);
  }

  /**
   * Sort battles by date (most recent first)
   */
  sortBattlesByDate(battles: Battle[], ascending: boolean = false): Battle[] {
    return [...battles].sort((a, b) => {
      const aTime = new Date(a.created_at).getTime();
      const bTime = new Date(b.created_at).getTime();
      return ascending ? aTime - bTime : bTime - aTime;
    });
  }
}

export const battlesService = new BattlesService();