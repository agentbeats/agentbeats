export async function createBattle(battleInfo: any) {
	try {
		const res = await fetch('http://localhost:9000/battles', {
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
		
		const result = await res.json();
		return result;
	} catch (error) {
		console.error('Failed to create battle:', error);
		throw error;
	}
} 