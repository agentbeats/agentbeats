<script lang="ts">
	import { signInWithGitHub, signInWithSlack } from "$lib/auth/supabase";
	import { 
		error as authError,
		loading as authLoading,
		setUser
	} from "$lib/stores/auth";
	import { goto } from "$app/navigation";
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
	import { Button } from "$lib/components/ui/button";

	let localError = "";

	async function handleGitHubLogin() {
		localError = "";
		try {
			await signInWithGitHub();
		} catch (err) {
			localError = "Failed to sign in with GitHub. Please try again.";
			console.error("GitHub login error:", err);
		}
	}

	async function handleSlackLogin() {
		localError = "";
		try {
			await signInWithSlack();
		} catch (err) {
			localError = "Failed to sign in with Slack. Please try again.";
			console.error("Slack login error:", err);
		}
	}

	function handleDevLogin() {
		setUser({
			id: 'dev-user-id',
			email: 'dev@example.com',
			user_metadata: { name: 'Dev User' },
			app_metadata: { provider: 'dev' },
			aud: 'authenticated',
			created_at: new Date().toISOString(),
			role: 'authenticated',
			confirmed_at: new Date().toISOString(),
			email_confirmed_at: new Date().toISOString(),
			phone: null,
			phone_confirmed_at: null,
			last_sign_in_at: new Date().toISOString(),
			invited_at: null,
			action_link: null,
			recovery_sent_at: null,
			new_email: null,
			new_phone: null,
			is_anonymous: false,
			identities: [],
			factor_ids: [],
			factors: [],
			...({} as any) // fallback for any extra fields
		});
		goto('/dashboard');
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
	<div class="w-full max-w-md">
		<Card class="shadow-lg">
			<CardHeader class="text-center">
				<CardTitle class="text-2xl font-bold">Welcome to AgentBeats</CardTitle>
				<CardDescription>
					Sign in to start battling AI agents!
				</CardDescription>
			</CardHeader>
			<CardContent>
				<div class="space-y-4">
					<!-- OAuth Buttons -->
					<div class="space-y-3">
						<Button 
							onclick={handleGitHubLogin}
							disabled={$authLoading}
							class="w-full btn-primary"
						>
							{#if $authLoading}
								<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
							{:else}
								Continue with GitHub
							{/if}
						</Button>
						
						<Button 
							onclick={handleSlackLogin}
							disabled={$authLoading}
							class="w-full btn-primary"
						>
							{#if $authLoading}
								<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
							{:else}
								Continue with Slack
							{/if}
						</Button>
					</div>
					
					{#if localError || $authError}
						<div class="text-red-600 text-sm text-center mt-4">
							{localError || $authError?.message}
						</div>
					{/if}
				</div>
			</CardContent>
		</Card>
		<div class="mt-8 flex flex-col items-center">
			<Button onclick={handleDevLogin} class="w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors">
				🚀 Automatic Login (Dev Only)
			</Button>
			<span class="text-xs text-gray-500 mt-2">For development/testing only. Bypasses real authentication.</span>
		</div>
	</div>
</div> 