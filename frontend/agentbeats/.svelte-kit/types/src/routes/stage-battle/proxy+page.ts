// @ts-nocheck
import type { PageLoad } from './$types';

export const load = async ({ fetch }: Parameters<PageLoad>[0]) => {
	// This is a load function for the page, but we'll handle POST in the component
	// The load function can be used for any initial data loading if needed
	return {};
}; 