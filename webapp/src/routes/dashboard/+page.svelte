<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import { goto } from "$app/navigation";
	import { user, isAuthenticated, loading } from "$lib/stores/auth";
	import { signOut, supabase } from "$lib/auth/supabase";
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
	import UserProfile from "$lib/components/user-profile.svelte";

	export const title = 'Dashboard';

	// Development bypass flag
	const SKIP_AUTH = import.meta.env.VITE_SKIP_AUTH === 'true';

	let unsubscribe: (() => void) | null = null;

	onMount(async () => {
		// Skip authentication check if VITE_SKIP_AUTH is set to 'true'
		if (SKIP_AUTH) {
			console.log('Dashboard page: Skipping authentication (VITE_SKIP_AUTH=true)');
			return;
		}

		// Check authentication using user store (works with dev login)
		const unsubscribeUser = user.subscribe(($user) => {
			if (!$user && !$loading) {
				console.log('Dashboard page: No user found, redirecting to login');
				goto('/login');
			}
		});
		
		// If no user in store, check Supabase session as fallback
		if (!$user) {
			const { data: { session } } = await supabase.auth.getSession();
			if (!session) {
				console.log('Dashboard page: No session found, redirecting to login');
				goto('/login');
				return;
			}
		}
		
		// Subscribe to auth state changes for logout detection
		unsubscribe = user.subscribe(($user) => {
			if (!$user && !$loading) {
				console.log('Dashboard page: User logged out, redirecting to login');
				goto('/login');
			}
		});
	});

	onDestroy(() => {
		if (unsubscribe) {
			unsubscribe();
		}
	});

	async function handleLogout() {
		// Skip logout if VITE_SKIP_AUTH is set to 'true'
		if (SKIP_AUTH) {
			console.log('Dashboard page: Skipping logout (VITE_SKIP_AUTH=true)');
			return;
		}

		try {
			await signOut();
			// Don't redirect, just let the page update
		} catch (error) {
			console.error('Logout error:', error);
		}
	}
</script>

<main class="flex-1 p-6 flex flex-col items-center justify-start">
	{#if $loading && !SKIP_AUTH}
		<div class="flex items-center justify-center h-64">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			<span class="ml-2">Loading...</span>
		</div>
	{:else}
		<div class="w-full max-w-6xl mx-auto">
			<div class="flex justify-between items-center mb-6">
				<h2 class="text-2xl font-bold">Dashboard</h2>
				<div class="flex items-center gap-4">
					{#if $user || SKIP_AUTH}
						<span class="text-sm text-gray-600">
							{#if SKIP_AUTH}
								Welcome, Test User (Development Mode)
							{:else}
								Welcome, {$user?.user_metadata?.name || $user?.email || 'User'}
							{/if}
						</span>
						<button 
							on:click={handleLogout}
							class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
						>
							{#if SKIP_AUTH}
								Development Mode
							{:else}
								Logout
							{/if}
						</button>
					{:else}
						<button 
							on:click={() => goto('/login')}
							class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
						>
							Sign In
						</button>
					{/if}
				</div>
			</div>
			
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<!-- User Profile or Login Prompt -->
				<div class="lg:col-span-1">
					{#if $user}
						<UserProfile />
					{:else}
						<Card>
							<CardHeader>
								<CardTitle>Get Started</CardTitle>
								<CardDescription>
									Sign in to access your profile and battle stats!
								</CardDescription>
							</CardHeader>
							<CardContent>
								<button 
									on:click={() => goto('/login')}
									class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
								>
									Sign In to Continue!
								</button>
							</CardContent>
						</Card>
					{/if}
				</div>
				
				<!-- Main Dashboard Content -->
				<div class="lg:col-span-2 space-y-6">
					<Card>
						<CardHeader>
							<CardTitle>Welcome to AgentBeats!</CardTitle>
						</CardHeader>
						<CardContent>
							{#if $user}
								<p class="text-muted-foreground">
									Here's your dashboard! Here, you'll see your battle history, agents, and ranking (do later).
								</p>
							{:else}
								<p class="text-muted-foreground">
									Sign in to start battling AI agents, track your performance, and climb the leaderboard.
								</p>
							{/if}
						</CardContent>
					</Card>
					
					<Card>
						<CardHeader>
							<CardTitle>Quick Actions</CardTitle>
						</CardHeader>
						<CardContent class="grid grid-cols-2 gap-4">
							<button 
								on:click={() => goto('/agents')}
								class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
							>
								Manage Agents
							</button>
							<button 
								on:click={() => goto('/battles')}
								class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
							>
								View Battles
							</button>
						</CardContent>
					</Card>
				</div>
			</div>
		</div>
	{/if}
</main>
