<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  export let src: string;
  export let options: { fit?: string; autoplay?: boolean; loop?: boolean; speed?: number } | undefined;

  let container: HTMLDivElement;
  let playerElement: HTMLElement | null = null;
  let disposed = false;

  function ensureAssetsLoaded(): Promise<void> {
    return new Promise((resolve) => {
      if (typeof window === 'undefined') return resolve();

      const cssId = 'asciinema-player-css';
      const jsId = 'asciinema-player-js';

      if (!document.getElementById(cssId)) {
        const link = document.createElement('link');
        link.id = cssId;
        link.rel = 'stylesheet';
        link.href = 'https://cdn.jsdelivr.net/npm/asciinema-player@latest/dist/bundle/asciinema-player.css';
        document.head.appendChild(link);
      }

      const maybeResolve = () => {
        if ((customElements as any)?.get?.('asciinema-player')) {
          resolve();
        }
      };

      if (!document.getElementById(jsId)) {
        const script = document.createElement('script');
        script.id = jsId;
        script.src = 'https://cdn.jsdelivr.net/npm/asciinema-player@latest/dist/bundle/asciinema-player.min.js';
        script.async = true;
        script.onload = () => maybeResolve();
        document.body.appendChild(script);
      }

      const checkInterval = setInterval(() => {
        if ((customElements as any)?.get?.('asciinema-player')) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 50);
    });
  }

  function isAsciinemaOrg(url: string): boolean {
    try {
      const u = new URL(url);
      return u.hostname.includes('asciinema.org') && /\/a\//.test(u.pathname);
    } catch {
      return false;
    }
  }

  function getAsciinemaId(url: string): string | null {
    try {
      const u = new URL(url);
      const match = u.pathname.match(/\/a\/([A-Za-z0-9_-]+)/);
      if (match && match[1]) return match[1];
      const castMatch = u.pathname.match(/\/a\/([A-Za-z0-9_-]+)\.cast$/);
      if (castMatch && castMatch[1]) return castMatch[1];
      return null;
    } catch {
      return null;
    }
  }

  function mountPlayer() {
    if (!container || !src) return;
    container.innerHTML = '';

    if (isAsciinemaOrg(src)) {
      const id = getAsciinemaId(src);
      if (id) {
        const script = document.createElement('script');
        script.id = `asciicast-${id}`;
        script.src = `https://asciinema.org/a/${id}.js`;
        script.async = true;
        if (options?.autoplay) script.setAttribute('data-autoplay', 'true');
        if (options?.loop) script.setAttribute('data-loop', 'true');
        if (typeof options?.speed === 'number') script.setAttribute('data-speed', String(options.speed));
        // Let the site auto-size width; player supports data-size or data-cols/rows
        container.appendChild(script);
        playerElement = script as unknown as HTMLElement;
        return;
      }
    }

    const el = document.createElement('asciinema-player');
    el.setAttribute('src', src);
    if (options?.fit) el.setAttribute('fit', String(options.fit));
    if (options?.autoplay) el.setAttribute('autoplay', 'true');
    if (options?.loop) el.setAttribute('loop', 'true');
    if (typeof options?.speed === 'number') el.setAttribute('speed', String(options.speed));
    container.appendChild(el);
    playerElement = el;
  }

  onMount(async () => {
    // Only load custom-element assets when not embedding asciinema.org script
    if (!isAsciinemaOrg(src)) {
      await ensureAssetsLoaded();
    }
    if (!disposed) mountPlayer();
  });

  onDestroy(() => {
    disposed = true;
    if (playerElement && playerElement.parentNode) {
      playerElement.parentNode.removeChild(playerElement);
    }
    playerElement = null;
  });
</script>

<div bind:this={container} class="w-full"></div>


