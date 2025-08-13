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

export interface RoleMatchResult {
  matched_roles: string[];
  reasons: Record<string, string>;
  confidence_score: number;
  error?: string;
}

/**
 * Register a new agent with the backend
 * @param registerInfo - Agent registration information
 * @returns Promise with the created agent data
 */
export async function registerAgent(registerInfo: AgentRegisterInfo) {
  console.log('🔵 [ROLE MATCHING] Starting agent registration:', {
    alias: registerInfo.alias,
    is_green: registerInfo.is_green,
    agent_url: registerInfo.agent_url,
    launcher_url: registerInfo.launcher_url,
    participant_requirements: registerInfo.participant_requirements
  });

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
      console.error('🔴 [ROLE MATCHING] Agent registration failed:', errorData);
      throw new Error(errorData.detail || 'Failed to register agent');
    }

    const result = await res.json();
    console.log('✅ [ROLE MATCHING] Agent registered successfully:', {
      agent_id: result.agent_id,
      alias: result.register_info.alias,
      is_green: result.register_info.is_green
    });

    // Log that role matching will be triggered automatically
    if (result.register_info.is_green) {
      console.log('🟢 [ROLE MATCHING] Green agent registered - will analyze against all non-green agents');
    } else {
      console.log('🔴 [ROLE MATCHING] Non-green agent registered - will analyze against all green agents');
    }

    return result;
  } catch (error) {
    console.error('🔴 [ROLE MATCHING] Failed to register agent:', error);
    throw error;
  }
}

/**
 * Analyze role matches for a specific agent
 * @param agentId - The agent ID to analyze
 * @returns Promise with analysis results
 */
export async function analyzeAgentMatches(agentId: string): Promise<{
  agent_id: string;
  matches_created: number;
  analysis_details: Array<{
    other_agent_id: string;
    other_agent_alias: string;
    matched_roles: string[];
    confidence_score: number;
    reasons: Record<string, string>;
  }>;
}> {
  console.log('🔍 [ROLE MATCHING] Starting role match analysis for agent:', agentId);

  try {
    const accessToken = await getAccessToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const res = await fetch(`/api/matches/analyze/${agentId}`, {
      method: 'POST',
      headers
    });

    if (!res.ok) {
      const errorData = await res.json();
      console.error('🔴 [ROLE MATCHING] Role analysis failed:', errorData);
      throw new Error(errorData.detail || 'Failed to analyze agent matches');
    }

    const result = await res.json();
    console.log('✅ [ROLE MATCHING] Role analysis completed:', {
      agent_id: agentId,
      matches_created: result.matches_created,
      total_agents_analyzed: result.analysis_details?.length || 0
    });

    // Log detailed analysis results
    if (result.analysis_details) {
      result.analysis_details.forEach((detail: any, index: number) => {
        console.log(`📊 [ROLE MATCHING] Analysis ${index + 1}:`, {
          other_agent_id: detail.other_agent_id,
          other_agent_alias: detail.other_agent_alias,
          matched_roles: detail.matched_roles,
          confidence_score: detail.confidence_score,
          reasons: detail.reasons
        });
      });
    }

    return result;
  } catch (error) {
    console.error('🔴 [ROLE MATCHING] Failed to analyze agent matches:', error);
    throw error;
  }
}

/**
 * Get role matches for a specific agent
 * @param agentId - The agent ID to get matches for
 * @returns Promise with match data
 */
export async function getAgentMatches(agentId: string): Promise<{
  as_green: Array<{
    id: string;
    other_agent_id: string;
    confidence_score: number;
    matched_roles: string[];
    reasons: Record<string, string>;
  }>;
  as_other: Array<{
    id: string;
    green_agent_id: string;
    confidence_score: number;
    matched_roles: string[];
    reasons: Record<string, string>;
  }>;
}> {
  console.log('🔍 [ROLE MATCHING] Fetching role matches for agent:', agentId);

  try {
    const accessToken = await getAccessToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const res = await fetch(`/api/matches/agent/${agentId}`, {
      headers
    });

    if (!res.ok) {
      const errorData = await res.json();
      console.error('🔴 [ROLE MATCHING] Failed to fetch agent matches:', errorData);
      throw new Error(errorData.detail || 'Failed to fetch agent matches');
    }

    const result = await res.json();
    console.log('✅ [ROLE MATCHING] Retrieved agent matches:', {
      agent_id: agentId,
      as_green_count: result.as_green?.length || 0,
      as_other_count: result.as_other?.length || 0
    });

    // Log detailed match information
    if (result.as_green && result.as_green.length > 0) {
      console.log('🟢 [ROLE MATCHING] Matches as green agent:');
      result.as_green.forEach((match: any, index: number) => {
        console.log(`  ${index + 1}. vs ${match.other_agent_id}:`, {
          matched_roles: match.matched_roles,
          confidence_score: match.confidence_score,
          reasons: match.reasons
        });
      });
    }

    if (result.as_other && result.as_other.length > 0) {
      console.log('🔴 [ROLE MATCHING] Matches as other agent:');
      result.as_other.forEach((match: any, index: number) => {
        console.log(`  ${index + 1}. vs ${match.green_agent_id}:`, {
          matched_roles: match.matched_roles,
          confidence_score: match.confidence_score,
          reasons: match.reasons
        });
      });
    }

    return result;
  } catch (error) {
    console.error('🔴 [ROLE MATCHING] Failed to fetch agent matches:', error);
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
  console.log('🔍 [ROLE MATCHING] Fetching all agents from backend...');
  
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
      console.error('🔴 [ROLE MATCHING] Failed to fetch agents:', errorData);
      throw new Error(errorData.detail || 'Failed to fetch agents');
    }
    
    const agents = await res.json();
    console.log('✅ [ROLE MATCHING] Retrieved agents:', {
      total_count: agents.length,
      green_agents: agents.filter((a: any) => a.register_info?.is_green).length,
      non_green_agents: agents.filter((a: any) => !a.register_info?.is_green).length
    });

    // Log agent details for role matching analysis
    agents.forEach((agent: any, index: number) => {
      console.log(`📋 [ROLE MATCHING] Agent ${index + 1}:`, {
        agent_id: agent.agent_id,
        alias: agent.register_info?.alias,
        is_green: agent.register_info?.is_green,
        participant_requirements: agent.register_info?.participant_requirements?.map((req: any) => req.name) || [],
        agent_url: agent.register_info?.agent_url,
        launcher_url: agent.register_info?.launcher_url
      });
    });

    return agents;
  } catch (error) {
    console.error('🔴 [ROLE MATCHING] Failed to fetch agents:', error);
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
 * @param checkLiveness - Whether to check if agents are online
 * @returns Promise with array of user's agents
 */
export async function getMyAgents(checkLiveness: boolean = false) {
  try {
    // Get access token from Supabase session
    const accessToken = await getAccessToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const url = checkLiveness ? '/api/agents/my?check_liveness=true' : '/api/agents/my';
    const res = await fetch(url, {
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
 * Get agents with layered loading - returns basic info immediately, then updates with liveness
 * @param updateCallback - Callback function to handle liveness updates
 * @returns Promise with initial agent data
 */
export async function getMyAgentsWithAsyncLiveness(
  updateCallback: (agents: any[]) => void
): Promise<any[]> {
  try {
    // 1. First, get basic info quickly and mark as loading liveness
    const basicAgents = await getMyAgents(false);
    
    // Add loading state to each agent
    const agentsWithLoading = basicAgents.map(agent => ({
      ...agent,
      livenessLoading: true
    }));
    
    // 2. Start async liveness check in background
    setTimeout(async () => {
      try {
        const liveAgents = await getMyAgents(true);
        // Remove loading state from updated agents
        const updatedAgents = liveAgents.map(agent => ({
          ...agent,
          livenessLoading: false
        }));
        updateCallback(updatedAgents);
      } catch (error) {
        console.error('Failed to update agent liveness:', error);
        // On error, still remove loading state
        const errorAgents = basicAgents.map(agent => ({
          ...agent,
          livenessLoading: false,
          live: false // Default to offline on error
        }));
        updateCallback(errorAgents);
      }
    }, 0);
    
    return agentsWithLoading;
  } catch (error) {
    console.error('Failed to fetch agents with async liveness:', error);
    throw error;
  }
}

/**
 * Get all agents with layered loading - returns basic info immediately, then updates with liveness
 * @param updateCallback - Callback function to handle liveness updates
 * @returns Promise with initial agent data
 */
export async function getAllAgentsWithAsyncLiveness(
  updateCallback: (agents: any[]) => void
): Promise<any[]> {
  try {
    // 1. First, get basic info quickly and mark as loading liveness
    const basicAgents = await getAllAgents(false);
    
    // Add loading state to each agent
    const agentsWithLoading = basicAgents.map(agent => ({
      ...agent,
      livenessLoading: true
    }));
    
    // 2. Start async liveness check in background
    setTimeout(async () => {
      try {
        const liveAgents = await getAllAgents(true);
        // Remove loading state from updated agents
        const updatedAgents = liveAgents.map(agent => ({
          ...agent,
          livenessLoading: false
        }));
        updateCallback(updatedAgents);
      } catch (error) {
        console.error('Failed to update agent liveness:', error);
        // On error, still remove loading state
        const errorAgents = basicAgents.map(agent => ({
          ...agent,
          livenessLoading: false,
          live: false // Default to offline on error
        }));
        updateCallback(errorAgents);
      }
    }, 0);
    
    return agentsWithLoading;
  } catch (error) {
    console.error('Failed to fetch agents with async liveness:', error);
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

/**
 * Get matches for a specific green agent and role
 * @param greenAgentId - The green agent ID
 * @param roleName - The role name to get matches for
 * @returns Promise with sorted matches for that role
 */
export async function getMatchesForGreenAgentRole(greenAgentId: string, roleName: string): Promise<Array<{
  id: string;
  other_agent_id: string;
  confidence_score: number;
  matched_roles: string[];
  reasons: Record<string, string>;
  other_agent: {
    agent_id: string;
    alias: string;
    name: string;
    description: string;
  };
}>> {
  try {
    const accessToken = await getAccessToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const res = await fetch(`/api/matches/green-agent/${greenAgentId}`, {
      headers
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to fetch green agent matches');
    }

    const matches = await res.json();
    
    // Filter matches for the specific role and sort by confidence
    const roleMatches = matches
      .filter((match: any) => match.matched_roles.includes(roleName))
      .sort((a: any, b: any) => b.confidence_score - a.confidence_score);

    return roleMatches;
  } catch (error) {
    console.error('Failed to fetch green agent role matches:', error);
    throw error;
  }
} 