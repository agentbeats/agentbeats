<script lang="ts">
	import '../app.css';
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { user, loading } from '$lib/stores/auth';
	import { supabase } from '$lib/auth/supabase';
	import * as NavigationMenu from "$lib/components/ui/navigation-menu/index.js";
	import { navigationMenuTriggerStyle } from "$lib/components/ui/navigation-menu/navigation-menu-trigger.svelte";
	
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

<div class="min-h-screen bg-white">
	<!-- Sticky Header -->
	<header class="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-end items-center h-16">
				<!-- Navigation Menu -->
				<NavigationMenu.Root viewport={false}>
					<NavigationMenu.List class="flex space-x-1">
						<NavigationMenu.Item>
							<NavigationMenu.Link>
								{#snippet child()}
									<a href="/" class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors duration-200">Home</a>
								{/snippet}
							</NavigationMenu.Link>
						</NavigationMenu.Item>
						<NavigationMenu.Item>
							<NavigationMenu.Link>
								{#snippet child()}
									<a href="/about" class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors duration-200">About</a>
								{/snippet}
							</NavigationMenu.Link>
						</NavigationMenu.Item>
						<NavigationMenu.Item>
							<NavigationMenu.Link>
								{#snippet child()}
									<a href="/docs" class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors duration-200">Docs</a>
								{/snippet}
							</NavigationMenu.Link>
						</NavigationMenu.Item>
						<NavigationMenu.Item>
							<NavigationMenu.Link>
								{#snippet child()}
									<a href="/login" class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors duration-200">Login</a>
								{/snippet}
							</NavigationMenu.Link>
						</NavigationMenu.Item>
					</NavigationMenu.List>
				</NavigationMenu.Root>
			</div>
		</div>
	</header>
	
	<!-- Page Content -->
	<main>
		{@render children()}
	</main>
</div>
