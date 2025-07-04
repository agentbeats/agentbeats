export async function registerAgent(registerInfo: any) {
	try {
		const res = await fetch('http://localhost:3001/agents', {
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