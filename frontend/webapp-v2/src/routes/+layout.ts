import { supabase } from '$lib/auth/supabase';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async () => {
	// Initialize auth state
	const { data: { session } } = await supabase.auth.getSession();
	
	return {
		session
	};
}; 