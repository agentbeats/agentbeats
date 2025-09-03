<script lang="ts">
  import type { PageData } from "./$types.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import * as Form from "$lib/components/ui/form/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Switch } from "$lib/components/ui/switch/index.js";
  import { formSchema, type FormSchema } from "./schema";
  import {
    type SuperValidated,
    type Infer,
    superForm,
  } from "sveltekit-superforms";
  import { zodClient } from "sveltekit-superforms/adapters";
  import { fly } from 'svelte/transition';
  import { fetchAgentCard, analyzeAgentCard, checkLauncherStatus } from "$lib/api/agents";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import { goto } from "$app/navigation";
  import { toast } from 'svelte-sonner';
  import { onMount, onDestroy } from 'svelte';

  onMount(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    onDestroy(() => {
      document.body.style.overflow = prev;
    });
  });

  let { data }: { data: { form: SuperValidated<Infer<FormSchema>> } } = $props();

  const form = superForm(data.form, {
    validators: zodClient(formSchema),
    dataType: "json",
    onResult: ({ result }) => {
      console.log('Form submission result:', result);
      if (result.type === 'success') {
        if (result.data?.success) {
          toast.success('Agent registered successfully!', {
            position: 'top-center'
          });
          // Redirect to agents page after successful registration
          setTimeout(() => {
            goto('/agents');
          }, 1500);
        } else if (result.data?.error) {
          toast.error(result.data.error, {
            position: 'top-center'
          });
        }
      } else if (result.type === 'failure') {
        console.error('Form validation failed:', result);
        toast.error('Failed to register agent. Please try again.', {
          position: 'top-center'
        });
      }
    }
  });

  const { form: formData, enhance } = form;
  
  // Track if we're in transition to prevent squishing
  let showGreenForm = $state(false);
  let showThirdCard = $state(false); // Controls third card visibility
  let originalFormMoved = $state(false); // Controls original form position
  let formsPushedDown = $state(false); // Controls forms moving down for agent card
  
  // Agent card preview state
  let isLoadingAgentCard = $state(false);
  let agentCardError = $state<string | null>(null);
  let agentCard = $state<any>(null);
  
  // Analysis state
  let isAnalyzing = $state(false);
  let analysisError = $state<string | null>(null);
  
  // Status indicators for URLs
  let canRegister = $state(true);
  let isCheckingLauncher = $state(false);
  let launcherStatus = $state<'unknown' | 'checking' | 'online' | 'offline'>('unknown');
  
  $effect(() => {
    if ($formData.green && !showGreenForm) {
      // Show green form: move original first, then show green
      originalFormMoved = true;
      setTimeout(() => {
        showGreenForm = true;
      }, 250);
    } else if (!$formData.green && showGreenForm) {
      // Hide green form: hide green first, then move original back
      showGreenForm = false;
      setTimeout(() => {
        originalFormMoved = false;
      }, 250);
    }
  });
  
  $effect(() => {
    // Sync formsPushedDown with showThirdCard with proper delays
    if (showThirdCard) {
      formsPushedDown = true;
      // Agent card will appear after forms finish moving down
    } else {
      // Delay moving forms back up to wait for fly transition to complete
      setTimeout(() => {
        formsPushedDown = false;
      }, 800); // Longer delay for smoother fly out
    }
  });
  
  async function checkLauncherStatusAsync() {
    if (!$formData.launcher_url?.trim()) {
      launcherStatus = 'unknown';
      return;
    }

    try {
      isCheckingLauncher = true;
      launcherStatus = 'checking';

      // Use the backend API to check launcher status
      const result = await checkLauncherStatus($formData.launcher_url);
      launcherStatus = result.online ? 'online' : 'offline';
    } catch (err) {
      launcherStatus = 'offline';
      console.error("Launcher status check failed:", err);
    } finally {
      isCheckingLauncher = false;
    }
  }

  async function loadAgentCard() {
    if (!$formData.agent_url?.trim()) {
      agentCard = null;
      agentCardError = null;
      canRegister = true;
      showThirdCard = false;
      return;
    }

    try {
      isLoadingAgentCard = true;
      agentCardError = null;
      agentCard = await fetchAgentCard($formData.agent_url);
      canRegister = true;
      
      // Delay showing the card to let forms move down first
      setTimeout(() => {
        showThirdCard = true;
      }, 250);

      // Auto-fill alias from agent card
      if (agentCard?.name) {
        console.log('Setting alias to:', agentCard.name);
        $formData.alias = agentCard.name;
      }

      // Automatically analyze the agent card
      await analyzeAgentCardAutomatically();
    } catch (err) {
      agentCardError = err instanceof Error ? err.message : "Failed to load agent card";
      agentCard = null;
      canRegister = false;
      showThirdCard = false;
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
        $formData.green = true;
        $formData.participant_requirements = analysis.participant_requirements || [];
        $formData.battle_timeout = analysis.battle_timeout || 300;
      }
    } catch (err) {
      analysisError = err instanceof Error ? err.message : "Failed to analyze agent card";
      console.error("Agent card analysis failed:", err);
    } finally {
      isAnalyzing = false;
    }
  }

  function handleAgentUrlBlur() {
    loadAgentCard();
  }

  function handleLauncherUrlBlur() {
    checkLauncherStatusAsync();
  }
  
  function toggleThirdCard() {
    showThirdCard = !showThirdCard;
  }
  
  function addParticipantRequirement() {
    $formData.participant_requirements = [
      ...$formData.participant_requirements,
      { id: Date.now() + Math.random(), role: "", name: "", required: false },
    ];
  }

  function removeParticipantRequirement(index: number) {
    const requirements = [...$formData.participant_requirements];
    requirements.splice(index, 1);
    $formData.participant_requirements = requirements;
  }
</script>

<div class="min-h-screen flex items-center justify-center p-4" style="margin-top: -80px;">
  <div class="flex flex-col gap-4 w-full max-w-md transition-all duration-500 ease-in-out">
    <!-- Third Card (flies in from top) -->
    {#if showThirdCard}
      <div class="absolute top-24 left-1/2 transform -translate-x-1/2 w-1/2" transition:fly={{ y: -500, duration: 500, delay: 250 }}>
        <Card.Root class="w-full">
          <Card.Header>
            <Card.Title>Agent Chip Preview</Card.Title>
            <Card.Description>Preview of how your agent will appear</Card.Description>
          </Card.Header>
          <Card.Content>
            {#if agentCardError}
              <div class="flex flex-col items-center justify-center py-8 space-y-4">
                <div class="text-6xl">🤖</div>
                <div class="text-destructive text-center">
                  <div class="font-medium">Agent Card Error</div>
                  <div class="text-sm mt-1">{agentCardError}</div>
                </div>
              </div>
            {:else if agentCard}
              <div class="flex justify-center py-8">
                <AgentChip agent={{
                  identifier: agentCard.name || 'agent',
                  avatar_url: agentCard.avatar_url,
                  description: agentCard.description || 'No description available'
                }} agent_id="preview" isOnline={canRegister && launcherStatus === 'online'} />
              </div>
            {:else}
              <div class="flex flex-col items-center justify-center py-8 space-y-4">
                <div class="text-6xl">🤖</div>
                <div class="text-muted-foreground text-center">
                  <div class="font-medium">Agent Chip</div>
                  <div class="text-sm">Enter an agent URL to load the card</div>
                </div>
              </div>
            {/if}
          </Card.Content>
        </Card.Root>
      </div>
    {/if}
    
    <!-- Forms Row -->
    <div class="flex gap-4 relative" style="transform: translateY({formsPushedDown ? '60px' : '0px'}); transition: transform 500ms ease-in-out;">
      <!-- Original Form -->
      <div class="w-full" style="transform: translateX({originalFormMoved ? '-52%' : '0px'}); transition: transform 500ms ease-in-out;">
        <Card.Root class="w-full">
          <Card.Header>
            <Card.Title>Register Agent</Card.Title>
            <Card.Description>Register a new agent for battles</Card.Description>
          </Card.Header>
          <Card.Content>
            <form method="POST" use:enhance class="space-y-4">
              <Form.Field {form} name="agent_url">
                <Form.Control>
                  {#snippet children({ props })}
                    <Form.Label>Agent URL</Form.Label>
                    <div class="flex items-center gap-2">
                      <Input {...props} bind:value={$formData.agent_url} placeholder="URL at which your agent is hosted" onblur={handleAgentUrlBlur} class="flex-1" />
                      <div class="flex-shrink-0 w-6 h-6">
                        {#if $formData.agent_url?.trim()}
                          {#if isLoadingAgentCard}
                            <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                          {:else if canRegister}
                            <div class="w-4 h-4 bg-green-500 rounded-full" title="Agent URL is accessible"></div>
                          {:else}
                            <div class="w-4 h-4 bg-red-500 rounded-full" title="Agent URL is not accessible"></div>
                          {/if}
                        {:else}
                          <div class="w-4 h-4 bg-muted rounded-full" title="No URL entered"></div>
                        {/if}
                      </div>
                    </div>
                  {/snippet}
                </Form.Control>
                <Form.FieldErrors />
                {#if isLoadingAgentCard}
                  <div class="text-sm text-muted-foreground">
                    Loading agent card...
                  </div>
                {/if}
              </Form.Field>

              <!-- Hidden alias field that gets auto-filled -->
              <Form.Field {form} name="alias">
                <Form.Control>
                  {#snippet children({ props })}
                    <Input {...props} bind:value={$formData.alias} type="hidden" />
                  {/snippet}
                </Form.Control>
              </Form.Field>

              <!-- Hidden participant requirements field -->
              <Form.Field {form} name="participant_requirements">
                <Form.Control>
                  {#snippet children({ props })}
                    <Input {...props} value={JSON.stringify($formData.participant_requirements)} type="hidden" />
                  {/snippet}
                </Form.Control>
              </Form.Field>

              <!-- Hidden battle timeout field -->
              <Form.Field {form} name="battle_timeout">
                <Form.Control>
                  {#snippet children({ props })}
                    <Input {...props} bind:value={$formData.battle_timeout} type="hidden" />
                  {/snippet}
                </Form.Control>
              </Form.Field>

              <!-- Hidden task description field -->
              <Form.Field {form} name="task_config">
                <Form.Control>
                  {#snippet children({ props })}
                    <Input {...props} bind:value={$formData.task_config} type="hidden" />
                  {/snippet}
                </Form.Control>
              </Form.Field>

              <Form.Field {form} name="launcher_url">
                <Form.Control>
                  {#snippet children({ props })}
                    <Form.Label>Launcher URL</Form.Label>
                    <div class="flex items-center gap-2">
                      <Input {...props} bind:value={$formData.launcher_url} placeholder="URL at which your agent launcher is hosted" onblur={handleLauncherUrlBlur} class="flex-1" />
                      <div class="flex-shrink-0 w-6 h-6">
                        {#if $formData.launcher_url?.trim()}
                          {#if launcherStatus === 'checking'}
                            <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                          {:else if launcherStatus === 'online'}
                            <div class="w-4 h-4 bg-green-500 rounded-full" title="Launcher server is running"></div>
                          {:else if launcherStatus === 'offline'}
                            <div class="w-4 h-4 bg-red-500 rounded-full" title="Launcher server is not accessible"></div>
                          {:else}
                            <div class="w-4 h-4 bg-muted rounded-full" title="Status unknown"></div>
                          {/if}
                        {:else}
                          <div class="w-4 h-4 bg-muted rounded-full" title="No URL entered"></div>
                        {/if}
                      </div>
                    </div>
                  {/snippet}
                </Form.Control>
                <Form.FieldErrors />
              </Form.Field>

              <Form.Field {form} name="green">
                <Form.Control>
                  {#snippet children({ props })}
                    <div class="flex items-center space-x-2">
                      <Switch {...props} bind:checked={$formData.green} class="data-[state=checked]:bg-primary data-[state=unchecked]:bg-muted" />
                      <Label for="green">Green?</Label>
                    </div>
                  {/snippet}
                </Form.Control>
                <Form.FieldErrors />
              </Form.Field>

              <div class="flex gap-2 pt-4">
                <Button type="submit" class="flex-1 btn-primary" disabled={!canRegister}>Register Agent</Button>
                <Button type="button" class="flex-1 btn-primary" onclick={() => goto('/agents')}>Cancel</Button>
              </div>
            </form>
          </Card.Content>
        </Card.Root>
      </div>

      <!-- Green Agent Form (only shown when green is checked) -->
      {#if showGreenForm}
        <div class="absolute left-1/2 top-0 w-full ml-4" transition:fly={{ x: 300, duration: 500, delay: 250 }}>
          <Card.Root class="w-full transition-all duration-300 ease-in-out">
            <Card.Header>
              <Card.Title>Green Agent Setup</Card.Title>
              <Card.Description>
                {#if isAnalyzing}
                  Analyzing agent card and suggesting configuration...
                {:else}
                  Configure agent type and participant requirements
                {/if}
              </Card.Description>
            </Card.Header>
            <Card.Content>
              {#if isAnalyzing}
                <div class="flex items-center justify-center py-8">
                  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  <span class="ml-2 text-muted-foreground">Analyzing agent card...</span>
                </div>
              {:else}
                <div class="space-y-4">
                  {#if analysisError}
                    <div class="text-destructive text-sm p-2 bg-destructive/10 rounded">
                      AI Analysis Error: {analysisError}
                    </div>
                  {/if}
                  <div class="space-y-4">
                  <div class="pb-4">
                    <Label for="task_config" class="text-sm">Task Index</Label>
                    <textarea
                      id="task_config"
                      bind:value={$formData.task_config}
                      placeholder="Write a task index (starting from 0), if applicable. e.g. Task index = 0. "
                      rows="3"
                      class="border-input bg-background selection:bg-primary dark:bg-input/30 selection:text-primary-foreground ring-offset-background placeholder:text-muted-foreground shadow-xs flex w-full min-w-0 rounded-md border px-3 py-2 text-base outline-none transition-[color,box-shadow] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[2px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive mt-1 resize-vertical"
                    ></textarea>
                  </div>
                  <div class="border-t pt-4">
                    <div class="flex items-center gap-2 mb-2">
                      <h4 class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Participant Requirements</h4>
                      <Button
                        type="button"
                        onclick={addParticipantRequirement}
                        class="h-6 w-6 p-0 btn-primary rounded"
                      >
                        +
                      </Button>
                    </div>
                    
                    <div class="space-y-2">
                      {#each $formData.participant_requirements as requirement, index (requirement.id || index)}
                        <div class="flex items-center gap-2 p-2 border rounded" 
                             in:fly={{ y: 20, duration: 300, delay: index * 50 }}
                             out:fly={{ y: -20, duration: 200 }}>
                          <Input
                            placeholder="Role"
                            bind:value={requirement.role}
                            class="w-24 text-sm"
                          />
                          <Input
                            placeholder="Name"
                            bind:value={requirement.name}
                            class="w-32 text-sm"
                          />
                          <div class="flex items-center gap-1">
                            <Switch bind:checked={requirement.required} class="data-[state=checked]:bg-primary data-[state=unchecked]:bg-muted" />
                            <Label class="text-xs">Required</Label>
                          </div>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onclick={() => removeParticipantRequirement(index)}
                            class="h-6 w-6 p-0 ml-auto"
                          >
                            ×
                          </Button>
                        </div>
                      {/each}
                    </div>
                  </div>
                  <div class="border-t pt-4">
                    <div>
                      <Label for="battle_timeout" class="text-sm">Battle Timeout (seconds)</Label>
                      <Input
                        id="battle_timeout"
                        type="number"
                        bind:value={$formData.battle_timeout}
                        min="1"
                        class="mt-1"
                      />
                    </div>
                  </div>
                  </div>
                </div>
              {/if}
            </Card.Content>
          </Card.Root>
        </div>
      {/if}
    </div>
  </div>

</div>
