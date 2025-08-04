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
		
		const result = await res.json();
		return result;
	} catch (error) {
		console.error('Failed to create battle:', error);
		throw error;
	}
}

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