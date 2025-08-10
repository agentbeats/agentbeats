<script lang="ts">
  import { Handle, Position } from '@xyflow/svelte';
  
  export let id: string;
  export let source: string;
  export let target: string;
  export let sourceX: number;
  export let sourceY: number;
  export let targetX: number;
  export let targetY: number;
  export let sourcePosition: Position;
  export let targetPosition: Position;
  export let data: any = {};
  
  // Calculate edge path
  $: path = `M ${sourceX} ${sourceY} L ${targetX} ${targetY}`;
</script>

<g>
  <path
    d={path}
    stroke="#6b7280"
    stroke-width="2"
    fill="none"
    stroke-dasharray="5,5"
    class="animate-pulse"
  />
  <circle
    cx={targetX}
    cy={targetY}
    r="4"
    fill="#6b7280"
    class="animate-pulse"
  />
</g> 