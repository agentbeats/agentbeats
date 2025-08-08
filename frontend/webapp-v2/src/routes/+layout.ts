import { supabase } from '$lib/auth/supabase';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async () => {
	// Check if we're in dev mode
	const isDevMode = import.meta.env.VITE_DEV_LOGIN === "true";
	
	if (isDevMode) {
		// Return mock session in dev mode
		return {
			session: {
				access_token: 'dev-access-token',
				user: {
					id: 'dev-user-id',
					email: 'dev@agentbeats.org'
				}
			}
		};
	}
	
	// Initialize auth state
	const { data: { session } } = await supabase.auth.getSession();
	
	return {
		session
	};
}; 