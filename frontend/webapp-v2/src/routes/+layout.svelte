<script lang="ts">
	import '../app.css';
	import { onMount, onDestroy } from 'svelte';
	import { goto, onNavigate } from '$app/navigation';
	import { user, loading } from '$lib/stores/auth';
	import { supabase } from '$lib/auth/supabase';
	import { page } from '$app/stores';
	import { fade } from 'svelte/transition';
	
	let { children } = $props();
	let unsubscribe: (() => void) | null = null;

	// Check if we should show navigation (root page, info pages, but not login page or docs pages)
	let showNavigation = $derived($page.url.pathname === '/' || $page.url.pathname.startsWith('/about'));

	// Page transitions
	onNavigate((navigation) => {
		if (!document.startViewTransition) return;
	
		return new Promise((resolve) => {
			document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
		});
	});

	onMount(() => {
		// Check if we're in dev mode
		const isDevMode = import.meta.env.VITE_DEV_LOGIN === "true";
		
		// Subscribe to auth state changes - ONLY for UI state, not navigation
		unsubscribe = user.subscribe(async ($user) => {
			const currentPath = window.location.pathname;
			
			console.log('Layout auth state update:', { user: $user?.email, loading: $loading, currentPath, isDevMode });
			
			// Only handle redirects from login page when user is already authenticated
			// Let server-side guards handle all other authentication redirects
			if (currentPath === '/login' && ($user || isDevMode)) {
				console.log('User authenticated (or dev mode) on login page, redirecting to intended destination');
				try {
					const redirectTo = new URLSearchParams(window.location.search).get('redirect') || '/dashboard';
					await goto(redirectTo);
					console.log('goto completed successfully');
				} catch (error) {
					console.error('goto failed, using window.location:', error);
					const redirectTo = new URLSearchParams(window.location.search).get('redirect') || '/dashboard';
					window.location.href = redirectTo;
				}
			}
		});

		// Only check session for logging purposes, not for navigation
		if (!isDevMode) {
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
		}
	});

	// Cleanup subscription
	onDestroy(() => {
		if (unsubscribe) {
			unsubscribe();
		}
	});
</script>

<div class="min-h-screen bg-background">
	<!-- Sticky Header - Only show on root and info pages -->
	{#if showNavigation}
		<header class="sticky top-0 z-50 bg-background border-b border-border">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex justify-end items-center h-16">
					<!-- Simple Navigation with Line Separators -->
					<nav class="flex items-center">
						<a href="/" class="px-4 py-2 text-sm font-medium text-foreground hover:text-foreground/80 transition-colors duration-200">Home</a>
						<div class="w-px h-4 bg-border mx-2"></div>
						<a href="https://github.com/agentbeats/agentbeats/tree/main/docs" target="_blank" rel="noopener noreferrer" class="px-4 py-2 text-sm font-medium text-foreground hover:text-foreground/80 transition-colors duration-200">Docs</a>
						<div class="w-px h-4 bg-border mx-2"></div>
						<a href="/login" class="px-4 py-2 text-sm font-medium text-foreground hover:text-foreground/80 transition-colors duration-200">Login</a>
					</nav>
				</div>
			</div>
		</header>
	{/if}
	
	<!-- Page Content -->
	<main>
		<div in:fade={{ duration: 200 }} out:fade={{ duration: 150 }}>
			{@render children()}
		</div>
	</main>
</div>
