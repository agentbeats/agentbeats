/**
 * Get all battles from the backend
 * @returns Promise with array of all battles
 */
export async function getAllBattles() {
  try {
    const res = await fetch('/api/battles');
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to fetch battles');
    }
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch battles:', error);
    throw error;
  }
}

/**
 * Get a single battle by ID from the backend
 * @param battleId - The unique identifier of the battle
 * @returns Promise with the battle data
 */
export async function getBattleById(battleId: string) {
  try {
    const res = await fetch(`/api/battles/${battleId}`);
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to fetch battle');
    }
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch battle:', error);
    throw error;
  }
}

/**
 * Create a new battle
 * @param battleInfo Battle information
 * @returns Promise with created battle data
 */
export async function createBattle(battleInfo: any) {
  try {
    const res = await fetch('/api/battles', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(battleInfo)
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to create battle');
    }
    
    return await res.json();
  } catch (error) {
    console.error('Failed to create battle:', error);
    throw error;
  }
} 

/**
 * Get battles for a specific agent in the last 24 hours
 * @param agentId - The agent ID to filter battles for
 * @returns Promise with array of battles for the agent in last 24 hours
 */
export async function getAgentBattlesLast24Hours(agentId: string) {
  try {
    const res = await fetch('/api/battles');
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to fetch battles');
    }
    
    const allBattles = await res.json();
    const now = new Date();
    const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    return allBattles.filter((battle: any) => {
      // Check if agent participated in this battle
      const isGreenAgent = battle.green_agent_id === agentId;
      const isOpponent = battle.opponents?.some((opponent: any) => opponent.agent_id === agentId);
      
      if (!isGreenAgent && !isOpponent) return false;
      
      // Check if battle was created in last 24 hours
      const battleDate = new Date(battle.created_at);
      return battleDate >= twentyFourHoursAgo;
    });
  } catch (error) {
    console.error('Failed to fetch agent battles:', error);
    throw error;
  }
} 