<script lang="ts">
  import { onMount } from 'svelte';

  export let src: string; // path or URL to .cast file
  export let options: Record<string, any> = {};

  let container: HTMLDivElement;
  let playerLib: any = null;
  let cssLoaded = false;

  function isAsciinemaOrgUrl(url: string | undefined): boolean {
    return !!url && /https?:\/\/asciinema\.org\/.+/i.test(url);
  }

  function extractAsciinemaId(url: string): string | null {
    const m = url.match(/https?:\/\/asciinema\.org\/a\/([\w-]+)/i);
    return m?.[1] ?? null;
  }

  async function ensurePlayerLibLoaded(): Promise<void> {
    if (isAsciinemaOrgUrl(src)) {
      // For asciinema.org embeds we don't need the npm player or css
      return;
    }
    if (!playerLib) {
      const { default: AsciinemaPlayer } = await import('asciinema-player');
      playerLib = AsciinemaPlayer;
    }
    if (!cssLoaded) {
      await import('asciinema-player/dist/bundle/asciinema-player.css');
      cssLoaded = true;
    }
  }

  function renderPlayer(): void {
    if (!container || !src) return;
    container.innerHTML = '';

    if (isAsciinemaOrgUrl(src)) {
      const id = extractAsciinemaId(src);
      if (!id) return;
      const script = document.createElement('script');
      script.src = `https://asciinema.org/a/${id}.js`;
      script.async = true;
      script.id = `asciicast-${id}`;
      // Map a few common options if provided
      if (options?.autoplay) script.setAttribute('data-autoplay', 'true');
      if (options?.preload) script.setAttribute('data-preload', 'true');
      if (options?.speed) script.setAttribute('data-speed', String(options.speed));
      if (options?.loop) script.setAttribute('data-loop', 'true');
      if (options?.theme) script.setAttribute('data-theme', String(options.theme));
      container.appendChild(script);
      return;
    }

    if (!playerLib) return;
    playerLib.create(src, container, options);
  }

  onMount(async () => {
    await ensurePlayerLibLoaded();
    renderPlayer();
  });

  $: if (playerLib && container && src) {
    // Re-render when src or options change
    renderPlayer();
  }
</script>

<div bind:this={container}></div>

