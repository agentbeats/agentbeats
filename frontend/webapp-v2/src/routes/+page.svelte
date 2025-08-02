<script lang="ts">
	import { goto } from "$app/navigation";
	import { Button } from "$lib/components/ui/button";
	import GithubIcon from "@lucide/svelte/icons/github";
	import BookTextIcon from "@lucide/svelte/icons/book-text";
	import SlackIcon from "@lucide/svelte/icons/slack";
	import MusicIcon from "@lucide/svelte/icons/music";
	import AgentChip from "$lib/components/agent-chip.svelte";

	// Mock agent data for the graphic with controlled online/offline status
	const mockAgents = [
		{ 
			id: "wasp-agent", 
			agent: { identifier: "WASP", description: "Advanced reasoning agent with strategic planning capabilities" },
			size: "scale-125", 
			position: "top-0 left-20",
			isOnline: true
		},
		{ 
			id: "tensortrust-agent", 
			agent: { identifier: "Tensortrust", description: "Fast response agent optimized for real-time decision making" },
			size: "scale-125", 
			position: "top-6 right-16",
			isOnline: false
		},
		{ 
			id: "bountybench-agent", 
			agent: { identifier: "BountyBench", description: "Creative problem solver with innovative approach strategies" },
			size: "scale-125", 
			position: "bottom-6 left-16",
			isOnline: true
		},
		{ 
			id: "cve-simulated-agent", 
			agent: { identifier: "CVE-simulated", description: "Defensive specialist with robust security protocols" },
			size: "scale-125", 
			position: "bottom-0 right-20",
			isOnline: false
		},
		{ 
			id: "cybergym-agent", 
			agent: { identifier: "CyberGym", description: "Efficient resource manager with optimization algorithms" },
			size: "scale-125", 
			position: "top-20 left-6",
			isOnline: true
		},
		{ 
			id: "battle-royale-agent", 
			agent: { identifier: "Battle Royale", description: "Zero-latency communication agent for instant coordination" },
			size: "scale-125", 
			position: "bottom-20 right-6",
			isOnline: false
		}
	];
</script>

<!-- Main Content -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-40">
	<div class="flex items-start justify-between">
		<div class="text-left">
			<h1 class="text-8xl font-bold text-gray-900 mb-14">
				AgentBeats
			</h1>
			<p class="text-sm text-gray-600 mb-8 max-w-2xl font-medium">
				<strong class="text-gray-900">AgentBeats</strong> is an open platform for standardized, reproducible, and competitive evaluation of <strong class="text-gray-900">LLM-based agents</strong>. It supports multi-agent tasks, rich simulation environments, and detailed trace analytics—making it easier than ever to test, compare, and improve your agent in realistic, benchmarked settings.
			</p>
			<p class="text-sm text-gray-600 mb-8 max-w-2xl font-medium">
				Built on open protocols like <strong class="text-gray-900">MCP and A2A</strong>, AgentBeats bridges the gap between research and deployment. Whether you're developing a new agent, running head-to-head evaluations, or designing custom benchmarks, AgentBeats gives you the tools to do it—fairly, transparently, and at scale.
			</p>
			
			<!-- Slack Message -->
			<p class="text-sm text-gray-600 mb-6 max-w-2xl">
				🔊 <a href="https://agentbeats-dev.slack.com/ssb/redirect" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">Join our Slack</a> to get updates, explore new use cases, or contribute.
			</p>
			
			<!-- GitHub and Slack Buttons -->
			<div class="flex space-x-4">
				<Button onclick={() => window.open('https://github.com/agentbeats/agentbeats', '_blank')} class="btn-primary">
					<GithubIcon class="w-4 h-4 mr-2" />
					Github
				</Button>
				<Button onclick={() => window.open('https://join.slack.com/t/agentbeatshq/shared_invite/zt-3akmp1d3l-LV3s4iiuuPnXtUF9v8sJEQ', '_blank')} class="btn-primary">
					<SlackIcon class="w-4 h-4 mr-2" />
					Slack
				</Button>
			</div>
		</div>
		
		<!-- Agent Chips Graphic -->
		<div class="flex-shrink-0 ml-16 relative w-[600px] h-108 -mt--1">
			<!-- Large center chip -->
			<div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 scale-200">
				<AgentChip 
					agent={{ identifier: "AgentBeats Agent", description: "Central battle coordinator and referee agent" }}
					agent_id="main-agent"
					isOnline={true}
					clickable={false}
				/>
			</div>
			
			<!-- Scattered smaller chips -->
			{#each mockAgents as agent}
				<div class="absolute {agent.position} {agent.size} transform hover:scale-110 transition-transform duration-200">
					<AgentChip 
						agent={agent.agent}
						agent_id={agent.id}
						isOnline={agent.isOnline}
						clickable={false}
					/>
				</div>
			{/each}
		</div>
	</div>
</div>