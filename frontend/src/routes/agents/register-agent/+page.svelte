<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import {
    registerAgent,
    fetchAgentCard,
    analyzeAgentCard,
  } from "$lib/api/agents";
  import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { Input } from "$lib/components/ui/input";
  import { user, loading } from "$lib/stores/auth";
  import { supabase } from "$lib/auth/supabase";

  export const data: { agents: any[] } = $props();

  let unsubscribe: (() => void) | null = null;

  onMount(async () => {
    // Check authentication immediately
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      console.log('Register agent page: No session found, redirecting to login');
      goto('/login');
      return;
    }
    
    // Subscribe to auth state changes for logout detection
    unsubscribe = user.subscribe(($user) => {
      if (!$user && !$loading) {
        console.log('Register agent page: User logged out, redirecting to login');
        goto('/login');
      }
    });
  });

  onDestroy(() => {
    if (unsubscribe) {
      unsubscribe();
    }
  });

  let formData: any = $state({
    alias: "",
    agent_url: "",
    launcher_url: "",
    is_green: false,
    participant_requirements: [],
    battle_timeout: 300,
  });

  let isSubmitting = $state(false);
  let error: string | null = $state(null);
  let success = $state(false);

  let isLoadingAgentCard = $state(false);
  let agentCardError: string | null = $state(null);
  let agentCard: any = $state(null);
  let canRegister = $state(true);

  let isAnalyzing = $state(false);
  let analysisError: string | null = $state(null);

  function addParticipantRequirement() {
    formData.participant_requirements = [
      ...formData.participant_requirements,
      { role: "", name: "", required: false },
    ];
  }

  function removeParticipantRequirement(index: number) {
    formData.participant_requirements =
      formData.participant_requirements.filter(
        (_: any, i: number) => i !== index
      );
  }

  async function loadAgentCard() {
    if (!formData.agent_url.trim()) {
      agentCard = null;
      agentCardError = null;
      canRegister = true;
      return;
    }

    try {
      isLoadingAgentCard = true;
      agentCardError = null;
      agentCard = await fetchAgentCard(formData.agent_url);
      canRegister = true;

      // Auto-fill name from agent card if form name is empty
      if (!formData.alias.trim() && agentCard?.name) {
        formData.alias = agentCard.name;
      }

      await analyzeAgentCardAutomatically();
    } catch (err) {
      agentCardError =
        err instanceof Error ? err.message : "Failed to load agent card";
      agentCard = null;
      canRegister = false;
    } finally {
      isLoadingAgentCard = false;
    }
  }

  async function analyzeAgentCardAutomatically() {
    if (!agentCard) return;

    try {
      isAnalyzing = true;
      analysisError = null;

      const analysis = await analyzeAgentCard(agentCard);

      if (analysis.is_green) {
        formData.is_green = true;
        formData.participant_requirements =
          analysis.participant_requirements || [];
        formData.battle_timeout = analysis.battle_timeout || 300;
      }
    } catch (err) {
      analysisError =
        err instanceof Error ? err.message : "Failed to analyze agent card";
      console.error("Agent card analysis failed:", err);
    } finally {
      isAnalyzing = false;
    }
  }

  function handleAgentUrlBlur() {
    loadAgentCard();
  }

  async function handleSubmit() {
    try {
      isSubmitting = true;
      error = null;
      success = false;

      // Use agent card name if no alias is provided
      const submitData = {
        ...formData,
        name: formData.alias.trim() || agentCard?.name || formData.alias,
      };

      const result = await registerAgent(submitData);
      success = true;
      formData = {
        name: "",
        agent_url: "",
        launcher_url: "",
        is_green: false,
        participant_requirements: [],
      };
      setTimeout(() => goto("/agents"), 2000);
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to register agent";
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
      debugError =
        err instanceof Error ? err.message : "Failed to register agent (debug)";
    }
  }
</script>

<svelte:head>
  <title>Register Agent - AgentBeats</title>
</svelte:head>

<div class="container mx-auto p-6 max-w-6xl">
  <div class="text-center mb-8">
    <h1 class="text-4xl font-bold mb-6">Register New Agent</h1>
    <p class="text-muted-foreground">
      Register a new agent to participate in battles
    </p>
  </div>

  {#if success}
    <Card class="mb-6"
      ><CardContent
        ><div class="text-green-600">
          Agent registered successfully! Redirecting to agents page...
        </div></CardContent
      ></Card
    >
  {/if}
  {#if error}
    <Card class="mb-6"
      ><CardContent><div class="text-destructive">{error}</div></CardContent
      ></Card
    >
  {/if}

  <!-- Agent Card Display -->
  <Card class="mb-6">
    <CardHeader>
      <CardTitle>Agent Card</CardTitle>
      <CardDescription>Preview of the agent information</CardDescription>
    </CardHeader>
    <CardContent>
      {#if isLoadingAgentCard}
        <div class="flex flex-col items-center justify-center py-8 space-y-4">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <div class="text-muted-foreground">Loading agent card...</div>
        </div>
      {:else if agentCardError}
        <div class="flex flex-col items-center justify-center py-8 space-y-4">
          <div class="text-6xl">🤖</div>
          <div class="text-destructive text-center">
            <div class="font-medium">Agent Card Error</div>
            <div class="text-sm mt-1">{agentCardError}</div>
          </div>
        </div>
      {:else if agentCard}
        <div class="space-y-4">
          <div class="flex items-center space-x-3">
            <div class="text-4xl">🤖</div>
            <div>
              <h3 class="font-semibold text-lg">{agentCard.name || 'Unnamed Agent'}</h3>
              {#if agentCard.description}
                <p class="text-muted-foreground text-sm">{agentCard.description}</p>
              {/if}
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            {#if agentCard.version}
              <div class="text-sm text-muted-foreground">
                <span class="font-medium">Version:</span> {agentCard.version}
              </div>
            {/if}
            {#if agentCard.protocolVersion}
              <div class="text-sm text-muted-foreground">
                <span class="font-medium">Protocol:</span> {agentCard.protocolVersion}
              </div>
            {/if}
          </div>
          {#if agentCard.capabilities && typeof agentCard.capabilities === 'object'}
            <div>
              <h4 class="font-medium text-sm mb-2">Capabilities:</h4>
              <div class="flex flex-wrap gap-1">
                {#each Object.entries(agentCard.capabilities) as [key, value]}
                  <span class="px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-xs">
                    {key}: {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                  </span>
                {/each}
              </div>
            </div>
          {/if}
          {#if agentCard.skills && agentCard.skills.length > 0}
            <div>
              <h4 class="font-medium text-sm mb-2">Skills:</h4>
              <div class="flex flex-wrap gap-1">
                {#each agentCard.skills as skill}
                  <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs">
                    {skill.name}
                  </span>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      {:else}
        <div class="flex flex-col items-center justify-center py-8 space-y-4">
          <div class="text-6xl">🤖</div>
          <div class="text-muted-foreground text-center">
            <div class="font-medium">Agent Card</div>
            <div class="text-sm">Enter an agent URL to load the card</div>
          </div>
        </div>
      {/if}
    </CardContent>
  </Card>

  <div class="grid gap-6 md:grid-cols-2">
    <!-- Agent Info -->
    <Card>
      <CardHeader>
        <CardTitle>Agent Information</CardTitle>
        <CardDescription>Enter the details for your new agent</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          onsubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          class="space-y-4"
        >
          <div class="space-y-2">
            <Label for="agent_url">Agent URL</Label>
            <Input
              id="agent_url"
              type="text"
              bind:value={formData.agent_url}
              placeholder="http://localhost:6001"
              onblur={handleAgentUrlBlur}
              required
            />
            {#if isLoadingAgentCard}
              <div class="text-sm text-muted-foreground">
                Loading agent card...
              </div>
            {/if}
          </div>
          <div class="space-y-2">
            <Label for="launcher_url">Launcher URL</Label>
            <Input
              id="launcher_url"
              type="text"
              bind:value={formData.launcher_url}
              placeholder="http://localhost:6001/launcher"
              required
            />
          </div>
          <div class="space-y-2">
            <Label for="name">Agent Alias (Optional)</Label>
            <Input
              id="name"
              type="text"
              bind:value={formData.alias}
              placeholder={agentCard?.name ||
                "Will use agent card name if not provided"}
            />
            <div class="text-xs text-muted-foreground">
              Leave empty to use the name from agent card: {agentCard?.name ||
                "Not loaded yet"}
            </div>
          </div>
          <div class="flex gap-2 pt-4">
            <Button type="submit" disabled={isSubmitting || !canRegister}>
              {isSubmitting ? "Registering..." : "Register Agent"}
            </Button>
            <Button variant="outline" onclick={() => goto("/agents")}
              >Cancel</Button
            >
          </div>
        </form>
      </CardContent>
    </Card>

    <!-- Agent Type & Requirements -->
    <Card>
      <CardHeader>
        <CardTitle>Agent Type & Requirements</CardTitle>
        <CardDescription>
          {#if isAnalyzing}
            Analyzing agent card and suggesting configuration...
          {:else}
            Configure agent type and participant requirements
          {/if}
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        {#if isAnalyzing}
          <div class="flex items-center justify-center py-8">
            <div
              class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
            ></div>
            <span class="ml-2 text-muted-foreground"
              >Analyzing agent card...</span
            >
          </div>
        {:else}
          <div class="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_green"
              bind:checked={formData.is_green}
            />
            <Label for="is_green">Green Agent (Battle Initiator)</Label>
          </div>

          {#if formData.is_green}
            <div class="border-t pt-4">
              <h4 class="font-medium mb-2">Participant Requirements</h4>
              <Button
                variant="outline"
                onclick={addParticipantRequirement}
                class="mb-4"
              >
                Add Requirement
              </Button>
              {#if formData.participant_requirements.length > 0}
                <div class="space-y-4">
                  {#each formData.participant_requirements as requirement, index (index)}
                    <div class="flex gap-2 items-center">
                      <Input
                        placeholder="Role"
                        bind:value={requirement.role}
                        class="w-1/3"
                      />
                      <Input
                        placeholder="Name"
                        bind:value={requirement.name}
                        class="w-1/3"
                      />
                      <div class="flex items-center gap-1">
                        <input
                          type="checkbox"
                          bind:checked={requirement.required}
                          id={`required-${index}`}
                        />
                        <Label for={`required-${index}`}>Required</Label>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onclick={() => removeParticipantRequirement(index)}
                      >
                        Remove
                      </Button>
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="text-muted-foreground text-sm">
                  No participant requirements defined
                </p>
              {/if}
            </div>
            <div class="border-t pt-4">
              <h4 class="font-medium mb-2">Battle Configuration</h4>
              <div class="space-y-2">
                <Label for="battle_timeout">Battle Timeout (seconds)</Label>
                <Input
                  id="battle_timeout"
                  type="number"
                  bind:value={formData.battle_timeout}
                  placeholder="300"
                  min="1"
                  class="w-full"
                />
                <div class="text-xs text-muted-foreground">
                  Maximum time allowed for the battle to complete
                </div>
              </div>
            </div>
          {:else}
            <p class="text-muted-foreground text-sm">
              This will be a regular participant agent
            </p>
          {/if}

          {#if analysisError}
            <div class="text-destructive text-sm">
              AI Analysis Error: {analysisError}
            </div>
          {/if}
        {/if}
      </CardContent>
    </Card>
  </div>

  <details class="mt-8">
    <summary class="text-lg font-medium cursor-pointer"
      >Debug: Form Data</summary
    >
    <div class="mt-4 p-4 bg-muted rounded-lg">
      <pre class="text-xs overflow-auto max-h-60">{JSON.stringify(
          formData,
          null,
          2
        )}</pre>
      <!-- POST button and result messages removed as requested -->
    </div>
  </details>
</div>
