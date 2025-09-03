<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { marked } from 'marked';
  import { userEmail } from '$lib/stores/auth';
  import AgentChip from "$lib/components/agent-chip.svelte";
  import * as Card from "$lib/components/ui/card";
  import { SvelteFlow, Background, Controls, MiniMap, Handle, Position } from '@xyflow/svelte';
  import '@xyflow/svelte/dist/style.css';
  import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
  import ChevronUpIcon from "@lucide/svelte/icons/chevron-up";
  import DownloadIcon from "@lucide/svelte/icons/download";
  import AgentNode from "$lib/components/agent-node.svelte";
  import LogEdge from "$lib/components/log-edge.svelte";
  import * as Carousel from "$lib/components/ui/carousel";
  import Autoplay from "embla-carousel-autoplay";
  import AsciinemaPlayerView from '$lib/components/AsciinemaPlayerView.svelte';
  
  // Node and edge types for Svelte Flow
  const nodeTypes = {
    agentNode: AgentNode
  };
  
  let interactHistoryContainer: HTMLDivElement | null = null;
  let isDevMode = false;
  let entryActiveTabs: Record<number, string> = {};

  async function fetchWithTimeout(input: RequestInfo, init?: RequestInit, timeoutMs: number = 15000): Promise<Response> {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(input, { ...(init || {}), signal: controller.signal });
      return res;
    } finally {
      clearTimeout(id);
    }
  }
  
  const edgeTypes = {
    logEdge: LogEdge
  };
  
  let battle = $state<any>(null);
  let loading = $state(true);
  let error = $state('');
  let greenAgentName = $state('');
  let opponentNames = $state<string[]>([]);
  let ws = $state<WebSocket | null>(null);
  let greenAgentInfo = $state<any>(null);
  let opponentAgentsInfo = $state<any[]>([]); // Store full opponent agent data
  let opponentRoleMap = $state(new Map<string, string>()); // name -> role mapping
  let agentDataMap = $state(new Map<string, any>()); // Map agent_id to full agent data
  let expandedLogs = $state(new Set<string>()); // track which log sections are expanded
  let openLogs = $state<Set<string>>(new Set()); // track which logs are open
  let openAgents = $state<Set<string>>(new Set()); // track which agents are open
  let closingAgents = $state<Set<string>>(new Set()); // track which agents are closing
  let closingLogs = $state<Set<string>>(new Set()); // track which logs are closing
  let currentAgentData = $state<any[]>([]);
  
  // Svelte Flow state
  let nodes = $state<any[]>([]);
  let edges = $state<any[]>([]);
  let selectedLogNode = $state<string | null>(null);
  let selectedLogEdge = $state<string | null>(null);
  let openLogSections = $state<Set<string>>(new Set());
  let closingLogSections = $state<Set<string>>(new Set());
  
  let battleInProgress = $derived(battle ? isBattleInProgress() : false);
  
  // Check if current user can cancel the battle
  let canCancelBattle = $derived(battleInProgress && (
    isDevMode || 
    (battle?.created_by && $userEmail && battle.created_by === $userEmail)
  ));
  
  function getChronologicalAgentGroups() {
    if (!battle?.interact_history) return [];
    
    const groups: any[] = [];
    let currentAgent = null;
    let currentGroup = null;
    
    for (const [index, entry] of battle.interact_history.entries()) {
      if (entry.reported_by !== currentAgent) {
        // New agent - push previous group and start new one
        if (currentGroup) {
          groups.push(currentGroup);
        }
        currentAgent = entry.reported_by;
        currentGroup = {
          agent: currentAgent,
          entries: [{ ...entry, logNumber: index + 1 }],
          groupId: `group-${groups.length}`
        };
      } else {
        // Same agent - add to current group
        currentGroup?.entries.push({ ...entry, logNumber: index + 1 });
      }
    }
    
    // Don't forget the last group
    if (currentGroup) {
      groups.push(currentGroup);
    }
    
    return groups;
  }

  // Create Svelte Flow nodes and edges from battle data
  function createSvelteFlowData() {
    if (!battle) return;
    
    console.log('Creating Svelte Flow data with agentDataMap size:', agentDataMap.size);
    console.log('Available agent IDs:', Array.from(agentDataMap.keys()));
    
    const newNodes: any[] = [];
    const newEdges: any[] = [];
    
    // Add green agent node
    if (battle.green_agent_id) {
      const greenAgentData = getAgentChipData(battle.green_agent_id);
      console.log('Green agent data:', greenAgentData);
      
      newNodes.push({
        id: battle.green_agent_id,
        type: 'agentNode',
        position: { x: 400, y: 150 },
        data: {
          agent: greenAgentData,
          agent_id: battle.green_agent_id
        },
        style: {
          background: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '12px',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          width: 200,
          height: 80,
          padding: '12px'
        }
      });
    }
    
    // Add opponent nodes
    if (battle.opponents) {
      battle.opponents.forEach((opponent: any, i: number) => {
        if (opponent.agent_id) {
          const opponentAgentData = getAgentChipData(opponent.agent_id);
          console.log(`Opponent ${i} (${opponent.agent_id}) data:`, opponentAgentData);
          
          const opponentsPerRow = 3;
          const row = Math.floor(i / opponentsPerRow);
          const col = i % opponentsPerRow;
          const rowStartX = 400 - ((Math.min(opponentsPerRow, battle.opponents.length - (row * opponentsPerRow)) - 1) * 220) / 2;
          
          newNodes.push({
            id: opponent.agent_id,
            type: 'agentNode',
            position: { 
              x: rowStartX + (col * 220), 
              y: 350 + (row * 200) 
            },
            data: {
              agent: opponentAgentData,
              agent_id: opponent.agent_id
            },
            style: {
              background: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '12px',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
              width: 200,
              height: 80,
              padding: '12px'
            }
          });
        }
      });
    }

    nodes = newNodes;
    edges = newEdges;
  }



  // Create Svelte Flow data when battle data is available
  $effect(() => {
    if (battle && greenAgentName && opponentNames.length > 0) {
      createSvelteFlowData();
    }
  });

  // Recreate Svelte Flow data when agent data map changes
  $effect(() => {
    if (battle && agentDataMap.size > 0) {
      createSvelteFlowData();
    }
  });

  // Clear selected log when agent changes
  $effect(() => {
    if (openAgents.size > 0) {
      openLogs = new Set();
    }
  });

  async function fetchAgentName(agentId: string): Promise<string> {
    try {
      const res = await fetch(`/api/agents/${agentId}`);
      if (!res.ok) return agentId;
      const agent = await res.json();
      // Store the full agent data
      agentDataMap.set(agentId, agent);
      return agent.register_info?.name || agent.registerInfo?.name || agent.agent_card?.name || agent.agentCard?.name || agentId;
    } catch {
      return agentId;
    }
  }
  
  async function fetchGreenAgentInfo(agentId: string): Promise<any> {
    try {
      const res = await fetch(`/api/agents/${agentId}`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }
  
  function buildOpponentRoleMap(greenAgentInfo: any, battleOpponents: any[]): Map<string, string> {
    const roleMap = new Map<string, string>();
    
    if (!greenAgentInfo.register_info?.participant_requirements || !Array.isArray(battleOpponents)) {
      return roleMap;
    }
    
    const participantReqs = greenAgentInfo.register_info.participant_requirements;
    
    for (const opponent of battleOpponents) {
      const matchedReq = participantReqs.find((req: any) => req.name === opponent.name);
      if (matchedReq && matchedReq.role) {
        roleMap.set(opponent.name, matchedReq.role);
      }
    }
    
    // in case reported_by is simplified
    for (const req of participantReqs) {
      if (req.name && req.role) {
        roleMap.set(req.name, req.role);
        const simpleName = req.name.split(' (')[0].trim();
        if (simpleName !== req.name) {
          roleMap.set(simpleName, req.role);
        }
      }
    }
    
    return roleMap;
  }

  function getAgentBackgroundClass(agentName: string): string {
    const lowerAgentName = agentName.toLowerCase();
    if (agentName === 'system') {
      return 'bg-muted border-border';
    } else if (lowerAgentName.includes('blue')) {
      return 'bg-blue-50 border-blue-200';
    } else if (lowerAgentName.includes('red')) {
      return 'bg-red-50 border-red-200';
    } else if (agentName === 'green_agent' || lowerAgentName.includes('green')) {
      return 'bg-green-50 border-green-200';
    } else if (opponentRoleMap.has(agentName)) {
      const role = opponentRoleMap.get(agentName);
      if (role === 'blue_agent') {
        return 'bg-blue-50 border-blue-200';
      } else if (role === 'red_agent') {
        return 'bg-red-50 border-red-200';
      }
    }
    // Default background for unknown agent
    return 'bg-yellow-50 border-yellow-200';
  }

  function getAgentIdFromReportedBy(reportedBy: string): string {
    // Check if it's already an agent ID (exists in our agentDataMap)
    if (agentDataMap.has(reportedBy)) {
      return reportedBy;
    }
    
    // Map common reported_by names to actual agent IDs
    if (reportedBy === 'green_agent' || reportedBy.toLowerCase().includes('green')) {
      return battle?.green_agent_id || reportedBy;
    }
    
    // Check if any opponent matches this reported_by name
    if (battle?.opponents) {
      for (const opponent of battle.opponents) {
        if (opponent.name === reportedBy || opponent.agent_id === reportedBy) {
          return opponent.agent_id;
        }
      }
    }
    
    // Return as-is if no mapping found
    return reportedBy;
  }

  function createLogEdge(sourceAgentId: string, targetAgentId: string, logData: any) {
    const edgeId = `edge-${sourceAgentId}-${targetAgentId}-${logData.logNumber}`;
    
    // Remove any existing edge for this log
    const newEdges = edges.filter(edge => edge.id !== selectedLogEdge);
    
    // Add new edge
    newEdges.push({
      id: edgeId,
      type: 'logEdge',
      source: sourceAgentId,
      target: targetAgentId,
      data: {
        logNumber: logData.logNumber,
        message: logData.message,
        timestamp: logData.timestamp
      }
    });
    
    edges = newEdges;
    selectedLogEdge = edgeId;
    
    console.log('Created edge:', edgeId, 'from', sourceAgentId, 'to', targetAgentId);
  }

  function getAgentChipData(agentIdOrName: string) {
    // Convert reported_by names to agent IDs if possible
    const actualAgentId = getAgentIdFromReportedBy(agentIdOrName);
    
    // First try to find by agent ID
    let agentData = agentDataMap.get(actualAgentId);
    
    // If not found by ID, try to find by name (for system messages, etc.)
    if (!agentData) {
      // For green agent, use greenAgentInfo
      if (actualAgentId === battle?.green_agent_id && greenAgentInfo) {
        agentData = greenAgentInfo;
      }
      // For system or other names, create a basic structure
      else {
        console.log('Creating basic agent data for:', agentIdOrName);
        return {
          identifier: agentIdOrName,
          description: agentIdOrName,
          avatar_url: undefined
        };
      }
    }
    
    const result = {
      identifier: agentData?.register_info?.alias || agentData?.register_info?.name || agentData?.agent_card?.name || agentIdOrName,
      description: agentData?.agent_card?.description || agentData?.register_info?.description || agentIdOrName,
      avatar_url: agentData?.register_info?.avatar_url || agentData?.agent_card?.avatar_url
    };
    
    console.log('Agent chip data for', agentIdOrName, ':', result);
    return result;
  }
  
  function renderMarkdown(content: string): string {
    if (!content) return '';
    
    // Configure marked to allow images and other features
    marked.setOptions({
      breaks: true,
      gfm: true
    });
    
    const result = marked(content);
    return typeof result === 'string' ? result : '';
  }
  
  function isBattleInProgress(): boolean {
    if (!battle) return false;
    
    if (battle.state === 'finished' || battle.state === 'error') {
      return false;
    }
    
    if (battle.interact_history && Array.isArray(battle.interact_history)) {
      return !battle.interact_history.some((entry: any) => entry.is_result);
    }
    
    return true;
  }
  
  async function cancelBattle() {
    if (!battle || !canCancelBattle) return;
    
    const confirmed = confirm('Are you sure you want to cancel this battle? This will end the battle with a draw result.');
    if (!confirmed) return;
    
    try {
      const cancelEvent = {
        is_result: true,
        winner: "draw",
        message: "Battle cancelled by user",
        reported_by: "system",
        timestamp: new Date().toISOString(),
        detail: {
          reason: "user_cancelled"
        }
      };
      
      const response = await fetch(`/api/battles/${$page.params.battle_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(cancelEvent)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to cancel battle: ${response.status}`);
      }
      
      console.log('Battle cancelled successfully');
    } catch (err) {
      console.error('Error cancelling battle:', err);
      alert('Failed to cancel battle. Please try again.');
    }
  }
  
  onMount(async () => {
    loading = true;
    error = '';
    
    // Check if we're in development mode
    isDevMode = import.meta.env.VITE_DEV_LOGIN === "true";
    
    try {
      const res = await fetchWithTimeout(`/api/battles/${$page.params.battle_id}`);
      if (!res.ok) {
        error = 'Failed to load battle';
        return;
      }
      battle = await res.json();

      if (battle?.interact_history && Array.isArray(battle.interact_history)) {
        entryActiveTabs = {};
        battle.interact_history.forEach((entry: any, idx: number) => {
          entryActiveTabs[idx] = entry.asciinema_url ? 'asciinema' : 'logs';
        });
      }
      
      // Fetch agent names
      if (battle.green_agent_id) {
        greenAgentName = await fetchAgentName(battle.green_agent_id);
        greenAgentInfo = await fetchGreenAgentInfo(battle.green_agent_id);
      }
      if (battle.opponents && Array.isArray(battle.opponents)) {
        opponentNames = await Promise.all(
          battle.opponents.map(async (opponent: any) => {
            const agentName = await fetchAgentName(opponent.agent_id);
            return `${agentName} (${opponent.name})`;
          })
        );
        
        if (greenAgentInfo) {
          opponentRoleMap = buildOpponentRoleMap(greenAgentInfo, battle.opponents);
        }
      }
      
      // Connect to WebSocket for real-time updates
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/battles`;
      ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('Connected to battles WebSocket');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'battle_update' && data.battle.battle_id === $page.params.battle_id) {
          const oldBattle = battle;
          const newBattle = { ...data.battle };
          
          // Check if there are new log entries
          if (newBattle.interact_history && oldBattle?.interact_history) {
            const oldLength = oldBattle.interact_history.length;
            const newLength = newBattle.interact_history.length;
            
            if (newLength > oldLength) {
              // New log entries added - auto-expand the latest
              const newEntries = newBattle.interact_history.slice(oldLength);
              
              // Close all currently open agents and logs
              openAgents = new Set();
              openLogs = new Set();
              closingAgents = new Set();
              closingLogs = new Set();
              
              // Find the agent group for the latest entry
              const latestEntry = newEntries[newEntries.length - 1];
              const agentGroups = getChronologicalAgentGroups();
                             const latestAgentGroup = agentGroups.find(group => 
                 group.entries.some((entry: any) => 
                   entry.timestamp === latestEntry.timestamp && 
                   entry.message === latestEntry.message
                 )
               );
              
              if (latestAgentGroup) {
                // Open the agent group for the latest entry
                openAgents = new Set([latestAgentGroup.groupId]);
                
                // Open the specific log entry
                const latestLogEntry = latestAgentGroup.entries[latestAgentGroup.entries.length - 1];
                const logId = `${latestAgentGroup.groupId}-log${latestLogEntry.logNumber}`;
                openLogs = new Set([logId]);
                
                // Auto-open message and detail sections for the new log
                const messageSectionId = `${logId}-message`;
                const detailSectionId = `${logId}-detail`;
                openLogSections = new Set([messageSectionId, detailSectionId]);
                
                console.log('Auto-expanded agent:', latestAgentGroup.agent, 'and log:', logId);
              }
            }
          }
          
          // Update battle data
          battle = newBattle;

          // Handle asciinema tabs for new entries
          if (battle?.interact_history && Array.isArray(battle.interact_history)) {
            battle.interact_history.forEach((entry: any, idx: number) => {
              if (entryActiveTabs[idx] === undefined) {
                entryActiveTabs[idx] = entry.asciinema_url ? 'asciinema' : 'logs';
              }
            });
          }
          
          // Update agent names if needed
          if (battle.green_agent_id && !greenAgentName) {
            fetchAgentName(battle.green_agent_id).then(name => greenAgentName = name);
          }
          if (battle.opponents && Array.isArray(battle.opponents)) {
            Promise.all(battle.opponents.map(async (opponent: any) => {
              const agentName = await fetchAgentName(opponent.agent_id);
              return `${agentName} (${opponent.name})`;
            })).then(names => opponentNames = names);
          }
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket connection closed');
      };
      
    } catch (err) {
      error = 'Failed to load battle';
      console.error(err);
    } finally {
      loading = false;
    }
  });
  
  // Cleanup function
  onDestroy(() => {
    if (ws) {
      ws.close();
    }
  });
</script>

<style>
  /* Custom animations for battle logs */
  .fade-in {
    animation: fadeIn 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }
  
  .fade-out {
    animation: fadeOut 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes fadeOut {
    from {
      opacity: 1;
      transform: translateY(0);
    }
    to {
      opacity: 0;
      transform: translateY(-10px);
    }
  }
  
  .log-entries {
    overflow: hidden;
    transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }
  
  .log-content {
    overflow: hidden;
    transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }
  
  /* Quick fade animations for agent sections */
  .agent-fade-in {
    animation: fadeIn 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }
  
  .agent-fade-out {
    animation: fadeOut 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }
</style>

<main class="p-6 max-w-6xl mx-auto">
  {#if loading}
    <div class="flex items-center justify-center h-64">
      <div class="text-lg text-muted-foreground">Loading...</div>
    </div>
  {:else if error}
    <div class="flex items-center justify-center h-64">
      <div class="text-lg text-destructive">Error: {error}</div>
    </div>
  {:else if battle}
    <!-- Battle Title -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-foreground">Battle {battle.battle_id}</h1>
    </div>
    <!-- Battle Details Section -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-4">
          <AgentChip 
            agent={getAgentChipData(battle.green_agent_id)}
            agent_id={battle.green_agent_id}
            clickable={true}
          />
          <div class="flex items-center gap-3">
            <span class="text-sm text-muted-foreground">Status:</span>
            <span class="px-3 py-1 rounded-full text-sm font-medium {battle.state === 'finished' ? 'bg-green-100 text-green-800' : battle.state === 'error' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}">
              {battle.state}
            </span>
                </div>
                  </div>
        {#if canCancelBattle}
          <button 
            onclick={cancelBattle}
            class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium"
          >
            Cancel Battle
          </button>
        {/if}
              </div>

      <!-- Opponents Section -->
      {#if battle.opponents && battle.opponents.length > 0}
        <div class="flex items-start gap-3">
          <span class="text-sm font-medium text-foreground w-24 pt-1">Opponents:</span>
          <div class="flex-1">
            <Carousel.Root 
              class="w-full"
              opts={{
                align: "start",
                loop: true,
                dragFree: true,
              }}
              plugins={[
                Autoplay({
                  delay: 6000,
                }),
              ]}
            >
              <Carousel.Content class="gap-2">
            {#each battle.opponents as opponent, i}
                  <Carousel.Item class="basis-auto">
                    <div class="p-1">
              <AgentChip 
                        agent={getAgentChipData(opponent.agent_id)}
                agent_id={opponent.agent_id}
                clickable={true}
              />
                    </div>
                  </Carousel.Item>
            {/each}
              </Carousel.Content>
            </Carousel.Root>
          </div>
              </div>
            {/if}
    </div>

    <!-- Big Card in the Middle -->
    <Card.Root class="min-h-[500px] p-4">
      <Card.Content class="h-full relative">
        <div class="w-full h-[500px]">
          <SvelteFlow {nodes} {edges} {nodeTypes} {edgeTypes} class="w-full h-full">
            <Background />
          </SvelteFlow>
          </div>
      </Card.Content>
    </Card.Root>

        <!-- Battle Logs - Minimalist Custom Design -->
    {#if battle?.interact_history && battle.interact_history.length > 0}
      {@const agentGroups = getChronologicalAgentGroups()}
      <div class="mt-8">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-foreground">Battle Logs</h2>
          <a 
            href="https://github.com/agentbeats/agentbeats" 
            target="_blank" 
            rel="noopener noreferrer"
            class="flex items-center justify-center p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted border border-border hover:border-border rounded-md transition-colors"
            title="Download from GitHub"
          >
            <DownloadIcon class="w-3.5 h-3.5" />
          </a>
        </div>
        <div class="space-y-6 -ml-2">
          {#each agentGroups as group}
            <div class="group">
              <!-- Agent Header -->
              <div class="flex items-center gap-3 w-full p-2">
                <button 
                  class="p-1 hover:bg-muted rounded transition-colors"
                  onclick={() => {
                    // Prevent multiple rapid clicks
                    if (closingAgents.has(group.groupId)) return;
                    
                    const newOpenAgents = new Set(openAgents);
                    const newClosingAgents = new Set(closingAgents);
                    
                    if (newOpenAgents.has(group.groupId)) {
                      // Start closing animation
                      newClosingAgents.add(group.groupId);
                      closingAgents = newClosingAgents;
                      
                      // Remove from open after animation
                      setTimeout(() => {
                        const currentOpenAgents = new Set(openAgents);
                        const currentClosingAgents = new Set(closingAgents);
                        
                        currentOpenAgents.delete(group.groupId);
                        currentClosingAgents.delete(group.groupId);
                        
                        openAgents = currentOpenAgents;
                        closingAgents = currentClosingAgents;
                      }, 200);
                    } else {
                      // Open immediately
                      newOpenAgents.add(group.groupId);
                      openAgents = newOpenAgents;
                    }
                  }}
                >
                  {#if openAgents.has(group.groupId)}
                    <ChevronDownIcon class="w-4 h-4 text-muted-foreground" />
                  {:else}
                    <ChevronUpIcon class="w-4 h-4 text-muted-foreground" />
                  {/if}
                </button>
                  <AgentChip 
                  agent={getAgentChipData(group.agent)}
                  agent_id={getAgentIdFromReportedBy(group.agent)}
                    clickable={false}
                  />
                <span class="text-muted-foreground text-sm">({group.entries.length})</span>
                {#if group.entries.some((entry: any) => entry.is_result)}
                  <span class="text-xs text-green-600">✓</span>
                {/if}
                <div class="flex-1"></div>
                <span class="text-xs text-muted-foreground">
                  {new Date(group.entries[0].timestamp).toLocaleTimeString()}
                </span>
              </div>
              
              <!-- Log Entries -->
              {#if openAgents.has(group.groupId) || closingAgents.has(group.groupId)}
                <div class="mt-2 space-y-1 log-entries {closingAgents.has(group.groupId) ? 'agent-fade-out' : 'agent-fade-in'}">
                  {#each group.entries as entry}
                    {@const logId = `${group.groupId}-log${(entry as any).logNumber}`}
                    {@const messageSectionId = `${logId}-message`}
                    {@const detailSectionId = `${logId}-detail`}
                    {@const markdownSectionId = `${logId}-markdown`}
                    {@const winnerSectionId = `${logId}-winner`}
                    <div class="ml-8">
                      <div class="flex items-center gap-2 w-full p-2">
                                           <button 
                          class="p-1 hover:bg-muted rounded transition-colors"
                    onclick={() => {
                            // Prevent multiple rapid clicks
                            if (closingLogs.has(logId)) return;
                            
                            const newOpenLogs = new Set(openLogs);
                            const newClosingLogs = new Set(closingLogs);
                            
                            if (newOpenLogs.has(logId)) {
                              // Start closing animation
                              newClosingLogs.add(logId);
                              closingLogs = newClosingLogs;
                              
                              // Remove from open after animation
                              setTimeout(() => {
                                const currentOpenLogs = new Set(openLogs);
                                const currentClosingLogs = new Set(closingLogs);
                                
                                currentOpenLogs.delete(logId);
                                currentClosingLogs.delete(logId);
                                
                                openLogs = currentOpenLogs;
                                closingLogs = currentClosingLogs;
                              }, 200);
                      } else {
                              // Open immediately
                              newOpenLogs.add(logId);
                              openLogs = newOpenLogs;
                              
                              // Auto-open message and detail sections for this log
                              const messageSectionId = `${logId}-message`;
                              const detailSectionId = `${logId}-detail`;
                              const newOpenSections = new Set(openLogSections);
                              newOpenSections.add(messageSectionId);
                              newOpenSections.add(detailSectionId);
                              openLogSections = newOpenSections;
                              
                              // Create edge between agents involved in this log
                              const sourceAgentId = getAgentIdFromReportedBy(group.agent);
                              let targetAgentId = null;
                              
                              // Try to find target agent from log data
                              if (entry.detail?.target_agent) {
                                targetAgentId = getAgentIdFromReportedBy(entry.detail.target_agent);
                              } else if (entry.detail?.opponent) {
                                targetAgentId = getAgentIdFromReportedBy(entry.detail.opponent);
                              } else if (battle.green_agent_id && sourceAgentId !== battle.green_agent_id) {
                                // If source is not green agent, connect to green agent
                                targetAgentId = battle.green_agent_id;
                              } else if (battle.opponents && battle.opponents.length > 0) {
                                // If source is green agent, connect to first opponent
                                targetAgentId = battle.opponents[0].agent_id;
                              }
                              
                              if (targetAgentId && sourceAgentId !== targetAgentId) {
                                createLogEdge(sourceAgentId, targetAgentId, entry);
                              }
                            }
                          }}
                        >
                          {#if openLogs.has(logId)}
                            <ChevronDownIcon class="w-4 h-4 text-muted-foreground" />
                          {:else}
                            <ChevronUpIcon class="w-4 h-4 text-muted-foreground" />
                          {/if}
                        </button>
                        <span class="text-xs text-muted-foreground font-mono min-w-[3ch]">#{entry.logNumber}</span>
                        <span class="text-foreground text-sm flex-1 truncate">
                          {entry.message.length > 60 ? entry.message.substring(0, 60) + '...' : entry.message}
                        </span>
                        <span class="text-xs text-muted-foreground">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </span>
                              {#if entry.is_result}
                          <span class="text-xs text-green-600">✓</span>
                              {/if}
                      </div>
                      
                                            <!-- Log Content -->
                      {#if openLogs.has(logId) || closingLogs.has(logId)}
                        <div class="ml-8 mt-1 log-content {closingLogs.has(logId) ? 'fade-out' : 'fade-in'}">
                          <!-- Message -->
                          <div class="mb-2">
                            <div class="flex items-center gap-2 w-full p-2">
                                                            <button 
                                class="p-1 hover:bg-muted rounded transition-colors"
                                onclick={() => {
                                  if (closingLogSections.has(messageSectionId)) return;
                                  
                                  const newOpenSections = new Set(openLogSections);
                                  const newClosingSections = new Set(closingLogSections);
                                  
                                  if (newOpenSections.has(messageSectionId)) {
                                    newClosingSections.add(messageSectionId);
                                    closingLogSections = newClosingSections;
                                    
                                    setTimeout(() => {
                                      const currentOpenSections = new Set(openLogSections);
                                      const currentClosingSections = new Set(closingLogSections);
                                        
                                      currentOpenSections.delete(messageSectionId);
                                      currentClosingSections.delete(messageSectionId);
                                        
                                      openLogSections = currentOpenSections;
                                      closingLogSections = currentClosingSections;
                                    }, 200);
                                  } else {
                                    newOpenSections.add(messageSectionId);
                                    openLogSections = newOpenSections;
                                  }
                                }}
                              >
                                {#if openLogSections.has(messageSectionId)}
                                  <ChevronDownIcon class="w-4 h-4 text-muted-foreground" />
                                {:else}
                                  <ChevronUpIcon class="w-4 h-4 text-muted-foreground" />
                                {/if}
                              </button>
                              <span class="text-foreground text-sm flex-1 truncate">Message</span>
                            </div>
                            {#if openLogSections.has(messageSectionId) || closingLogSections.has(messageSectionId)}
                              <div class="ml-8 mt-1 log-content {closingLogSections.has(messageSectionId) ? 'fade-out' : 'fade-in'}">
                                <pre class="bg-muted p-2 rounded text-xs overflow-x-auto">{entry.message}</pre>
                              </div>
                            {/if}
                          </div>

                          <!-- Detail -->
                          {#if entry.detail}
                            <div class="mb-2">
                              <div class="flex items-center gap-2 w-full p-2">
                                <button 
                                  class="p-1 hover:bg-muted rounded transition-colors"
                                  onclick={() => {
                                    if (closingLogSections.has(detailSectionId)) return;
                                    
                                    const newOpenSections = new Set(openLogSections);
                                    const newClosingSections = new Set(closingLogSections);
                                    
                                    if (newOpenSections.has(detailSectionId)) {
                                      newClosingSections.add(detailSectionId);
                                      closingLogSections = newClosingSections;
                                      
                                      setTimeout(() => {
                                        const currentOpenSections = new Set(openLogSections);
                                        const currentClosingSections = new Set(closingLogSections);
                                        
                                        currentOpenSections.delete(detailSectionId);
                                        currentClosingSections.delete(detailSectionId);
                                        
                                        openLogSections = currentOpenSections;
                                        closingLogSections = currentClosingSections;
                                      }, 200);
                                    } else {
                                      newOpenSections.add(detailSectionId);
                                      openLogSections = newOpenSections;
                                    }
                                  }}
                                >
                                  {#if openLogSections.has(detailSectionId)}
                                    <ChevronDownIcon class="w-4 h-4 text-muted-foreground" />
                                  {:else}
                                    <ChevronUpIcon class="w-4 h-4 text-muted-foreground" />
                                  {/if}
                                </button>
                                <span class="text-foreground text-sm flex-1 truncate">Detail</span>
                              </div>
                              {#if openLogSections.has(detailSectionId) || closingLogSections.has(detailSectionId)}
                                <div class="ml-8 mt-1 log-content {closingLogSections.has(detailSectionId) ? 'fade-out' : 'fade-in'}">
                                  <pre class="bg-muted p-2 rounded text-xs overflow-x-auto">{JSON.stringify(entry.detail, null, 2)}</pre>
                                </div>
                              {/if}
                            </div>
                          {/if}

                                                    <!-- Markdown Content -->
                          {#if entry.markdown_content}
                            <div class="mb-2">
                              <div class="flex items-center gap-2 w-full p-2">
                                <button 
                                  class="p-1 hover:bg-muted rounded transition-colors"
                                  onclick={() => {
                                    if (closingLogSections.has(markdownSectionId)) return;
                                    
                                    const newOpenSections = new Set(openLogSections);
                                    const newClosingSections = new Set(closingLogSections);
                                    
                                    if (newOpenSections.has(markdownSectionId)) {
                                      newClosingSections.add(markdownSectionId);
                                      closingLogSections = newClosingSections;
                                      
                                      setTimeout(() => {
                                        const currentOpenSections = new Set(openLogSections);
                                        const currentClosingSections = new Set(closingLogSections);
                                        
                                        currentOpenSections.delete(markdownSectionId);
                                        currentClosingSections.delete(markdownSectionId);
                                        
                                        openLogSections = currentOpenSections;
                                        closingLogSections = currentClosingSections;
                                      }, 200);
                                    } else {
                                      newOpenSections.add(markdownSectionId);
                                      openLogSections = newOpenSections;
                                    }
                                  }}
                                >
                                  {#if openLogSections.has(markdownSectionId)}
                                    <ChevronDownIcon class="w-4 h-4 text-muted-foreground" />
                                  {:else}
                                    <ChevronUpIcon class="w-4 h-4 text-muted-foreground" />
                                  {/if}
                                </button>
                                <span class="text-foreground text-sm flex-1 truncate">Markdown Content</span>
                              </div>
                              {#if openLogSections.has(markdownSectionId) || closingLogSections.has(markdownSectionId)}
                                <div class="ml-8 mt-1 log-content {closingLogSections.has(markdownSectionId) ? 'fade-out' : 'fade-in'}">
                                  <div class="text-sm prose prose-sm max-w-none bg-muted p-2 rounded">
                              {@html renderMarkdown(entry.markdown_content)}
                                  </div>
                                </div>
                              {/if}
                            </div>
                          {/if}

                          <!-- Winner (only for results) -->
                          {#if entry.winner}
                            <div class="mb-2">
                              <div class="flex items-center gap-2 w-full p-2">
                                <button 
                                  class="p-1 hover:bg-muted rounded transition-colors"
                                  onclick={() => {
                                    if (closingLogSections.has(winnerSectionId)) return;
                                    
                                    const newOpenSections = new Set(openLogSections);
                                    const newClosingSections = new Set(closingLogSections);
                                    
                                    if (newOpenSections.has(winnerSectionId)) {
                                      newClosingSections.add(winnerSectionId);
                                      closingLogSections = newClosingSections;
                                      
                                      setTimeout(() => {
                                        const currentOpenSections = new Set(openLogSections);
                                        const currentClosingSections = new Set(closingLogSections);
                                        
                                        currentOpenSections.delete(winnerSectionId);
                                        currentClosingSections.delete(winnerSectionId);
                                        
                                        openLogSections = currentOpenSections;
                                        closingLogSections = currentClosingSections;
                                      }, 200);
                                    } else {
                                      newOpenSections.add(winnerSectionId);
                                      openLogSections = newOpenSections;
                                    }
                                  }}
                                >
                                  {#if openLogSections.has(winnerSectionId)}
                                    <ChevronDownIcon class="w-4 h-4 text-muted-foreground" />
                                  {:else}
                                    <ChevronUpIcon class="w-4 h-4 text-muted-foreground" />
                                  {/if}
                                </button>
                                <span class="text-foreground text-sm flex-1 truncate">Winner</span>
                              </div>
                              {#if openLogSections.has(winnerSectionId) || closingLogSections.has(winnerSectionId)}
                                <div class="ml-8 mt-1 log-content {closingLogSections.has(winnerSectionId) ? 'fade-out' : 'fade-in'}">
                                  <span class="text-green-700 font-mono">🏆 {entry.winner}</span>
                                </div>
                              {/if}
                            </div>
                          {/if}
                          
                          <!-- Asciinema Terminal Output -->
                          {#if (entry.terminal_input && entry.terminal_output) || entry.asciinema_url}
                            <div class="mt-2 rounded-md border border-zinc-800 text-zinc-100 font-mono text-xs overflow-hidden" style="background-color: #121314;">
                              <div class="flex items-center gap-2 px-3 py-1.5" style="background-color: #121314;">
                                <div class="flex items-center gap-2 border-b border-zinc-800 pb-1.5 -mb-1.5">
                                  <span class="h-2 w-2 rounded-full bg-red-500"></span>
                                  <span class="h-2 w-2 rounded-full bg-yellow-400"></span>
                                  <span class="h-2 w-2 rounded-full bg-green-500"></span>
                                  <span class="ml-2 text-[10px] text-zinc-400">Terminal</span>
                                </div>
                                
                                <!-- Terminal-style tabs -->
                                <div class="ml-4 flex flex-1 gap-px -mb-px">
                                  {#if entry.asciinema_url}
                                    <button 
                                      class="flex-1 py-1 text-[10px] border-t border-l border-r {entryActiveTabs[entry.logNumber] === 'asciinema' ? 'text-zinc-200 border-zinc-400 font-medium rounded-t-sm' : 'text-zinc-400 border-transparent hover:text-zinc-300'}"
                                      style="{entryActiveTabs[entry.logNumber] === 'asciinema' ? 'background-color: #121314;' : ''}"
                                      onclick={() => entryActiveTabs[entry.logNumber] = 'asciinema'}
                                    >
                                      Live
                                    </button>
                                  {/if}
                                  <button 
                                    class="flex-1 py-1 text-[10px] border-t border-l border-r {entryActiveTabs[entry.logNumber] === 'logs' || !entryActiveTabs[entry.logNumber] ? 'text-zinc-200 border-zinc-400 font-medium rounded-t-sm' : 'text-zinc-400 border-transparent hover:text-zinc-300'}"
                                    style="{entryActiveTabs[entry.logNumber] === 'logs' || !entryActiveTabs[entry.logNumber] ? 'background-color: #121314;' : ''}"
                                    onclick={() => entryActiveTabs[entry.logNumber] = 'logs'}
                                  >
                                    Logs
                                  </button>
                                </div>
                              </div>
                              <!-- Tab content -->
                              {#if entryActiveTabs[entry.logNumber] === 'asciinema' && entry.asciinema_url}
                                <div class="p-2">
                                  <AsciinemaPlayerView src={entry.asciinema_url} options={{ fit: 'width', autoplay: true, loop: false, speed: 0.3 }} />
                                </div>
                              {:else if entryActiveTabs[entry.logNumber] === 'logs' || (!entryActiveTabs[entry.logNumber] && !entry.asciinema_url)}
                                {#if entry.terminal_input && entry.terminal_output}
                                  <pre class="px-3 py-2 whitespace-pre-wrap leading-relaxed max-h-100 overflow-y-auto"><span class="text-green-400">docker $ </span><span class="text-yellow-300 font-medium">{entry.terminal_input}</span>
<span class="text-white">{entry.terminal_output}</span></pre>
                                {/if}
                              {/if}
                            </div>
                          {/if}
                        </div>
                      {/if}
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</main>