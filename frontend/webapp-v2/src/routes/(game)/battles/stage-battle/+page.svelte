<script lang="ts">
  import type { PageData } from "./$types.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import CustomDropdown from "$lib/components/custom-dropdown.svelte";
  import RecommendedAgentsDropdown from "$lib/components/recommended-agents-dropdown.svelte";
  import { fly } from 'svelte/transition';
  import { goto } from "$app/navigation";
  import { toast } from 'svelte-sonner';
  import { onMount, onDestroy } from 'svelte';
  import { supabase } from '$lib/auth/supabase';
  import { getAllAgentsWithAsyncLiveness } from '$lib/api/agents';

  onMount(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    onDestroy(() => {
      document.body.style.overflow = prev;
    });
  });

  let { data } = $props();

  // Form data state
  let formData = $state({
    green_agent_id: '',
    battle_timeout: 300
  });
  
  // Track if we're in transition to prevent squishing
  let showParticipantForm = $state(false);
  let originalFormMoved = $state(false);
  
  // Agents data
  let agents = $state<any[]>([]);
  let greenAgents = $state<any[]>([]);
  let opponentAgents = $state<any[]>([]);
  let agentsLoading = $state(true);
  let agentsError = $state<string | null>(null);
  
  // Participant requirements and role assignments
  let participantRequirements = $state<any[]>([]);
  let roleAssignments = $state<Record<string, string>>({});
  
  // Load agents on mount
  onMount(() => {
    loadAgents();
  });
  
  $effect(() => {
    if (formData.green_agent_id && !showParticipantForm) {
      // Show participant form: move original first, then show participant
      originalFormMoved = true;
      setTimeout(() => {
        showParticipantForm = true;
      }, 250);
    } else if (!formData.green_agent_id && showParticipantForm) {
      // Hide participant form: hide participant first, then move original back
      showParticipantForm = false;
      setTimeout(() => {
        originalFormMoved = false;
      }, 250);
    }
  });

  // Update participant requirements when green agent changes
  $effect(() => {
    console.log('Green agent changed:', formData.green_agent_id);
    console.log('Available green agents:', greenAgents);
    
    if (formData.green_agent_id) {
      const green = greenAgents.find((a: any) => a.agent_id === formData.green_agent_id);
      participantRequirements = green?.register_info?.participant_requirements || [];
      console.log('Participant requirements:', participantRequirements);
      
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
  });

  async function loadAgents() {
    try {
      agentsLoading = true;
      agentsError = null;
      
      // Use layered loading for better performance
      const rawAgents = await getAllAgentsWithAsyncLiveness((updatedAgents) => {
        // This callback will be called when liveness data is ready
        console.log('Stage battle agents liveness updated:', updatedAgents);
        updateAgentsData(updatedAgents);
      });
      
      console.log('Stage battle loaded basic agent info:', rawAgents);
      updateAgentsData(rawAgents);
      
    } catch (error) {
      console.error('Error loading agents:', error);
      agentsError = error instanceof Error ? error.message : 'Failed to load agents';
    } finally {
      agentsLoading = false;
    }
  }
  
  function updateAgentsData(rawAgents: any[]) {
    // Transform the data to match expected format
    agents = rawAgents.map((agent: any) => ({
      agent_id: agent.agent_id || agent.id,
      name: agent.register_info?.alias || agent.agent_card?.name || 'Unnamed Agent',
      register_info: agent.register_info || {},
      status: agent.status || 'unlocked',
      agent_card: agent.agent_card || {},
      live: agent.live || false,
      livenessLoading: agent.livenessLoading || false
    }));
    
    // Filter agents by type
    greenAgents = agents.filter((agent: any) => agent.register_info.is_green);
    opponentAgents = agents.filter((agent: any) => !agent.register_info.is_green);
    
    console.log('Updated agents data:', { agents, greenAgents, opponentAgents });
  }

  function handleRoleAssign(roleName: string, agentId: string) {
    // Prevent assigning the same agent to multiple roles
    for (const [key, value] of Object.entries(roleAssignments)) {
      if (value === agentId && key !== roleName) {
        roleAssignments[key] = '';
      }
    }
    roleAssignments[roleName] = agentId;
  }

  function validateRequiredRoles() {
    return participantRequirements.every(req => 
      !req.required || roleAssignments[req.name]
    );
  }

  async function handleSubmit(event: Event) {
    event.preventDefault();
    
    if (!formData.green_agent_id) {
      toast.error('Please select a green agent');
      return;
    }

    if (participantRequirements.length === 0) {
      toast.error('This green agent has no required roles');
      return;
    }

    if (!validateRequiredRoles()) {
      toast.error('Please assign all required roles');
      return;
    }

    // Build opponents array with { name, agent_id } using roleAssignments
    const opponents = participantRequirements
      .filter(req => roleAssignments[req.name])
      .map(req => ({ name: req.name, agent_id: roleAssignments[req.name] }));

    console.log('Sending battle request to backend:', {
      green_agent_id: formData.green_agent_id,
      opponents
    });

    try {
      const { data: { session } } = await supabase.auth.getSession();
      const accessToken = session?.access_token;

      const response = await fetch('/api/battles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          green_agent_id: formData.green_agent_id,
          opponents,
          created_by: session?.user?.email || 'Unknown User'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start battle');
      }

      const result = await response.json();
      
      toast.success('Battle started successfully!', {
        position: 'top-center'
      });
      
      // Redirect to the specific battle page
      setTimeout(() => {
        goto(`/battles/${result.battle_id}`);
      }, 1500);
      
    } catch (error) {
      console.error('Error starting battle:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to start battle', {
        position: 'top-center'
      });
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center p-4" style="margin-top: -180px;">
  <div class="flex flex-col gap-4 w-full max-w-md transition-all duration-500 ease-in-out">
    <!-- Forms Row -->
    <div class="flex gap-4 relative">
      <!-- Main Form -->
      <div class="w-full" style="transform: translateX({originalFormMoved ? '-52%' : '0px'}); transition: transform 500ms ease-in-out;">
        <Card.Root class="w-full">
          <Card.Header>
            <Card.Title>Stage Battle</Card.Title>
            <Card.Description>Select a green agent to orchestrate the battle</Card.Description>
          </Card.Header>
          <Card.Content>
            {#if agentsLoading}
              <div class="text-center py-8">
                <div class="text-muted-foreground">Loading agents...</div>
              </div>
            {:else if agentsError}
              <div class="text-center py-8">
                <div class="text-red-500">Error: {agentsError}</div>
                <Button onclick={loadAgents} class="mt-2">Retry</Button>
              </div>
            {:else}
              <div class="space-y-4">
                <div>
                  <CustomDropdown
                    label="Green Agent (Orchestrator)"
                    value={formData.green_agent_id}
                    placeholder="Select a green agent"
                    options={[
                      { value: '', label: 'Select a green agent' },
                      ...greenAgents.map((agent: any) => ({
                        value: agent.agent_id,
                        label: agent.register_info?.alias || agent.agent_card?.name || 'Unknown Agent',
                        agent: agent
                      }))
                    ]}
                    on:change={(e) => formData.green_agent_id = e.detail.value}
                  />
                </div>
                
                {#if greenAgents.length === 0}
                  <div class="text-center py-6 text-muted-foreground">
                    <div class="text-sm">No green agents available</div>
                    <div class="text-xs mt-1">Register a green agent first</div>
                  </div>
                {/if}
              </div>
            {/if}
          </Card.Content>
        </Card.Root>
      </div>

      <!-- Participant Agents Form (only shown when green agent is selected) -->
      {#if showParticipantForm}
        <div class="absolute left-1/2 top-0 w-full ml-4" transition:fly={{ x: 300, duration: 500, delay: 250 }}>
          <Card.Root class="w-full transition-all duration-300 ease-in-out">
            <Card.Header>
              <Card.Title>Select Participants</Card.Title>
            </Card.Header>
            <Card.Content>
              <form onsubmit={handleSubmit} class="space-y-4">
                {#if participantRequirements.length === 0}
                  <div class="text-center py-6 text-muted-foreground">
                    <div class="text-sm">No participant requirements defined</div>
                    <div class="text-xs mt-1">This green agent has no required roles</div>
                  </div>
                {:else}
                  {#each participantRequirements as req}
                    <div class="space-y-2">
                      <RecommendedAgentsDropdown
                        label={`${req.name} ${req.required ? '(Required)' : '(Optional)'}`}
                        greenAgentId={formData.green_agent_id}
                        roleName={req.name}
                        value={roleAssignments[req.name]}
                        placeholder="Select an agent"
                        allAgents={opponentAgents}
                        assignedAgents={Object.values(roleAssignments).filter(id => id && id !== roleAssignments[req.name])}
                        on:change={(e) => handleRoleAssign(req.name, e.detail.value)}
                      />
                    </div>
                  {/each}
                {/if}

                {#if opponentAgents.length === 0}
                  <div class="text-center py-6 text-muted-foreground">
                    <div class="text-sm">No opponent agents available</div>
                    <div class="text-xs mt-1">Register opponent agents first</div>
                  </div>
                {/if}

                <div class="flex gap-2 pt-4">
                  <Button 
                    type="submit" 
                    class="flex-1 btn-primary"
                    disabled={!validateRequiredRoles()}
                  >
                    Start Battle
                  </Button>
                  <Button 
                    type="button"
                    class="flex-1 btn-primary"
                    onclick={() => goto('/battles')}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </Card.Content>
          </Card.Root>
        </div>
      {/if}
    </div>
  </div>
</div>
