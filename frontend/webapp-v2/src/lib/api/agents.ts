import { getAccessToken } from '../auth/supabase';

// Types for agent-related data structures
export interface AgentCard {
  name?: string;
  description?: string;
  version?: string;
  protocolVersion?: string;
  capabilities?: Record<string, any>;
  skills?: Array<{ name: string }>;
}

export interface LauncherStatus {
  online: boolean;
  message?: string;
}

export interface AgentRegisterInfo {
  alias: string;
  agent_url: string;
  launcher_url: string;
  is_green: boolean;
  participant_requirements?: Array<{
    role: string;
    name: string;
    required: boolean;
  }>;
  battle_timeout?: number;
}

/**
 * Register a new agent with the backend
 * @param registerInfo - Agent registration information
 * @returns Promise with the created agent data
 */
export async function registerAgent(registerInfo: AgentRegisterInfo) {
  try {
    const res = await fetch('/api/agents', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(registerInfo)
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to register agent');
    }

    return await res.json();
  } catch (error) {
    console.error('Failed to register agent:', error);
    throw error;
  }
}

/**
 * Fetch agent card from a given agent URL via backend proxy
 * @param agentUrl - The URL of the agent to fetch the card from
 * @returns Promise with the agent card data
 */
export async function fetchAgentCard(agentUrl: string): Promise<AgentCard> {
  try {
    const res = await fetch('/api/agents/card', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ agent_url: agentUrl })
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || `Failed to fetch agent card: ${res.status} ${res.statusText}`);
    }

    return await res.json();
  } catch (error) {
    console.error('Failed to fetch agent card:', error);
    throw error;
  }
}

/**
 * Get agent by ID from the backend
 * @param agentId - The unique identifier of the agent
 * @returns Promise with the agent data
 */
export async function getAgentById(agentId: string) {
  try {
    // Get access token from Supabase session
    const accessToken = await getAccessToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const res = await fetch(`/api/agents/${agentId}`, {
      headers
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to fetch agent');
    }
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch agent:', error);
    throw error;
  }
}

/**
 * Get all registered agents from the backend
 * @returns Promise with array of all agents
 */
export async function getAllAgents(checkLiveness: boolean = false) {
  try {
    // Get access token from Supabase session
    const accessToken = await getAccessToken();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const url = checkLiveness ? '/api/agents?check_liveness=true' : '/api/agents';
    const res = await fetch(url, {
      headers
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to fetch agents');
    }
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch agents:', error);
    throw error;
  }
}

/**
 * Analyze agent card to determine if it's a green agent and suggest configuration
 * @param agentCard - The agent card to analyze
 * @returns Promise with analysis results including participant requirements
 */
export async function analyzeAgentCard(agentCard: AgentCard): Promise<{
  is_green: boolean;
  participant_requirements: Array<{ role: string; name: string; required: boolean }>;
  battle_timeout: number;
}> {
  try {
    const res = await fetch('/api/agents/analyze_card', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ agent_card: agentCard })
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || `Failed to analyze agent card: ${res.status} ${res.statusText}`);
    }

    return await res.json();
  } catch (error) {
    console.error('Failed to analyze agent card:', error);
    throw error;
  }
}

/**
 * Check if launcher server is online via backend API
 * @param launcherUrl - The URL of the launcher to check
 * @returns Promise with launcher status information
 */
export async function checkLauncherStatus(launcherUrl: string): Promise<LauncherStatus> {
  try {
    const res = await fetch('/api/agents/check_launcher', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ launcher_url: launcherUrl })
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || `Failed to check launcher status: ${res.status} ${res.statusText}`);
    }

    return await res.json();
  } catch (error) {
    console.error('Failed to check launcher status:', error);
    throw error;
  }
}

/**
 * Get all agents owned by the current user
 * @returns Promise with array of user's agents
 */
export async function getMyAgents() {
  try {
    // Get access token from Supabase session
    const accessToken = await getAccessToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const res = await fetch('/api/agents/my', {
      headers
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to fetch user agents');
    }
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch user agents:', error);
    throw error;
  }
}

/**
 * Delete an agent (only by owner)
 * @param agentId - The unique identifier of the agent to delete
 * @returns Promise that resolves when agent is deleted
 */
export async function deleteAgent(agentId: string) {
  try {
    // Get access token from Supabase session
    const accessToken = await getAccessToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const res = await fetch(`/api/agents/${agentId}`, {
      method: 'DELETE',
      headers
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to delete agent');
    }
    
    return true;
  } catch (error) {
    console.error('Failed to delete agent:', error);
    throw error;
  }
}

/**
 * Update agent status or info
 * @param agentId - The unique identifier of the agent
 * @param update - Object containing fields to update
 * @returns Promise that resolves when agent is updated
 */
export async function updateAgent(agentId: string, update: { ready?: boolean; [key: string]: any }) {
  try {
    const res = await fetch(`/api/agents/${agentId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(update)
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to update agent');
    }
    
    return true;
  } catch (error) {
    console.error('Failed to update agent:', error);
    throw error;
  }
} 