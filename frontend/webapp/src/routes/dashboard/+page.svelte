<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import { goto } from "$app/navigation";
	import { user, isAuthenticated, loading } from "$lib/stores/auth";
	import { signOut, supabase } from "$lib/auth/supabase";
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
	import UserProfile from "$lib/components/user-profile.svelte";
	import { getAllBattles } from "$lib/api/battles";

	export const title = 'Dashboard';

	// Development bypass flag
	const SKIP_AUTH = import.meta.env.VITE_SKIP_AUTH === 'true';

	let unsubscribe: (() => void) | null = null;
	let battles = $state<any[]>([]);
	let battlesLoading = $state(true);

	onMount(async () => {
		// Skip authentication check if VITE_SKIP_AUTH is set to 'true'
		if (SKIP_AUTH) {
			console.log('Dashboard page: Skipping authentication (VITE_SKIP_AUTH=true)');
		} else {
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
		}

		// Load battles
		try {
			battles = await getAllBattles();
		} catch (error) {
			console.error('Failed to load battles:', error);
			battles = [];
		} finally {
			battlesLoading = false;
		}
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

	const username = $derived(SKIP_AUTH ? 'Test User' : ($user?.user_metadata?.name || $user?.email || 'User'));
</script>

<main class="flex-1 p-6">
	<div class="w-full max-w-7xl mx-auto">
		<!-- Welcome Message -->
		<div class="mb-6">
			<h1 class="text-3xl font-bold text-gray-900">Welcome, {username}</h1>
		</div>

		<!-- Two Cards Layout -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- User Info Card (Wider) -->
			<div class="lg:col-span-2">
				<Card>
					<CardHeader>
						<CardTitle>User Information</CardTitle>
						<CardDescription>Your profile and account details</CardDescription>
					</CardHeader>
					<CardContent>
						{#if $user || SKIP_AUTH}
							<UserProfile />
						{:else}
							<div class="text-center py-8">
								<p class="text-muted-foreground mb-4">Sign in to view your profile information</p>
								<button 
									on:click={() => goto('/login')}
									class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
								>
									Sign In
								</button>
							</div>
						{/if}
					</CardContent>
				</Card>
			</div>

			<!-- Past Battles Card -->
			<div class="lg:col-span-1">
				<Card>
					<CardHeader>
						<CardTitle>Past Battles</CardTitle>
						<CardDescription>Your recent battle history</CardDescription>
					</CardHeader>
					<CardContent>
						{#if battlesLoading}
							<div class="flex items-center justify-center py-4">
								<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
								<span class="ml-2 text-sm">Loading...</span>
							</div>
						{:else if battles.length === 0}
							<div class="text-center py-4">
								<p class="text-muted-foreground text-sm">No battles found</p>
								<button 
									on:click={() => goto('/battles/stage-battle')}
									class="mt-2 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
								>
									Start a Battle
								</button>
							</div>
						{:else}
							<div class="space-y-3">
								{#each battles.slice(0, 5) as battle}
									<div class="flex items-center justify-between p-3 border rounded-lg">
										<div class="flex-1">
											<p class="font-medium text-sm">{battle.battle_id?.slice(0, 8) || 'Unknown'}</p>
											<p class="text-xs text-muted-foreground">
												{battle.status || 'Unknown Status'}
											</p>
										</div>
										<button 
											on:click={() => goto(`/battles/${battle.battle_id}`)}
											class="text-xs text-blue-600 hover:text-blue-800"
										>
											View
										</button>
									</div>
								{/each}
								{#if battles.length > 5}
									<button 
										on:click={() => goto('/battles')}
										class="w-full text-sm text-blue-600 hover:text-blue-800 py-2"
									>
										View All Battles
									</button>
								{/if}
							</div>
						{/if}
					</CardContent>
				</Card>
			</div>
		</div>
	</div>
</main>
