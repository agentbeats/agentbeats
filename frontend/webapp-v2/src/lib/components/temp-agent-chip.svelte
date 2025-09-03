<!-- Simple agent chip component -->
<script lang="ts">
  export let name: string;
  export let isSystem = false;

  // Determine color based on agent name or if it's a system log
  function getColor(name: string, isSystem: boolean): { bg: string; text: string } {
    if (isSystem) {
      return { bg: 'bg-muted', text: 'text-muted-foreground' };
    }
    
    // Simple hash function to get consistent colors
    const hash = name.split('').reduce((acc, char) => char.charCodeAt(0) + ((acc << 5) - acc), 0);
    const colors = [
      { bg: 'bg-blue-100', text: 'text-blue-700' },
      { bg: 'bg-green-100', text: 'text-green-700' },
      { bg: 'bg-purple-100', text: 'text-purple-700' },
      { bg: 'bg-orange-100', text: 'text-orange-700' },
      { bg: 'bg-pink-100', text: 'text-pink-700' },
    ];
    return colors[Math.abs(hash) % colors.length];
  }

  $: color = getColor(name, isSystem);
</script>

<div class="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium {color.bg} {color.text}">
  {name}
</div> 