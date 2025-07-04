<script lang="ts">
	import LoginForm from "$lib/components/login-form.svelte";
	import ShieldIcon from "@lucide/svelte/icons/shield-half";
</script>

<div class="bg-muted flex min-h-svh flex-col items-center justify-center gap-6 p-6 md:p-10">
	<div class="flex w-full max-w-sm flex-col gap-6">
		<a href="##" class="flex items-center gap-2 self-center font-medium">
			<div
				class="bg-primary text-primary-foreground flex size-8 items-center justify-center rounded-md"
			>
				<ShieldIcon class="size-5" />
			</div>
			AgentBeats
		</a>
		<LoginForm />
	</div>
</div>
