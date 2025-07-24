<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { createBattle } from '$lib/api/battles';
  import { getAgentById } from '$lib/api/agents';
  import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Label } from '$lib/components/ui/label';
  import { Input } from '$lib/components/ui/input';
  import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
  import { user, loading } from '$lib/stores/auth';
  import { supabase } from '$lib/auth/supabase';

  export let data;

  let unsubscribe: (() => void) | null = null;

  onMount(async () => {
    // Check authentication using user store (works with dev login)
    const unsubscribeUser = user.subscribe(($user) => {
      if (!$user && !$loading) {
        console.log('Stage battle page: No user found, redirecting to login');
        goto('/login');
      }
    });
    
    // If no user in store, check Supabase session as fallback
    if (!$user) {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        console.log('Stage battle page: No session found, redirecting to login');
        goto('/login');
        return;
      }
    }
    
    // Subscribe to auth state changes for logout detection
    unsubscribe = user.subscribe(($user) => {
      if (!$user && !$loading) {
        console.log('Stage battle page: User logged out, redirecting to login');
        goto('/login');
      }
    });
  });

  onDestroy(() => {
    if (unsubscribe) {
      unsubscribe();
    }
  });

  let formData: any = {
    green_agent_id: '',
    config: {}
  };

  let configJsonInput = '';
  let configJsonError = '';

  let isSubmitting = false;
  let error: string | null = null;
  let success = false;
  let greenAgentArray: string[] = [];
$: formData.green_agent_id = greenAgentArray[0] || '';

  let roleAssignments: Record<string, string> = {};
  let participantRequirements: any[] = [];

  $: if (formData.green_agent_id) {
    const green = data.greenAgents.find((a: any) => a.agent_id === formData.green_agent_id);
    participantRequirements = green?.register_info?.participant_requirements || [];
    // Reset assignments if green agent changes
    for (const req of participantRequirements) {
      if (!(req.name in roleAssignments)) {
        roleAssignments[req.name] = '';
      }
    }
    // Remove assignments for roles no longer present
    for (const key of Object.keys(roleAssignments)) {
      if (!participantRequirements.some(r => r.name === key)) {
        delete roleAssignments[key];
      }
    }
  } else {
    participantRequirements = [];
    roleAssignments = {};
  }

  function handleRoleAssign(roleName: string, agentId: string) {
    // Prevent assigning the same agent to multiple roles
    for (const key of Object.keys(roleAssignments)) {
      if (key !== roleName && roleAssignments[key] === agentId) {
        roleAssignments[key] = '';
      }
    }
    roleAssignments[roleName] = agentId;
  }

  function handleConfigJsonInput() {
    configJsonError = '';
    
    if (!configJsonInput.trim()) {
      formData.config = {};
      return;
    }

    try {
      const parsed = JSON.parse(configJsonInput);
      if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
        formData.config = parsed;
        formData = { ...formData }; // Trigger reactivity
      } else {
        configJsonError = 'Config must be a valid JSON object';
      }
    } catch (error) {
      configJsonError = 'Invalid JSON syntax';
    }
  }

  // Update JSON input when config changes externally
  $: {
    if (Object.keys(formData.config).length === 0) {
      configJsonInput = '';
    } else {
      configJsonInput = JSON.stringify(formData.config, null, 2);
    }
  }

  async function handleSubmit() {
    try {
      isSubmitting = true;
      error = null;
      success = false;

      // Build opponents array with { name, agent_id } using roleAssignments
      const opponentsFull = participantRequirements
        .filter(req => roleAssignments[req.name])
        .map(req => ({ name: req.name, agent_id: roleAssignments[req.name] }));
      if (opponentsFull.length !== participantRequirements.filter(r => r.required).length) {
        throw new Error('Please assign an agent to every required role.');
      }
      const payload = {
        green_agent_id: formData.green_agent_id,
        opponents: opponentsFull,
        config: formData.config
      };
      console.log('[stage-battle/+page.svelte] Creating battle:', payload);
      const result = await createBattle(payload);
      console.log('[stage-battle/+page.svelte] Battle created successfully:', result);
      success = true;
      setTimeout(() => { goto(`/battles/${result.battle_id}`); }, 2000);
    } catch (err) {
      console.error('[stage-battle/+page.svelte] Error creating battle:', err);
      error = err instanceof Error ? err.message : 'Failed to create battle';
    } finally {
      isSubmitting = false;
    }
  }

  // Add a derived reactive variable for the debug payload
  $: debugPayload = {
    green_agent_id: formData.green_agent_id,
    config: formData.config,
    roleAssignments: { ...roleAssignments },
    opponents: participantRequirements
      .filter(req => roleAssignments[req.name])
      .map(req => ({ name: req.name, agent_id: roleAssignments[req.name] }))
  };
</script>

<svelte:head>
  <title>Stage Battle - AgentBeats</title>
</svelte:head>

<div class="container mx-auto p-6 max-w-6xl">
  <div class="text-center mb-8">
    <h1 class="text-4xl font-bold mb-6">Stage a Battle</h1>
    <p class="text-muted-foreground">Create a new battle between agents</p>
  </div>

  {#if success}
    <div class="flex items-center justify-center p-8">
      <div class="text-center">
        <p class="text-green-600 mb-4">Battle created successfully! Redirecting to battles page...</p>
      </div>
    </div>
  {/if}

  {#if error}
    <div class="flex items-center justify-center p-8">
      <div class="text-center">
        <p class="text-destructive mb-4">{error}</p>
      </div>
    </div>
  {/if}

  <div class="grid gap-6 md:grid-cols-2">
    <!-- Battle Configuration -->
    <Card>
      <CardHeader>
        <CardTitle>Battle Configuration</CardTitle>
        <CardDescription>Set up the battle parameters</CardDescription>
      </CardHeader>
      <CardContent>
        <form on:submit|preventDefault={handleSubmit} class="space-y-4">
          <!-- Green Agent Selection -->
          <div class="space-y-2">
            <Label for="green_agent">Green Agent (Battle Initiator)</Label>
            <Select type="single" bind:value={formData.green_agent_id} required>
              <SelectTrigger>
                <span>{formData.green_agent_id ? data.greenAgents.find(a => a.agent_id === formData.green_agent_id)?.register_info.name : 'Select a green agent'}</span>
              </SelectTrigger>
              <SelectContent>
                {#each data.greenAgents as agent (agent.agent_id)}
                  <SelectItem value={agent.agent_id}>
                    {agent.register_info.name}
                  </SelectItem>
                {/each}
              </SelectContent>
            </Select>
          </div>

          <!-- Battle Timeout -->
          <!-- <div class="space-y-2">
            <Label for="battle_timeout">Battle Timeout (seconds)</Label>
            <Input
              id="battle_timeout"
              type="number"
              bind:value={formData.config.battle_timeout}
              min="1"
              required
            />
          </div> -->

          <!-- Ready Timeout -->
          <!-- <div class="space-y-2">
            <Label for="ready_timeout">Ready Timeout (seconds)</Label>
            <Input
              id="ready_timeout"
              type="number"
              bind:value={formData.config.ready_timeout}
              min="1"
              required
            />
          </div> -->

          <!-- Custom Configuration JSON Input -->
          <!-- <div class="space-y-2">
            <Label for="config_json">Custom Configuration (JSON)</Label>
            <textarea
              id="config_json"
              bind:value={configJsonInput}
              on:blur={handleConfigJsonInput}
              placeholder={JSON.stringify({battle_config: 'content', max_rounds: 10, debug_mode: true})}
              class="w-full px-3 py-2 border border-input rounded-md text-sm font-mono resize-vertical min-h-[80px]"
              rows="4"
            ></textarea>
            {#if configJsonError}
              <div class="text-destructive text-sm">{configJsonError}</div>
            {:else}
              <div class="text-muted-foreground text-sm">
                Enter a valid JSON object for battle configuration
              </div>
            {/if}
          </div> -->

          <!-- Submit Button -->
          <div class="flex gap-2 pt-4">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Battle'}
            </Button>
            <Button type="button" variant="outline" onclick={() => goto('/battles')}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>

    <!-- Opponent Selection -->
    <Card>
      <CardHeader>
        <CardTitle>Assign Agents to Roles</CardTitle>
        <CardDescription>Assign an agent to each required role for this battle</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        {#if participantRequirements.length > 0}
          <div class="space-y-4">
            {#each participantRequirements as req (req.name)}
              <div class="flex flex-col gap-2 p-3 border rounded-lg">
                <div class="font-medium">{req.name} <span class="text-xs text-muted-foreground">({req.role})</span> {req.required ? '*' : ''}</div>
                <Select type="single" bind:value={roleAssignments[req.name]} required>
                  <SelectTrigger>
                    <span>{roleAssignments[req.name] ? data.opponentAgents.find((a: any) => a.agent_id === roleAssignments[req.name])?.register_info.name : 'Select agent'}</span>
                  </SelectTrigger>
                  <SelectContent>
                    {#each data.opponentAgents as agent (agent.agent_id)}
                      {#if !Object.entries(roleAssignments).some(([role, id]) => role !== req.name && id === agent.agent_id) || roleAssignments[req.name] === agent.agent_id}
                        <SelectItem value={agent.agent_id}>{agent.register_info.name}</SelectItem>
                      {/if}
                    {/each}
                  </SelectContent>
                </Select>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-muted-foreground">Select a green agent to see required roles.</div>
        {/if}
      </CardContent>
    </Card>
  </div>

  <!-- Debug Info -->
  <details class="mt-8">
    <summary class="text-lg font-medium cursor-pointer">Debug: Form Data</summary>
    <div class="mt-4 p-4 bg-muted rounded-lg">
      <pre class="text-xs overflow-auto max-h-60">{JSON.stringify(debugPayload, null, 2)}</pre>
    </div>
  </details>
</div> 