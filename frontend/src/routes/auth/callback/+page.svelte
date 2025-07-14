<script lang="ts">
	import { onMount } from "svelte";
	import { goto } from "$app/navigation";
	import { supabase } from "$lib/auth/supabase";
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";

	let loading = true;
	let error = "";

	onMount(async () => {
		try {
			// Handle the OAuth callback
			const { data, error: authError } = await supabase.auth.getSession();
			
			if (authError) {
				throw authError;
			}
			
			if (data.session) {
				// Store the access token
				localStorage.setItem('auth_token', data.session.access_token);
				localStorage.setItem('user_id', data.session.user.id);
				
				// Redirect to dashboard
				setTimeout(() => {
					goto('/dashboard');
				}, 1000);
			} else {
				error = "Authentication failed. No session found.";
				loading = false;
			}
		} catch (err) {
			console.error("Auth callback error:", err);
			error = "Authentication failed. Please try again.";
			loading = false;
		}
	});
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
	<Card class="shadow-lg max-w-md w-full p-6">
		<CardHeader class="text-center space-y-2">
			<CardTitle class="text-2xl font-bold break-words">
				{loading ? 'Signing you in...' : 'Authentication Error'}
			</CardTitle>
			<CardDescription class="break-words">
				{loading ? 'Please wait while we complete your sign-in' : error}
			</CardDescription>
		</CardHeader>
		<CardContent class="text-center flex flex-col items-center gap-6">
			{#if loading}
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			{:else}
				<button 
					on:click={() => goto('/login')}
					class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
				>
					Back to Login
				</button>
			{/if}
		</CardContent>
	</Card>
</div> 