<script lang="ts">
  import { goto } from '$app/navigation';
  import { registerAgent } from '$lib/api/agents';
  import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Label } from '$lib/components/ui/label';
  import { Input } from '$lib/components/ui/input';

  export let data: { agents: any[] };

  let formData: any = {
    name: '',
    agent_url: '',
    launcher_url: '',
    is_green: false,
    participant_requirements: []
  };

  let isSubmitting = false;
  let error: string | null = null;
  let success = false;

  function addParticipantRequirement() {
    formData.participant_requirements = [
      ...formData.participant_requirements,
      { role: '', name: '', required: false }
    ];
  }

  function removeParticipantRequirement(index: number) {
    formData.participant_requirements = formData.participant_requirements.filter((_: any, i: number) => i !== index);
  }

  async function handleSubmit() {
    try {
      isSubmitting = true;
      error = null;
      success = false;
      const result = await registerAgent(formData);
      success = true;
      formData = {
        name: '',
        agent_url: '',
        launcher_url: '',
        is_green: false,
        participant_requirements: []
      };
      setTimeout(() => goto('/agents'), 2000);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to register agent';
    } finally {
      isSubmitting = false;
    }
  }

  // Debug: post raw formData
  let debugError: string | null = null;
  let debugSuccess: boolean = false;
  async function handleDebugPost() {
    try {
      debugError = null;
      debugSuccess = false;
      await registerAgent(formData);
      debugSuccess = true;
    } catch (err) {
      debugError = err instanceof Error ? err.message : 'Failed to register agent (debug)';
    }
  }
</script>

<svelte:head>
  <title>Register Agent - AgentBeats</title>
</svelte:head>

<div class="container mx-auto p-6 max-w-6xl">
  <div class="text-center mb-8">
    <h1 class="text-4xl font-bold mb-6">Register New Agent</h1>
    <p class="text-muted-foreground">Register a new agent to participate in battles</p>
  </div>

  {#if success}
    <Card class="mb-6"><CardContent><div class="text-green-600">Agent registered successfully! Redirecting to agents page...</div></CardContent></Card>
  {/if}
  {#if error}
    <Card class="mb-6"><CardContent><div class="text-destructive">{error}</div></CardContent></Card>
  {/if}

  <div class="grid gap-6 md:grid-cols-2">
    <!-- Agent Info -->
    <Card>
      <CardHeader>
        <CardTitle>Agent Information</CardTitle>
        <CardDescription>Enter the details for your new agent</CardDescription>
      </CardHeader>
      <CardContent>
        <form on:submit|preventDefault={handleSubmit} class="space-y-4">
          <div class="space-y-2">
            <Label for="name">Agent Name</Label>
            <Input id="name" type="text" bind:value={formData.name} placeholder="My Agent" required />
          </div>
          <div class="space-y-2">
            <Label for="agent_url">Agent URL</Label>
            <Input id="agent_url" type="text" bind:value={formData.agent_url} placeholder="http://localhost:6001" required />
          </div>
          <div class="space-y-2">
            <Label for="launcher_url">Launcher URL</Label>
            <Input id="launcher_url" type="text" bind:value={formData.launcher_url} placeholder="http://localhost:6001/launcher" required />
          </div>
          <div class="flex items-center gap-2">
            <input type="checkbox" id="is_green" bind:checked={formData.is_green} />
            <Label for="is_green">Green Agent (Battle Initiator)</Label>
          </div>
          <div class="flex gap-2 pt-4">
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Registering...' : 'Register Agent'}</Button>
            <button type="button" class="btn btn-outline" on:click={() => goto('/agents')}>Cancel</button>
          </div>
        </form>
      </CardContent>
    </Card>

    <!-- Participant Requirements (if green agent) -->
    <Card>
      <CardHeader>
        <CardTitle>Participant Requirements</CardTitle>
        <CardDescription>Define required roles for this green agent</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <button type="button" class="btn btn-outline" on:click={addParticipantRequirement}>Add Requirement</button>
        {#if formData.is_green && formData.participant_requirements.length > 0}
          <div class="space-y-4">
            {#each formData.participant_requirements as requirement, index (index)}
              <div class="flex gap-2 items-center">
                <Input placeholder="Role" bind:value={requirement.role} class="w-1/3" />
                <Input placeholder="Name" bind:value={requirement.name} class="w-1/3" />
                <div class="flex items-center gap-1">
                  <input type="checkbox" bind:checked={requirement.required} id={`required-${index}`} />
                  <Label for={`required-${index}`}>Required</Label>
                </div>
                <button type="button" class="btn btn-outline btn-small" on:click={() => removeParticipantRequirement(index)}>Remove</button>
              </div>
            {/each}
          </div>
        {:else}
          <p class="text-muted-foreground">No participant requirements defined</p>
        {/if}
      </CardContent>
    </Card>
  </div>

  <details class="mt-8">
    <summary class="text-lg font-medium cursor-pointer">Debug: Form Data</summary>
    <div class="mt-4 p-4 bg-muted rounded-lg">
      <pre class="text-xs overflow-auto max-h-60">{JSON.stringify(formData, null, 2)}</pre>
      <!-- POST button and result messages removed as requested -->
    </div>
  </details>
</div> 