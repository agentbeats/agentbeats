<script lang="ts">
	  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Spinner } from "$lib/components/ui/spinner";
	import { supabase } from '$lib/auth/supabase';

	let loading = true;
	let error = '';

	onMount(() => {
		console.log('Auth callback page mounted');
		
		// Listen for auth state changes instead of manually checking
		const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
			console.log('Auth callback - Auth state changed:', event, session?.user?.email);
			
					if (event === 'SIGNED_IN' && session) {
			console.log('Auth callback - User signed in successfully, redirecting to intended destination');
			loading = false;
			// Redirect to intended destination or dashboard as fallback
			const redirectTo = new URLSearchParams(window.location.search).get('redirect') || '/dashboard';
			goto(redirectTo);
		} else if (event === 'SIGNED_OUT' || (!session && event !== 'INITIAL_SESSION')) {
				console.log('Auth callback - No valid session, redirecting to login');
				loading = false;
				goto('/login');
			}
		});
		
		// Fallback: Check session after a longer delay
		setTimeout(async () => {
			if (loading) {
				console.log('Auth callback - Fallback: Checking session after delay');
				const { data, error: authError } = await supabase.auth.getSession();
				
				if (authError) {
					console.error('Auth callback error:', authError);
					error = 'Authentication failed. Please try again.';
					loading = false;
					return;
				}

				console.log('Auth callback - Fallback session data:', data);
				if (data.session) {
					console.log('Auth callback - Fallback: Successfully authenticated, redirecting to intended destination');
					loading = false;
					// Redirect to intended destination or dashboard as fallback
					const redirectTo = new URLSearchParams(window.location.search).get('redirect') || '/dashboard';
					goto(redirectTo);
				} else {
					console.log('Auth callback - Fallback: No session found, redirecting to login');
					loading = false;
					goto('/login');
				}
			}
		}, 3000); // Wait 3 seconds before fallback check
		
		// Cleanup subscription
		return () => {
			subscription.unsubscribe();
		};
	});
</script>

<div class="min-h-screen flex items-center justify-center bg-background">
	<div class="text-center">
		{#if loading}
			      <Spinner size="lg" centered />
			<p class="text-muted-foreground">Completing authentication...</p>
		{:else if error}
			<div class="text-destructive mb-4">{error}</div>
			<button onclick={() => goto('/login')} class="btn-primary">
				Back to Login
			</button>
		{/if}
	</div>
</div> 