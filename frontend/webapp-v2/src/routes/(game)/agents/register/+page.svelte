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
  import { fetchAgentCard } from "$lib/api/agents";
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
  
  async function loadAgentCard() {
    if (!$formData.agent_url?.trim()) {
      agentCard = null;
      agentCardError = null;
      showThirdCard = false;
      return;
    }

    try {
      isLoadingAgentCard = true;
      agentCardError = null;
      agentCard = await fetchAgentCard($formData.agent_url);
      
      // Delay showing the card to let forms move down first
      setTimeout(() => {
        showThirdCard = true;
      }, 250);

      // Auto-fill alias from agent card
      if (agentCard?.name) {
        console.log('Setting alias to:', agentCard.name);
        $formData.alias = agentCard.name;
      }
    } catch (err) {
      agentCardError = err instanceof Error ? err.message : "Failed to load agent card";
      agentCard = null;
      showThirdCard = false;
    } finally {
      isLoadingAgentCard = false;
    }
  }

  function handleAgentUrlBlur() {
    loadAgentCard();
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
                }} agent_id="preview" />
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
                    <Input {...props} bind:value={$formData.agent_url} placeholder="URL at which your agent is hosted" onblur={handleAgentUrlBlur} />
                  {/snippet}
                </Form.Control>
                <Form.FieldErrors />
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

              <Form.Field {form} name="launcher_url">
                <Form.Control>
                  {#snippet children({ props })}
                    <Form.Label>Launcher URL</Form.Label>
                    <Input {...props} bind:value={$formData.launcher_url} placeholder="URL at which your agent launcher is hosted" />
                  {/snippet}
                </Form.Control>
                <Form.FieldErrors />
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
                <Button type="submit" class="flex-1 btn-primary">Register Agent</Button>
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
            </Card.Header>
            <Card.Content>
              <div class="space-y-4">
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
                </div>
              </div>
            </Card.Content>
          </Card.Root>
        </div>
      {/if}
    </div>
  </div>

</div>
