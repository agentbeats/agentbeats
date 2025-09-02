import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ parent, url }) => {
	const { session } = await parent();
	
	// Redirect to login if not authenticated, preserving intended destination
	if (!session) {
		throw redirect(302, `/login?redirect=${encodeURIComponent(url.pathname)}`);
	}
	
	return {
		user: session.user
	};
}; 