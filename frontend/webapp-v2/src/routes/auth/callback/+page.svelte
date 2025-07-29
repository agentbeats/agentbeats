<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/auth/supabase';

	let loading = true;
	let error = '';

	onMount(async () => {
		try {
			// Wait a bit for the session to be processed
			await new Promise(resolve => setTimeout(resolve, 1000));
			
			const { data, error: authError } = await supabase.auth.getSession();
			
			if (authError) {
				console.error('Auth callback error:', authError);
				error = 'Authentication failed. Please try again.';
				loading = false;
				return;
			}

			if (data.session) {
				console.log('Successfully authenticated, redirecting to dashboard');
				// Successfully authenticated, redirect to dashboard
				goto('/dashboard');
			} else {
				console.log('No session found, redirecting to login');
				// No session found, redirect to login
				goto('/login');
			}
		} catch (err) {
			console.error('Auth callback error:', err);
			error = 'Authentication failed. Please try again.';
			loading = false;
		}
	});
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50">
	<div class="text-center">
		{#if loading}
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
			<p class="text-gray-600">Completing authentication...</p>
		{:else if error}
			<div class="text-red-600 mb-4">{error}</div>
			<button onclick={() => goto('/login')} class="btn-primary">
				Back to Login
			</button>
		{/if}
	</div>
</div> 