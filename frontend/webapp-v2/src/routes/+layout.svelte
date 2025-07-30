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
		// Subscribe to auth state changes
		unsubscribe = user.subscribe(async ($user) => {
			// Check if we're on a public page that doesn't require auth
			const publicPages = ['/', '/login', '/auth/callback', '/about'];
			const currentPath = window.location.pathname;
			const isDocsPage = currentPath.startsWith('/docs');
			
			console.log('Layout auth check:', { user: $user?.email, loading: $loading, currentPath });
			
			if (!publicPages.includes(currentPath) && !isDocsPage) {
				// If user is not authenticated and not on a public page or docs page, redirect to login
				if (!$user && !$loading) {
					console.log('User not authenticated, redirecting to login');
					goto('/login');
				}
			} else if (currentPath === '/login' && $user) {
				// If user is authenticated and on login page, redirect to dashboard
				console.log('User authenticated, redirecting to dashboard');
				try {
					await goto('/dashboard');
					console.log('goto completed successfully');
				} catch (error) {
					console.error('goto failed, using window.location:', error);
					window.location.href = '/dashboard';
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

<div class="min-h-screen bg-white">
	<!-- Sticky Header - Only show on root and info pages -->
	{#if showNavigation}
		<header class="sticky top-0 z-50 bg-white border-b border-gray-300">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex justify-end items-center h-16">
					<!-- Simple Navigation with Line Separators -->
					<nav class="flex items-center">
						<a href="/" class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 transition-colors duration-200">Home</a>
						<div class="w-px h-4 bg-gray-300 mx-2"></div>
						<a href="/docs" class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 transition-colors duration-200">Docs</a>
						<div class="w-px h-4 bg-gray-300 mx-2"></div>
						<a href="/login" class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 transition-colors duration-200">Login</a>
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
