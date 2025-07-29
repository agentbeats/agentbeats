<script lang="ts">
	import '../app.css';
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { user, loading } from '$lib/stores/auth';
	import { supabase } from '$lib/auth/supabase';
	
	let { children } = $props();
	let unsubscribe: (() => void) | null = null;

	onMount(() => {
		// Subscribe to auth state changes
		unsubscribe = user.subscribe(($user) => {
			// Check if we're on a public page that doesn't require auth
			const publicPages = ['/', '/login', '/auth/callback', '/about', '/docs'];
			const currentPath = window.location.pathname;
			
			if (!publicPages.includes(currentPath)) {
				// If user is not authenticated and not on a public page, redirect to login
				if (!$user && !$loading) {
					console.log('User not authenticated, redirecting to login');
					goto('/login');
				}
			}
		});

		// Check for existing session on mount
		const checkSession = async () => {
			try {
				const { data: { session } } = await supabase.auth.getSession();
				if (session) {
					console.log('Session found on mount:', session.user.email);
				}
			} catch (err) {
				console.error('Error checking session on mount:', err);
			}
		};
		
		checkSession();
	});

	// Cleanup subscription
	onDestroy(() => {
		if (unsubscribe) {
			unsubscribe();
		}
	});
</script>

{@render children()}
