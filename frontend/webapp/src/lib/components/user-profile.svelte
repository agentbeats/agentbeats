<script lang="ts">
	import { user, updateUser, resetPassword, error as authError } from '$lib/stores/auth';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';

	let isEditing = false;
	let newEmail = '';
	let newPassword = '';
	let confirmPassword = '';
	let newName = '';
	let localError = '';
	let successMessage = '';

	// Initialize form with current user data
	$: if ($user && !isEditing) {
		newEmail = $user.email || '';
		newName = $user.user_metadata?.name || '';
	}

	async function handleUpdateProfile() {
		localError = '';
		successMessage = '';

		if (newPassword && newPassword !== confirmPassword) {
			localError = 'Passwords do not match.';
			return;
		}

		try {
			const updates: any = {};
			
			if (newEmail !== $user?.email) {
				updates.email = newEmail;
			}
			
			if (newPassword) {
				updates.password = newPassword;
			}
			
			if (newName !== $user?.user_metadata?.name) {
				updates.data = { name: newName };
			}

			if (Object.keys(updates).length === 0) {
				localError = 'No changes to save.';
				return;
			}

			const updatedUser = await updateUser(updates);
			
			if (updatedUser) {
				successMessage = 'Profile updated successfully!';
				isEditing = false;
				newPassword = '';
				confirmPassword = '';
			} else {
				localError = 'Failed to update profile. Please try again.';
			}
		} catch (err) {
			localError = 'Failed to update profile. Please try again.';
			console.error('Update profile error:', err);
		}
	}

	async function handlePasswordReset() {
		localError = '';
		successMessage = '';

		if (!$user?.email) {
			localError = 'No email address available for password reset.';
			return;
		}

		try {
			const success = await resetPassword($user.email);
			
			if (success) {
				successMessage = 'Password reset email sent! Check your inbox.';
			} else {
				localError = 'Failed to send password reset email. Please try again.';
			}
		} catch (err) {
			localError = 'Failed to send password reset email. Please try again.';
			console.error('Password reset error:', err);
		}
	}

	function cancelEdit() {
		isEditing = false;
		newEmail = $user?.email || '';
		newName = $user?.user_metadata?.name || '';
		newPassword = '';
		confirmPassword = '';
		localError = '';
		successMessage = '';
	}
</script>

<Card>
	<CardHeader>
		<CardTitle>User Profile</CardTitle>
		<CardDescription>
			Manage your account settings and preferences
		</CardDescription>
	</CardHeader>
	<CardContent class="space-y-4">
		{#if $user}
			<div class="space-y-4">
				<!-- User Info Display -->
				{#if !isEditing}
					<div class="space-y-3">
						<div class="flex justify-between items-center">
							<div>
								<p class="text-sm font-medium">Email</p>
								<p class="text-sm text-gray-600">{$user.email}</p>
							</div>
						</div>
						
						{#if $user.user_metadata?.name}
							<div class="flex justify-between items-center">
								<div>
									<p class="text-sm font-medium">Name</p>
									<p class="text-sm text-gray-600">{$user.user_metadata.name}</p>
								</div>
							</div>
						{/if}
						
						<div class="flex justify-between items-center">
							<div>
								<p class="text-sm font-medium">Provider</p>
								<p class="text-sm text-gray-600">{$user.app_metadata?.provider || 'Email'}</p>
							</div>
						</div>
						
						<div class="flex justify-between items-center">
							<div>
								<p class="text-sm font-medium">Member Since</p>
								<p class="text-sm text-gray-600">{new Date($user.created_at).toLocaleDateString()}</p>
							</div>
						</div>
						
						<div class="flex gap-2 pt-2">
							<button 
								on:click={() => isEditing = true}
								class="px-3 py-1 bg-primary text-primary-foreground text-sm rounded-md hover:bg-primary/90"
							>
								Edit Profile
							</button>
							<button 
								on:click={handlePasswordReset}
								class="px-3 py-1 bg-secondary text-secondary-foreground text-sm rounded-md hover:bg-secondary/80"
							>
								Reset Password
							</button>
						</div>
					</div>
				{:else}
					<!-- Edit Form -->
					<div class="space-y-4">
						<div class="space-y-2">
							<Label for="edit-email">Email</Label>
							<Input 
								id="edit-email"
								type="email" 
								bind:value={newEmail}
								placeholder="Enter your email"
							/>
						</div>
						
						<div class="space-y-2">
							<Label for="edit-name">Name</Label>
							<Input 
								id="edit-name"
								type="text" 
								bind:value={newName}
								placeholder="Enter your name"
							/>
						</div>
						
						<div class="space-y-2">
							<Label for="edit-password">New Password (optional)</Label>
							<Input 
								id="edit-password"
								type="password" 
								bind:value={newPassword}
								placeholder="Enter new password"
							/>
						</div>
						
						{#if newPassword}
							<div class="space-y-2">
								<Label for="edit-confirm-password">Confirm New Password</Label>
								<Input 
									id="edit-confirm-password"
									type="password" 
									bind:value={confirmPassword}
									placeholder="Confirm new password"
								/>
							</div>
						{/if}
						
						<div class="flex gap-2">
							<button 
								on:click={handleUpdateProfile}
								class="px-3 py-1 bg-primary text-primary-foreground text-sm rounded-md hover:bg-primary/90"
							>
								Save Changes
							</button>
							<button 
								on:click={cancelEdit}
								class="px-3 py-1 bg-secondary text-secondary-foreground text-sm rounded-md hover:bg-secondary/80"
							>
								Cancel
							</button>
						</div>
					</div>
				{/if}
				
				<!-- Error and Success Messages -->
				{#if localError || $authError}
					<div class="text-red-600 text-sm">
						{localError || $authError?.message}
					</div>
				{/if}
				
				{#if successMessage}
					<div class="text-green-600 text-sm">
						{successMessage}
					</div>
				{/if}
			</div>
		{:else}
			<div class="text-center text-gray-600">
				<p>No user data available</p>
			</div>
		{/if}
	</CardContent>
</Card> 