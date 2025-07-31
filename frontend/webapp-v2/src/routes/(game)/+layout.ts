import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ parent }) => {
	const { session } = await parent();
	
	// Redirect to login if not authenticated
	if (!session) {
		throw redirect(302, '/login');
	}
	
	return {
		user: session.user
	};
}; 