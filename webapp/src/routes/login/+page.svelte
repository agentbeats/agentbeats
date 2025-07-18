<script lang="ts">
	import { signInWithGitHub, signInWithSlack } from "$lib/auth/supabase";
	import { 
		signInWithEmail, 
		signUpWithEmail, 
		signInWithMagicLink,
		error as authError,
		loading as authLoading,
		setUser
	} from "$lib/stores/auth";
	import { goto } from "$app/navigation";
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
	import { Input } from "$lib/components/ui/input";
	import { Label } from "$lib/components/ui/label";
	import { Separator } from "$lib/components/ui/separator";
	import { Tabs, TabsContent, TabsList, TabsTrigger } from "$lib/components/ui/tabs";
	import { Github, Slack } from "@lucide/svelte";

	let email = "";
	let password = "";
	let confirmPassword = "";
	let isSignUp = false;
	let magicLinkSent = false;
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

	async function handleEmailAuth() {
		localError = "";
		
		if (!email || !password) {
			localError = "Please fill in all fields.";
			return;
		}

		if (isSignUp && password !== confirmPassword) {
			localError = "Passwords do not match.";
			return;
		}

		try {
			let success = false;
			
			if (isSignUp) {
				success = await signUpWithEmail(email, password);
				if (success) {
					localError = "Check your email to confirm your account!";
				}
			} else {
				success = await signInWithEmail(email, password);
			}
			
			if (!success && !localError) {
				localError = isSignUp ? "Failed to create account. Please try again." : "Invalid email or password.";
			}
		} catch (err) {
			localError = isSignUp ? "Failed to create account. Please try again." : "Failed to sign in. Please try again.";
			console.error("Email auth error:", err);
		}
	}

	async function handleMagicLink() {
		localError = "";
		
		if (!email) {
			localError = "Please enter your email address.";
			return;
		}

		try {
			const success = await signInWithMagicLink(email);
			if (success) {
				magicLinkSent = true;
			} else {
				localError = "Failed to send magic link. Please try again.";
			}
		} catch (err) {
			localError = "Failed to send magic link. Please try again.";
			console.error("Magic link error:", err);
		}
	}

	function resetForm() {
		email = "";
		password = "";
		confirmPassword = "";
		localError = "";
		magicLinkSent = false;
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
				{#if magicLinkSent}
					<div class="text-center space-y-4">
						<div class="text-green-600 text-sm">
							Magic link sent! Check your email and click the link to sign in.
						</div>
						<button on:click={resetForm} class="w-full bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50 border h-9 px-4 py-2 rounded-md text-sm font-medium">
							Back to Sign In
						</button>
					</div>
				{:else}
					<Tabs value="oauth" class="w-full">
						<TabsList class="grid w-full grid-cols-3">
							<TabsTrigger value="oauth">OAuth</TabsTrigger>
							<TabsTrigger value="email">Email</TabsTrigger>
							<TabsTrigger value="magic">Magic Link</TabsTrigger>
						</TabsList>
						
						<TabsContent value="oauth" class="space-y-4">
							<div class="space-y-3">
								<button 
									on:click={handleGitHubLogin}
									disabled={$authLoading}
									class="w-full bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50 border h-9 px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2"
								>
									{#if $authLoading}
										<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
									{:else}
										<span class="flex items-center"><Github class="h-4 w-4 mr-2 relative top-[1px]" />Continue with GitHub</span>
									{/if}
								</button>
								
								<button 
									on:click={handleSlackLogin}
									disabled={$authLoading}
									class="w-full bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50 border h-9 px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2"
								>
									{#if $authLoading}
										<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
									{:else}
										<span class="flex items-center"><Slack class="h-4 w-4 mr-2 relative top-[1px]" />Continue with Slack</span>
									{/if}
								</button>
							</div>
						</TabsContent>
						
						<TabsContent value="email" class="space-y-4">
							<div class="space-y-4">
								<div class="space-y-2">
									<Label for="email">Email</Label>
									<Input 
										id="email"
										type="email" 
										bind:value={email}
										placeholder="Enter your email"
										required
									/>
								</div>
								
								<div class="space-y-2">
									<Label for="password">Password</Label>
									<Input 
										id="password"
										type="password" 
										bind:value={password}
										placeholder="Enter your password"
										required
									/>
								</div>
								
								{#if isSignUp}
									<div class="space-y-2">
										<Label for="confirm-password">Confirm Password</Label>
										<Input 
											id="confirm-password"
											type="password" 
											bind:value={confirmPassword}
											placeholder="Confirm your password"
											required
										/>
									</div>
								{/if}
								
								<button 
									on:click={handleEmailAuth}
									disabled={$authLoading}
									class="w-full bg-primary text-primary-foreground shadow-xs hover:bg-primary/90 h-9 px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:pointer-events-none"
								>
									{#if $authLoading}
										<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
									{/if}
									{isSignUp ? 'Create Account' : 'Sign In'}
								</button>
								
								<button 
									on:click={() => isSignUp = !isSignUp}
									class="w-full text-sm hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50 h-9 px-4 py-2 rounded-md font-medium"
								>
									{isSignUp ? 'Already have an account? Sign In' : 'Need an account? Sign Up'}
								</button>
							</div>
						</TabsContent>
						
						<TabsContent value="magic" class="space-y-4">
							<div class="space-y-4">
								<div class="space-y-2">
									<Label for="magic-email">Email</Label>
									<Input 
										id="magic-email"
										type="email" 
										bind:value={email}
										placeholder="Enter your email"
										required
									/>
								</div>
								
								<button 
									on:click={handleMagicLink}
									disabled={$authLoading}
									class="w-full bg-primary text-primary-foreground shadow-xs hover:bg-primary/90 h-9 px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:pointer-events-none"
								>
									{#if $authLoading}
										<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
									{/if}
									Send Magic Link
								</button>
								
								<p class="text-xs text-gray-600 text-center">
									We'll send you a secure link to sign in without a password
								</p>
							</div>
						</TabsContent>
					</Tabs>
					
					{#if localError || $authError}
						<div class="text-red-600 text-sm text-center mt-4">
							{localError || $authError?.message}
						</div>
					{/if}
					
					<div class="text-center text-sm text-gray-600 mt-6">
						<p>By continuing, you agree to our Terms of Service and Privacy Policy (do later)</p>
					</div>
				{/if}
			</CardContent>
		</Card>
		<div class="mt-8 flex flex-col items-center">
			<button on:click={handleDevLogin} class="w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors mt-4">
				🚀 Automatic Login (Dev Only)
			</button>
			<span class="text-xs text-gray-500 mt-2">For development/testing only. Bypasses real authentication.</span>
		</div>
	</div>
</div> 