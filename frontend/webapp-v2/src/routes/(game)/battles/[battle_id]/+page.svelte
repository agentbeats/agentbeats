<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { marked } from 'marked';
  import { userEmail } from '$lib/stores/auth';
  import AsciinemaPlayerView from '$lib/components/AsciinemaPlayerView.svelte';
  
  let battle: any = null;
  let loading = true;
  let error = '';
  let greenAgentName = '';
  let opponentNames: string[] = [];
  let ws: WebSocket | null = null;
  let greenAgentInfo: any = null;
  let opponentRoleMap = new Map<string, string>(); // name -> role mapping
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
  
  $: battleId = $page.params.battle_id;
  
  $: battleInProgress = battle ? isBattleInProgress() : false;
  
  // Check if current user can cancel the battle
  $: canCancelBattle = battleInProgress && (
    isDevMode || 
    (battle?.created_by && $userEmail && battle.created_by === $userEmail)
  );
  
  async function fetchAgentName(agentId: string): Promise<string> {
    try {
      const res = await fetch(`/api/agents/${agentId}`);
      if (!res.ok) return agentId;
      const agent = await res.json();
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
  
  function getEntryBackgroundClass(reportedBy: string): string {
    const lowerReportedBy = reportedBy.toLowerCase();
    if (reportedBy === 'system') {
      return 'bg-gray-50 border-gray-200';
    } else if (lowerReportedBy.includes('blue')) {
      return 'bg-blue-50 border-blue-200';
    } else if (lowerReportedBy.includes('red')) {
      return 'bg-red-50 border-red-200';
    } else if (reportedBy === 'green_agent' || lowerReportedBy.includes('green')) {
      return 'bg-green-50 border-green-200';
    } else if (opponentRoleMap.has(reportedBy)) {
      const role = opponentRoleMap.get(reportedBy);
      if (role === 'blue_agent') {
        return 'bg-blue-50 border-blue-200';
      } else if (role === 'red_agent') {
        return 'bg-red-50 border-red-200';
      }
    }
    // Default background for unknown reported_by
    return 'bg-yellow-50 border-yellow-200';
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
  
  function scrollToBottom() {
    if (interactHistoryContainer) {
      setTimeout(() => {
        interactHistoryContainer?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'end' 
        });
      }, 100);
    }
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
      
      const response = await fetch(`/api/battles/${battleId}`, {
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
      const res = await fetchWithTimeout(`/api/battles/${battleId}`);
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
        if (data.type === 'battle_update' && data.battle.battle_id === battleId) {
          const previousHistoryLength = battle?.interact_history?.length || 0;
          
          // create a new battle object to trigger Svelte's reactivity
          battle = { ...data.battle };

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
          
          // Auto-scroll if new interact history entries were added
          const currentHistoryLength = battle?.interact_history?.length || 0;
          if (currentHistoryLength > previousHistoryLength) {
            scrollToBottom();
          }
          
          // Also scroll when battle state changes (for loading indicator updates)
          if (battle.state === 'finished' || battle.state === 'error') {
            console.log('Battle finished, triggering scroll');
            scrollToBottom();
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
  import { onDestroy } from 'svelte';
  onDestroy(() => {
    if (ws) {
      ws.close();
    }
  });
  </script>
  
  <main class="p-4 flex flex-col min-h-[60vh] max-w-xl mx-auto">
    {#if loading}
      <div class="text-gray-900">Loading...</div>
    {:else if error}
      <div class="text-red-500">{error}</div>
    {:else if battle}
      <div class="mb-8 space-y-2 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">Battle #{battle.battle_id?.slice(0, 8)}</h1>
        <div class="text-sm text-gray-600 break-all">ID: <span class="font-semibold">{battle.battle_id}</span></div>
        <div class="text-sm text-gray-600">State: <span class="font-semibold">{battle.state}</span></div>
        <div class="text-sm text-gray-600">Green Agent: <span class="font-semibold">{greenAgentName}</span></div>
        <div class="text-sm text-gray-600">Opponents: <span class="font-semibold">{opponentNames.join(', ')}</span></div>
        {#if battle.result && battle.state === 'finished'}
          <div class="text-green-700">Winner: <span class="font-semibold">{battle.result.winner}</span></div>
        {/if}
        {#if battle.error && battle.state === 'error'}
          <div class="text-red-700">Error: <span class="font-semibold">{battle.error}</span></div>
        {/if}
        
        {#if canCancelBattle}
          <div class="mt-3 pt-3 border-t">
            <button 
              on:click={cancelBattle}
              class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 text-sm font-medium transition-colors"
              title="Cancel this battle and end it with a draw result"
            >
              Cancel Battle
            </button>
          </div>
        {/if}
      </div>
      <!-- Interact History -->
      {#if battle.interact_history && battle.interact_history.length > 0}
        <div class="flex flex-col gap-3 mt-6" bind:this={interactHistoryContainer}>
          <h2 class="text-lg font-semibold text-gray-900 mb-2">Interact History</h2>
          {#each battle.interact_history as entry, i (entry.timestamp + entry.message + i)}
            <div class="border rounded-lg p-3 {getEntryBackgroundClass(entry.reported_by)}">
              <div class="flex flex-row justify-between items-center mb-1">
                <span class="text-xs text-gray-600">{new Date(entry.timestamp).toLocaleString()}</span>
                <span class="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700">{entry.reported_by}</span>
                {#if entry.is_result}
                  <span class="text-xs font-bold text-green-700 ml-2">Result</span>
                {/if}
              </div>
              <div class="text-sm font-medium text-gray-900 mb-1">{entry.message}</div>
              {#if entry.markdown_content}
                <div class="markdown-content mt-2 bg-white p-3 rounded border text-sm">
                  {@html renderMarkdown(entry.markdown_content)}
                </div>
              {/if}
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
                          class="flex-1 py-1 text-[10px] border-t border-l border-r {entryActiveTabs[i] === 'asciinema' ? 'text-zinc-200 border-zinc-400 font-medium rounded-t-sm' : 'text-zinc-400 border-transparent hover:text-zinc-300'}"
                          style="{entryActiveTabs[i] === 'asciinema' ? 'background-color: #121314;' : ''}"
                          on:click={() => entryActiveTabs[i] = 'asciinema'}
                        >
                          Live
                        </button>
                      {/if}
                      <button 
                        class="flex-1 py-1 text-[10px] border-t border-l border-r {entryActiveTabs[i] === 'logs' || !entryActiveTabs[i] ? 'text-zinc-200 border-zinc-400 font-medium rounded-t-sm' : 'text-zinc-400 border-transparent hover:text-zinc-300'}"
                        style="{entryActiveTabs[i] === 'logs' || !entryActiveTabs[i] ? 'background-color: #121314;' : ''}"
                        on:click={() => entryActiveTabs[i] = 'logs'}
                      >
                        Logs
                      </button>
                      
                    </div>
                  </div>
                  <!-- Tab content -->
                  {#if entryActiveTabs[i] === 'asciinema' && entry.asciinema_url}
                    <div class="p-2">
                      <AsciinemaPlayerView src={entry.asciinema_url} options={{ fit: 'width', autoplay: true, loop: false, speed: 0.3 }} />
                    </div>
                  {:else if entryActiveTabs[i] === 'logs' || (!entryActiveTabs[i] && !entry.asciinema_url)}
                    {#if entry.terminal_input && entry.terminal_output}
                      <pre class="px-3 py-2 whitespace-pre-wrap leading-relaxed max-h-100 overflow-y-auto"><span class="text-green-400">docker $ </span><span class="text-yellow-300 font-medium">{entry.terminal_input}</span>
<span class="text-white">{entry.terminal_output}</span></pre>
                    {/if}
                  {/if}
                </div>
              {/if}
              {#if entry.detail}
                <pre class="text-xs bg-muted p-2 rounded overflow-x-auto mt-1">{JSON.stringify(entry.detail, null, 2)}</pre>
              {/if}
              {#if entry.winner}
                <div class="text-xs text-green-700 mt-1">Winner: <span class="font-mono">{entry.winner}</span></div>
              {/if}
            </div>
          {/each}
          
          <!-- Loading indicator for battles in progress -->
          {#if battleInProgress}
            <div class="border rounded-lg p-4 bg-purple-50 border-purple-200 flex items-center justify-center space-x-3">
              <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
              <span class="text-sm text-purple-700 font-medium">Battle in progress...</span>
            </div>
          {/if}
        </div>
      {:else if battle && battleInProgress}
        <!-- Show loading if no history yet but battle is starting -->
        <div class="flex flex-col gap-3 mt-6" bind:this={interactHistoryContainer}>
          <h2 class="text-lg font-semibold mb-2">Interact History</h2>
          <div class="border rounded-lg p-4 bg-purple-50 border-purple-200 flex items-center justify-center space-x-3">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
            <span class="text-sm text-purple-700 font-medium">Waiting for battle to start...</span>
          </div>
        </div>
      {/if}
    {/if}
  </main>
  
  <style>
    :global(.markdown-content h1) {
      font-size: 1.125rem;
      font-weight: bold;
      margin-bottom: 0.5rem;
      margin-top: 1rem;
    }
    
    :global(.markdown-content h2) {
      font-size: 1rem;
      font-weight: bold;
      margin-bottom: 0.5rem;
      margin-top: 0.75rem;
    }
    
    :global(.markdown-content h3) {
      font-size: 0.875rem;
      font-weight: bold;
      margin-bottom: 0.25rem;
      margin-top: 0.5rem;
    }
    
    :global(.markdown-content p) {
      margin-bottom: 0.5rem;
      line-height: 1.625;
    }
    
    :global(.markdown-content ul, .markdown-content ol) {
      margin-left: 1rem;
      margin-bottom: 0.5rem;
    }
    
    :global(.markdown-content li) {
      margin-bottom: 0.25rem;
    }
    
    :global(.markdown-content code) {
      background-color: #f3f4f6;
      padding: 0.125rem 0.25rem;
      border-radius: 0.25rem;
      font-size: 0.75rem;
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
    
    :global(.markdown-content pre) {
      background-color: #f3f4f6;
      padding: 0.5rem;
      border-radius: 0.25rem;
      overflow-x: auto;
      margin-bottom: 0.5rem;
    }
    
    :global(.markdown-content pre code) {
      background-color: transparent;
      padding: 0;
    }
    
    :global(.markdown-content blockquote) {
      border-left: 4px solid #d1d5db;
      padding-left: 1rem;
      font-style: italic;
      margin-bottom: 0.5rem;
    }
    
    :global(.markdown-content img) {
      max-width: 100%;
      height: auto;
      border-radius: 0.25rem;
      box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
      margin-bottom: 0.5rem;
    }
    
    :global(.markdown-content a) {
      color: #2563eb;
      text-decoration: none;
    }
    
    :global(.markdown-content a:hover) {
      text-decoration: underline;
    }
    
    :global(.markdown-content table) {
      width: 100%;
      border-collapse: collapse;
      border: 1px solid #d1d5db;
      margin-bottom: 0.5rem;
    }
    
    :global(.markdown-content th, .markdown-content td) {
      border: 1px solid #d1d5db;
      padding: 0.25rem 0.5rem;
      text-align: left;
    }
    
    :global(.markdown-content th) {
      background-color: #f3f4f6;
      font-weight: bold;
    }
  </style> 