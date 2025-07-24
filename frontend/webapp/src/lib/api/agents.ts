export async function registerAgent(registerInfo: any) {
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

    const result = await res.json();
    return result;
  } catch (error) {
    console.error('Failed to register agent:', error);
    throw error;
  }
}

export async function fetchAgentCard(agentUrl: string) {
  try {
    const res = await fetch('/api/agents/card', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ agent_url: agentUrl })
    });

    if (!res.ok) {
      let errorMessage = `Failed to fetch agent card: ${res.status} ${res.statusText}`;
      
      try {
        const errorData = await res.json();
        errorMessage = errorData.detail || errorMessage;
      } catch (parseError) {
        try {
          const errorText = await res.text();
          if (errorText.includes('<!doctype') || errorText.includes('<html')) {
            errorMessage = 'Server returned HTML instead of JSON. The agent URL may be incorrect or the agent service is not running properly.';
          } else {
            errorMessage = `Server error: ${errorText.substring(0, 200)}`;
          }
        } catch {
        }
      }
      throw new Error(errorMessage); 
    }
    const agentCard = await res.json();
    return agentCard;
  } catch (error) {
    console.error('Failed to fetch agent card:', error);
    
    if (error instanceof Error) {
      if (error.message.includes('not valid JSON') || error.message.includes('<!doctype')) {
        throw new Error('The agent URL returned HTML instead of a valid agent card. Please check:\n1. Agent service is running\n2. URL points to correct agent card endpoint\n3. Agent service returns JSON format');
      }
    }
    
    throw error;
  }
}

export async function getAgentById(agentId: string) {
  try {
    const res = await fetch(`/api/agents/${agentId}`);
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

export async function getAllAgents() {
  try {
    const res = await fetch('/api/agents');
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

export async function analyzeAgentCard(agentCard: any) {
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

    const analysis = await res.json();
    return analysis;
  } catch (error) {
    console.error('Failed to analyze agent card:', error);
    throw error;
  }
}

export async function checkLauncherStatus(launcherUrl: string) {
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

    const result = await res.json();
    return result;
  } catch (error) {
    console.error('Failed to check launcher status:', error);
    throw error;
  }
}