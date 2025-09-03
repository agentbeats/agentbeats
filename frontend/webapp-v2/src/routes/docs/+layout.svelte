<script lang="ts">
	import '../../app.css';
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
	import { Separator } from "$lib/components/ui/separator/index.js";
	import DocsSidebar from "./components/sidebar.svelte";
	import { fade } from 'svelte/transition';
	import { onNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	
	let { children } = $props();
	
	// Get breadcrumb data based on current route
	let breadcrumbData = $derived(() => {
		const path = $page.url.pathname;
		
		if (path === '/docs') {
			return { parent: null as string | null, current: 'Documentation' };
		}
		
		// Parse the path to extract breadcrumb segments
		const segments = path.split('/').filter(segment => segment.length > 0);
		
		// Remove 'docs' from segments and create breadcrumb data
		const docSegments = segments.slice(1); // Remove 'docs'
		
		if (docSegments.length === 0) {
			return { parent: null as string | null, current: 'Documentation' };
		}
		
		// Convert kebab-case to Title Case
		const formatSegment = (segment: string) => {
			return segment
				.split('-')
				.map(word => word.charAt(0).toUpperCase() + word.slice(1))
				.join(' ');
		};
		
		if (docSegments.length === 1) {
			// Single level: /docs/getting-started
			return { 
				parent: 'Documentation', 
				current: formatSegment(docSegments[0]) 
			};
		} else if (docSegments.length === 2) {
			// Two levels: /docs/getting-started/quick-start
			return { 
				parent: 'Documentation', 
				current: formatSegment(docSegments[0]), 
				child: formatSegment(docSegments[1]) 
			};
		}
		
		// Fallback for deeper nesting if needed
		return { parent: 'Documentation', current: 'Documentation' };
	});
	
	// Page transitions
	onNavigate((navigation) => {
		if (!document.startViewTransition) return;
	
		return new Promise((resolve) => {
			document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
		});
	});
	
	onMount(() => {
		// Add copy buttons to code blocks
		const codeBlocks = document.querySelectorAll('pre');
		codeBlocks.forEach((pre, index) => {
			const code = pre.querySelector('code');
			if (code) {
				const copyButton = document.createElement('button');
				copyButton.className = 'absolute top-2 right-2 p-2 text-muted-foreground hover:text-foreground bg-muted hover:bg-muted/80 rounded transition-colors';
				copyButton.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>';
				
				copyButton.onclick = async () => {
					try {
						await navigator.clipboard.writeText(code.textContent || '');
						copyButton.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
						setTimeout(() => {
							copyButton.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>';
						}, 2000);
					} catch (err) {
						console.error('Failed to copy:', err);
					}
				};
				
				pre.style.position = 'relative';
				pre.appendChild(copyButton);
			}
		});
	});
</script>

<style>
	:global(.markdown-body p + p) {
		margin-top: 2rem !important;
	}
	
	:global(.markdown-body h1) {
		font-size: 3rem !important;
		font-weight: 700 !important;
		line-height: 1.25 !important;
		margin-bottom: 2rem !important;
		letter-spacing: -0.025em !important;
	}
	
	:global(.markdown-body h2) {
		font-size: 1.875rem !important;
		font-weight: 700 !important;
		line-height: 1.33333 !important;
		margin-top: 2rem !important;
		margin-bottom: 1rem !important;
		letter-spacing: -0.025em !important;
	}
	
	:global(.markdown-body h3) {
		font-size: 1.5rem !important;
		font-weight: 700 !important;
		line-height: 1.5 !important;
		margin-top: 1.5rem !important;
		margin-bottom: 0.75rem !important;
		letter-spacing: -0.025em !important;
	}
	
	:global(.markdown-body h4) {
		font-size: 1.25rem !important;
		font-weight: 700 !important;
		line-height: 1.6 !important;
		margin-top: 1rem !important;
		margin-bottom: 0.5rem !important;
		letter-spacing: -0.025em !important;
	}
	
	:global(.markdown-body pre) {
		position: relative;
		background: #0d1117 !important;
		border: 1px solid #30363d !important;
		border-radius: 6px !important;
		padding: 16px !important;
		margin: 16px 0 !important;
	}
	
	:global(.markdown-body code) {
		background: #f6f8fa !important;
		border: 1px solid #d0d7de !important;
		border-radius: 6px !important;
		padding: 0.2em 0.4em !important;
		font-size: 85% !important;
		font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace !important;
	}
	
	:global(.markdown-body pre code) {
		background: transparent !important;
		border: none !important;
		padding: 0 !important;
		color: #c9d1d9 !important;
	}
	
	:global(.markdown-body ul) {
		list-style-type: disc !important;
		padding-left: 2em !important;
		margin: 1em 0 !important;
	}
	
	:global(.markdown-body ol) {
		list-style-type: decimal !important;
		padding-left: 2em !important;
		margin: 1em 0 !important;
	}
	
	:global(.markdown-body li) {
		margin: 0.5em 0 !important;
		line-height: 1.6 !important;
	}
	
	:global(.markdown-body li::marker) {
		color: #656d76 !important;
	}
	
	:global(.markdown-body hr) {
		margin: 3rem 0 !important;
		border: none !important;
		border-top: 1px solid #d0d7de !important;
	}
</style>

<Sidebar.Provider style="--sidebar-width: 14rem;">
	<DocsSidebar />
	<Sidebar.Inset>
		<header class="flex h-16 shrink-0 items-center gap-2 px-4">
			<Sidebar.Trigger class="-ml-1" />
			<Separator orientation="vertical" class="mr-2 data-[orientation=vertical]:h-4" />
			<Breadcrumb.Root>
				<Breadcrumb.List>
					{#if breadcrumbData().parent}
						<Breadcrumb.Item class="hidden md:block">
							<Breadcrumb.Link href="/docs">{breadcrumbData().parent}</Breadcrumb.Link>
						</Breadcrumb.Item>
						<Breadcrumb.Separator class="hidden md:block" />
					{/if}
					<Breadcrumb.Item>
						{#if breadcrumbData().child}
							<Breadcrumb.Link href="/docs">{breadcrumbData().current}</Breadcrumb.Link>
						{:else}
							<Breadcrumb.Page>{breadcrumbData().current}</Breadcrumb.Page>
						{/if}
					</Breadcrumb.Item>
					{#if breadcrumbData().child}
						<Breadcrumb.Separator class="hidden md:block" />
						<Breadcrumb.Item>
							<Breadcrumb.Page>{breadcrumbData().child}</Breadcrumb.Page>
						</Breadcrumb.Item>
					{/if}
				</Breadcrumb.List>
			</Breadcrumb.Root>
		</header>
		<div class="flex flex-1 flex-col gap-4 p-14 pt-6">
			<div in:fade={{ duration: 200 }} out:fade={{ duration: 150 }}>
				{@render children()}
			</div>
		</div>
	</Sidebar.Inset>
</Sidebar.Provider> 