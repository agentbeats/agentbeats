/**
 * Modern Svelte 5 Hooks
 * 
 * These hooks are designed to work seamlessly with Svelte 5's runes system.
 * They provide reactive state that automatically updates components when data changes.
 * 
 * Key principles:
 * 1. Simple and consistent API across all hooks
 * 2. Direct property access (no getters or manual subscriptions)
 * 3. Built-in computed values using $derived()
 * 4. Automatic reactivity with Svelte 5 runes
 * 
 * Usage pattern:
 * ```svelte
 * <script>
 *   import { useAgents } from '$lib/hooks';
 *   
 *   const agents = useAgents();
 *   
 *   // Load data on mount
 *   $effect(() => {
 *     agents.loadMyAgents();
 *   });
 *   
 *   // React to data changes
 *   $effect(() => {
 *     console.log('Agents updated:', agents.data);
 *   });
 * </script>
 * 
 * <!-- Use reactive data directly -->
 * {#if agents.isLoading}
 *   Loading...
 * {:else if agents.error}
 *   Error: {agents.error}
 * {:else}
 *   {#each agents.data as agent}
 *     <div>{agent.name}</div>
 *   {/each}
 * {/if}
 * ```
 */

// Main hooks exports
export { useAgents } from './useAgents.svelte';
export { useBattles } from './useBattles.svelte';
export { useAuth } from './useAuth.svelte';

// Utility hooks
export { IsMobile } from './is-mobile.svelte';