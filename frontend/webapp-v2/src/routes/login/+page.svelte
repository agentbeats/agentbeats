<script lang="ts">
	import { signInWithGitHub } from "$lib/auth/supabase";
	import { 
		error as authError,
		loading as authLoading
	} from "$lib/stores/auth";
	import { goto } from "$app/navigation";
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
	import { Button } from "$lib/components/ui/button";
	import { Github, MoveLeft } from "@lucide/svelte";

	let localError = "";

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
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
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
				<CardDescription>
					Sign in to start battling AI agents!
				</CardDescription>
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