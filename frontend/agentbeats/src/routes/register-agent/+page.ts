import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	// This is a load function for the page, but we'll handle POST in the component
	// The load function can be used for any initial data loading if needed
	return {};
}; 