<script lang="ts">
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

  let isLoadingAgentCard = false;
  let agentCardError: string | null = null;
  let agentCard: any = null;
  let canRegister = true;

  let isAnalyzing = false;
  let analysisError: string | null = null;

  function addParticipantRequirement() {
    formData.participant_requirements = [
      ...formData.participant_requirements,
      { role: '', name: '', required: false }
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
      if (!formData.name.trim() && agentCard?.name) {
        formData.name = agentCard.name;
      }

      // 获取到 agent card 后自动分析
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
        name: formData.name.trim() || agentCard?.name || formData.name,
      };

      const result = await registerAgent(submitData);
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
    <Card class="mb-6"
      ><CardContent><div class="text-destructive">{error}</div></CardContent
      ></Card
    >
  {/if}

  {#if agentCardError}
    <Card class="mb-6"
      ><CardContent
        ><div class="text-destructive">
          Agent Card Error: {agentCardError}
        </div></CardContent
      ></Card
    >
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
            <Label for="agent_url">Agent URL</Label>
            <input
              id="agent_url"
              type="text"
              bind:value={formData.agent_url}
              placeholder="http://localhost:6001"
              on:blur={handleAgentUrlBlur}
              class="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
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
            <Input id="launcher_url" type="text" bind:value={formData.launcher_url} placeholder="http://localhost:6001/launcher" required />
          </div>
          <div class="space-y-2">
            <Label for="name">Agent Alias (Optional)</Label>
            <Input
              id="name"
              type="text"
              bind:value={formData.name}
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
            <button
              type="button"
              class="btn btn-outline"
              on:click={() => goto("/agents")}>Cancel</button
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
            🤖 AI is analyzing agent card and suggesting configuration...
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
              <button
                type="button"
                class="btn btn-outline mb-4"
                on:click={addParticipantRequirement}>Add Requirement</button
              >
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
                      <button
                        type="button"
                        class="btn btn-outline btn-small"
                        on:click={() => removeParticipantRequirement(index)}
                        >Remove</button
                      >
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="text-muted-foreground text-sm">
                  No participant requirements defined
                </p>
              {/if}
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

  <details class="mt-4">
    <summary class="text-lg font-medium cursor-pointer"
      >Agent Card Preview</summary
    >
    <div class="mt-4 p-4 bg-muted rounded-lg">
      {#if agentCard}
        <pre class="text-xs overflow-auto max-h-60">{JSON.stringify(
            agentCard,
            null,
            2
          )}</pre>
      {:else}
        <div class="text-muted-foreground text-sm">
          {#if isLoadingAgentCard}
            Loading agent card...
          {:else if agentCardError}
            Failed to load agent card: {agentCardError}
          {:else}
            No agent card loaded. Enter an agent URL to fetch the card.
          {/if}
        </div>
      {/if}
    </div>
  </details>
</div>