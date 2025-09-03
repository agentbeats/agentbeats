<script lang="ts">
	import { signInWithGitHub, supabase } from "$lib/auth/supabase";
	import { 
		error as authError,
		loading as authLoading,
		user
	} from "$lib/stores/auth";
	import { goto } from "$app/navigation";
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
	import { Button } from "$lib/components/ui/button";
	import { Github, MoveLeft, Zap } from "@lucide/svelte";
	import { onMount } from 'svelte';

	let localError = "";
	
	// Check if dev login is enabled
	const isDevMode = import.meta.env.VITE_DEV_LOGIN === "true";

	// In dev mode, redirect immediately if user is already set
	onMount(() => {
		if (isDevMode) {
			// Check if user is already authenticated
			user.subscribe(currentUser => {
				if (currentUser) {
					console.log('Dev mode: User already authenticated, redirecting to intended destination');
					// Redirect to intended destination or dashboard as fallback
					const redirectTo = new URLSearchParams(window.location.search).get('redirect') || '/dashboard';
					goto(redirectTo);
				}
			});
		}
	});

	async function handleGitHubLogin() {
		localError = "";
		console.log("Starting GitHub OAuth flow...");
		try {
			const result = await signInWithGitHub();
			console.log("GitHub OAuth initiated:", result);
			// The OAuth flow will redirect to GitHub, then back to /auth/callback
		} catch (err) {
			localError = "Failed to sign in with GitHub. Please try again.";
			console.error("GitHub login error:", err);
		}
	}

	async function handleDevLogin() {
		localError = "";
		console.log("Development login, signing in with dev user...");
		
		try {
			// In dev mode, we don't need to actually call supabase
			// The mock client will handle this, or we can set user directly
			console.log("Dev login successful - redirecting to intended destination");
			// Redirect to intended destination or dashboard as fallback
			const redirectTo = new URLSearchParams(window.location.search).get('redirect') || '/dashboard';
			goto(redirectTo);
			
		} catch (err) {
			console.error("Dev login error:", err);
			localError = "Dev login failed. Please try again.";
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-background p-4">
	<div class="w-full max-w-md">
		<div class="flex items-center gap-4 mb-6">
			<Button 
				onclick={() => goto('/')}
				class="btn-primary flex items-center gap-2"
			>
				<MoveLeft class="h-4 w-4" />
				Back to Home
			</Button>
		</div>
		
		<Card class="shadow-lg">
			<CardHeader class="text-center">
				<CardTitle class="text-2xl font-bold">Welcome to AgentBeats</CardTitle>
			</CardHeader>
			<CardContent>
				<div class="space-y-4">
					<!-- GitHub OAuth Button -->
					<Button 
						onclick={handleGitHubLogin}
						disabled={$authLoading}
						class="w-full btn-primary"
					>
						{#if $authLoading}
							<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
						{:else}
							<span class="flex items-center"><Github class="h-4 w-4 mr-2 relative top-[1px]" />Continue with GitHub</span>
						{/if}
					</Button>
					
					<!-- Dev Login Button (only shown in dev mode) -->
					{#if isDevMode}
						<div class="border-t pt-4">
							<Button 
								onclick={handleDevLogin}
								class="w-full bg-green-600 hover:bg-green-700 text-white"
								disabled={$authLoading}
							>
								{#if $authLoading}
									<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
								{:else}
									<Zap class="h-4 w-4 mr-2" />
									🚀 Dev Login
								{/if}
							</Button>
						</div>
					{/if}
					
					{#if localError || $authError}
						<div class="text-red-600 text-sm text-center mt-4">
							{localError || $authError?.message}
						</div>
					{/if}
				</div>
			</CardContent>
		</Card>
	</div>
</div> 