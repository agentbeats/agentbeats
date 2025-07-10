export async function registerAgent(registerInfo: any) {
	try {
		const res = await fetch('http://localhost:9000/agents', {
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

export async function getAgentById(agentId: string) {
  try {
    const res = await fetch(`http://localhost:9000/agents/${agentId}`);
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
    const res = await fetch('http://localhost:9000/agents');
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