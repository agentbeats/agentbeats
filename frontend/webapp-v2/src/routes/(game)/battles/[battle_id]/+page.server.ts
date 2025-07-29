import type { PageServerLoad } from "./$types";
import { error } from "@sveltejs/kit";

export const load: PageServerLoad = async ({ params, fetch }) => {
  try {
    const battleId = params.battle_id;
    
    if (!battleId) {
      throw error(404, 'Battle ID not found');
    }

    // Fetch battle data from backend
    const response = await fetch(`/api/battles/${battleId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        throw error(404, 'Battle not found');
      }
      throw error(response.status, 'Failed to fetch battle');
    }

    const battle = await response.json();
    
    return {
      battle
    };
  } catch (err) {
    console.error('Error loading battle:', err);
    if (err instanceof Error && err.message.includes('404')) {
      throw error(404, 'Battle not found');
    }
    throw error(500, 'Failed to load battle');
  }
}; 