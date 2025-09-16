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
  import { useAgents } from "$lib/hooks";
  import { agentsService } from "$lib/services/agents.service.js";
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
    dataType: "json"
  });

  const { form: formData } = form;
  
  // Use the new useAgents hook
  const agentsHook = useAgents();
  
  // Registration state
  let isRegistering = $state(false);
  
  // Track if we're in transition to prevent squishing
  let showGreenForm = $state(false);
  let showThirdCard = $state(false); // Controls third card visibility
  let originalFormMoved = $state(false); // Controls original form position
  let formsPushedDown = $state(false); // Controls forms moving down for agent card
  
  // Agent card preview state
  let isLoadingAgentCard = $state(false);
  let agentCardError = $state<string | null>(null);
  let agentCard = $state<any>(null);
  let suggestedAlias = $state('');
  
  // Analysis state
  let isAnalyzing = $state(false);
  let analysisError = $state<string | null>(null);
  
  // Status indicators for URLs
  let canRegister = $state(true);
  let isCheckingLauncher = $state(false);
  let launcherStatus = $state<'unknown' | 'checking' | 'online' | 'offline'>('unknown');
  
  // Agent type state
  let agentType = $state<'remote' | 'hosted'>('remote');
  
  // Debug panel state
  let showDebugPanel = $state(false);
  
  $effect(() => {
    // Update form data when agent type changes
    $formData.is_hosted = agentType === 'hosted';
    
    // Reset fields when switching types
    if (agentType === 'hosted') {
      $formData.agent_url = '';
      $formData.launcher_url = '';
      agentCard = null;
      showThirdCard = false;
      launcherStatus = 'unknown';
    } else {
      $formData.docker_image_link = '';
    }
  });
  
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
      const result = await agentsService.checkLauncherStatus($formData.launcher_url);
      if (result.data){
        launcherStatus = result.data.online ? 'online' : 'offline';
      } else {
        launcherStatus = 'offline';
        console.error("Unexpected response format:", result);
        toast.error("Unexpected response format from launcher status check");
      }
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
      const res = await agentsService.fetchAgentCard($formData.agent_url);
      if (res.success) {
        agentCard = res.data;
      } else {
        throw new Error(res.error || "Failed to load agent card");
      }
      canRegister = true;
      
      // Delay showing the card to let forms move down first
      setTimeout(() => {
        showThirdCard = true;
      }, 250);

      // Set suggested alias from agent card name (don't auto-fill)
      if (agentCard?.name) {
        console.log('Setting suggested alias to:', agentCard.name);
        suggestedAlias = agentCard.name;
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

      const res = await agentsService.analyzeAgentCard(agentCard);
      if (!res.success || !res.data) {
        throw new Error(res.error || "Failed to analyze agent card");
      }
      const analysis = res.data;

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

  async function handleRegisterAgent() {
    // Validate form first
    const validation = formSchema.safeParse($formData);
    if (!validation.success) {
      toast.error('Please fill in all required fields correctly.', {
        position: 'top-center'
      });
      return;
    }

    try {
      isRegistering = true;
      
      // Prepare the registration data
      const registerData = {
        alias: $formData.alias,
        is_green: $formData.green,
        is_hosted: $formData.is_hosted,
        battle_description: $formData.battle_description || '',
        participant_requirements: $formData.participant_requirements,
        battle_timeout: $formData.battle_timeout,
        ...(agentType === 'hosted' 
          ? { docker_image_link: $formData.docker_image_link }
          : { 
              agent_url: $formData.agent_url,
              launcher_url: $formData.launcher_url 
            }
        )
      };

      console.log('Registering agent with data:', registerData);

      // Use the agentsHook to register the agent
      const result = await agentsHook.registerAgent(registerData);
      
      console.log('Agent registered successfully:', result);
      
      toast.success('Agent registered successfully!', {
        position: 'top-center'
      });
      
      // Redirect to agents page after successful registration
      setTimeout(() => {
        goto('/agents');
      }, 1500);
      
    } catch (error) {
      console.error('Failed to register agent:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to register agent. Please try again.';
      toast.error(errorMessage, {
        position: 'top-center'
      });
    } finally {
      isRegistering = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center p-4" style="margin-top: -80px;">
  <div class="flex gap-6 w-full max-w-4xl transition-all duration-500 ease-in-out">
    
    <!-- Vertical Agent Type Tabs (Left Side) -->
    <div class="flex flex-col gap-2 pt-20 transition-transform duration-650 ease-in-out" style="transform: translateX({originalFormMoved ? '-250px' : '0px'});">
      <button
        onclick={() => agentType = 'remote'}
        class="flex items-center justify-center p-3 w-16 h-12 rounded-lg border transition-all duration-200 {agentType === 'remote' ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'}"
        title="Remote Agent"
      >
        <div class="text-center">
          <div class="text-xs font-medium">Remote</div>
        </div>
      </button>
      
      <button
        onclick={() => agentType = 'hosted'}
        class="flex items-center justify-center p-3 w-16 h-12 rounded-lg border transition-all duration-200 {agentType === 'hosted' ? 'bg-green-500 text-white border-green-500' : 'bg-white text-gray-600 border-gray-200 hover:border-green-300'}"
        title="Hosted Agent"
      >
        <div class="text-center">
          <div class="text-xs font-medium">Hosted</div>
        </div>
      </button>
    </div>
    
    <!-- Main Content Area -->
    <div class="flex flex-col gap-4 flex-1 max-w-md transition-all duration-500 ease-in-out">
    <!-- Third Card (flies in from top) - Only for Remote Agents -->
    {#if showThirdCard && agentType === 'remote'}
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
    <div class="flex gap-4 relative justify-center" style="transform: translateY({formsPushedDown ? '60px' : '0px'}); transition: transform 500ms ease-in-out;">
      <!-- Original Form -->
      <div class="w-full max-w-md" style="transform: translateX({originalFormMoved ? '-250px' : '0px'}); transition: transform 500ms ease-in-out;">
        <Card.Root class="w-full">
          <Card.Header>
            <Card.Title>Register Agent</Card.Title>
            <Card.Description>Register a new agent for battles</Card.Description>
          </Card.Header>
          <Card.Content>
            <form class="space-y-4" onsubmit={(e) => { e.preventDefault(); handleRegisterAgent(); }}>
              
              <!-- Dynamic Agent Type Fields -->
              {#if agentType === 'remote'}
                <!-- Remote Agent Fields -->
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
                            <div class="w-4 h-4 bg-gray-300 rounded-full" title="No URL entered"></div>
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
                              <div class="w-4 h-4 bg-gray-300 rounded-full" title="Status unknown"></div>
                            {/if}
                          {:else}
                            <div class="w-4 h-4 bg-gray-300 rounded-full" title="No URL entered"></div>
                          {/if}
                        </div>
                      </div>
                    {/snippet}
                  </Form.Control>
                  <Form.FieldErrors />
                </Form.Field>
              {:else}
                <!-- Hosted Agent Fields -->
                <Form.Field {form} name="docker_image_link">
                  <Form.Control>
                    {#snippet children({ props })}
                      <Form.Label>Docker Image Link</Form.Label>
                      <Input {...props} bind:value={$formData.docker_image_link} placeholder="https://agent-docker-image-link" />
                    {/snippet}
                  </Form.Control>
                  <Form.FieldErrors />
                  <div class="text-sm text-muted-foreground">
                    Provide a Docker image link for your hosted agent.
                  </div>
                </Form.Field>
              {/if}

              <!-- Common Fields
              <Form.Field {form} name="alias">
                <Form.Control>
                  {#snippet children({ props })}
                    <Form.Label>Agent Alias</Form.Label>
                    <Input {...props} bind:value={$formData.alias} placeholder="My Awesome Agent" />
                  {/snippet}
                </Form.Control>
                <Form.FieldErrors />
              </Form.Field>

              <Form.Field {form} name="battle_description">
                <Form.Control>
                  {#snippet children({ props })}
                    <Form.Label>Battle Description (optional)</Form.Label>
                    <Input {...props} bind:value={$formData.battle_description} placeholder="Describe what makes your agent special for battles..." />
                  {/snippet}
                </Form.Control>
                <Form.FieldErrors />
              </Form.Field> -->

              <!-- Hidden fields -->
              <Form.Field {form} name="is_hosted">
                <Form.Control>
                  {#snippet children({ props })}
                    <Input {...props} bind:value={$formData.is_hosted} type="hidden" />
                  {/snippet}
                </Form.Control>
              </Form.Field>

              <Form.Field {form} name="participant_requirements">
                <Form.Control>
                  {#snippet children({ props })}
                    <Input {...props} value={JSON.stringify($formData.participant_requirements)} type="hidden" />
                  {/snippet}
                </Form.Control>
              </Form.Field>

              <Form.Field {form} name="battle_timeout">
                <Form.Control>
                  {#snippet children({ props })}
                    <Input {...props} bind:value={$formData.battle_timeout} type="hidden" />
                  {/snippet}
                </Form.Control>
              </Form.Field>

              <!-- Agent Alias Field - Always shown at bottom -->
              <Form.Field {form} name="alias">
                <Form.Control>
                  {#snippet children({ props })}
                    <Form.Label>Agent Alias</Form.Label>
                    <Input 
                      {...props} 
                      bind:value={$formData.alias} 
                      placeholder={suggestedAlias || "My Awesome Agent"} 
                    />
                  {/snippet}
                </Form.Control>
                <Form.FieldErrors />
                {#if suggestedAlias && suggestedAlias !== $formData.alias}
                  <div class="text-sm text-muted-foreground">
                    Suggested from agent card: {suggestedAlias}
                  </div>
                {/if}
              </Form.Field>

              <Form.Field {form} name="green">
                <Form.Control>
                  {#snippet children({ props })}
                    <div class="flex items-center space-x-2">
                      <Switch {...props} bind:checked={$formData.green} class="data-[state=checked]:bg-gray-900 data-[state=unchecked]:bg-gray-200" />
                      <Label for="green">Green?</Label>
                    </div>
                  {/snippet}
                </Form.Control>
                <Form.FieldErrors />
              </Form.Field>

              <div class="flex gap-2 pt-4">
                <Button 
                  type="submit" 
                  class="flex-1 btn-primary" 
                  disabled={!canRegister || isRegistering}
                >
                  {#if isRegistering}
                    <div class="flex items-center gap-2">
                      <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Registering...
                    </div>
                  {:else}
                    Register Agent
                  {/if}
                </Button>
                <Button type="button" class="flex-1 btn-primary" onclick={() => goto('/agents')}>Cancel</Button>
              </div>
            </form>
          </Card.Content>
        </Card.Root>
      </div>

      <!-- Green Agent Form (only shown when green is checked) -->
      {#if showGreenForm}
        <div class="absolute left-1/2 top-0 w-full max-w-md ml-4" transition:fly={{ x: 300, duration: 500, delay: 250 }}>
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
                            <Switch bind:checked={requirement.required} class="data-[state=checked]:bg-gray-900 data-[state=unchecked]:bg-gray-200" />
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
                  <div class="border-t pt-4">
                    <div>
                      <Label for="battle_description" class="text-sm">Battle Description</Label>
                      <Input
                        id="battle_description"
                        type="text"
                        bind:value={$formData.battle_description}
                        placeholder="Configure the battle here..."
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
  
  <!-- Debug Panel -->
  <div class="fixed bottom-0 left-0 right-0 z-50 transition-all duration-300 ease-in-out {showDebugPanel ? 'translate-y-0' : 'translate-y-full'}">
    <div class="bg-gray-900 text-white border-t border-gray-700 max-h-96 overflow-y-auto">
      <div class="p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-lg font-semibold">Debug - Form Data</h3>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onclick={() => showDebugPanel = false}
            class="text-white hover:bg-gray-800"
          >
            ×
          </Button>
        </div>
        <div class="space-y-2 text-sm font-mono">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div class="text-yellow-400 font-bold mb-2">Form Fields:</div>
              <div class="space-y-1">
                <div><span class="text-blue-400">agent_url:</span> <span class="text-green-400">"{$formData.agent_url || ''}"</span></div>
                <div><span class="text-blue-400">launcher_url:</span> <span class="text-green-400">"{$formData.launcher_url || ''}"</span></div>
                <div><span class="text-blue-400">docker_image_link:</span> <span class="text-green-400">"{$formData.docker_image_link || ''}"</span></div>
                <div><span class="text-blue-400">alias:</span> <span class="text-green-400">"{$formData.alias || ''}"</span></div>
                <div><span class="text-blue-400">battle_description:</span> <span class="text-green-400">"{$formData.battle_description || ''}"</span></div>
                <div><span class="text-blue-400">is_hosted:</span> <span class="text-orange-400">{$formData.is_hosted}</span></div>
                <div><span class="text-blue-400">green:</span> <span class="text-orange-400">{$formData.green}</span></div>
                <div><span class="text-blue-400">battle_timeout:</span> <span class="text-orange-400">{$formData.battle_timeout}</span></div>
              </div>
            </div>
            <div>
              <div class="text-yellow-400 font-bold mb-2">State Variables:</div>
              <div class="space-y-1">
                <div><span class="text-blue-400">agentType:</span> <span class="text-green-400">"{agentType}"</span></div>
                <div><span class="text-blue-400">showGreenForm:</span> <span class="text-orange-400">{showGreenForm}</span></div>
                <div><span class="text-blue-400">showThirdCard:</span> <span class="text-orange-400">{showThirdCard}</span></div>
                <div><span class="text-blue-400">canRegister:</span> <span class="text-orange-400">{canRegister}</span></div>
                <div><span class="text-blue-400">launcherStatus:</span> <span class="text-green-400">"{launcherStatus}"</span></div>
                <div><span class="text-blue-400">isLoadingAgentCard:</span> <span class="text-orange-400">{isLoadingAgentCard}</span></div>
                <div><span class="text-blue-400">isAnalyzing:</span> <span class="text-orange-400">{isAnalyzing}</span></div>
                <div><span class="text-blue-400">isRegistering:</span> <span class="text-orange-400">{isRegistering}</span></div>
              </div>
            </div>
          </div>
          {#if $formData.participant_requirements.length > 0}
            <div class="mt-4">
              <div class="text-yellow-400 font-bold mb-2">Participant Requirements:</div>
              <pre class="text-green-400 text-xs overflow-x-auto">{JSON.stringify($formData.participant_requirements, null, 2)}</pre>
            </div>
          {/if}
          {#if agentCard}
            <div class="mt-4">
              <div class="text-yellow-400 font-bold mb-2">Agent Card:</div>
              <pre class="text-green-400 text-xs overflow-x-auto max-h-32 overflow-y-auto">{JSON.stringify(agentCard, null, 2)}</pre>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
  
  <!-- Debug Toggle Button -->
  <button
    onclick={() => showDebugPanel = !showDebugPanel}
    class="fixed bottom-4 right-4 bg-gray-900 text-white px-3 py-2 rounded-full shadow-lg hover:bg-gray-800 transition-colors duration-200 z-40 text-sm font-mono"
    title="Toggle Debug Panel"
  >
    {showDebugPanel ? 'Hide Debug' : 'Show Debug'}
  </button>
</div>
