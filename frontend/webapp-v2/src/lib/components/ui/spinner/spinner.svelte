<script lang="ts">
  interface $$Props {
    size?: 'sm' | 'md' | 'lg';
    color?: 'gray' | 'blue' | 'purple' | 'primary';
    centered?: boolean;
  }

  let { size = 'md', color = 'gray', centered = false } = $props();

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6', 
    lg: 'h-8 w-8'
  };

  const colorClasses = {
    gray: 'border-muted-foreground',
    blue: 'border-blue-600',
    purple: 'border-purple-600',
    primary: 'border-primary'
  };

  const containerClasses = centered ? 'mx-auto mb-4' : '';
</script>

<div class="animate-spin rounded-full border-b-2 {sizeClasses[size as keyof typeof sizeClasses]} {colorClasses[color as keyof typeof colorClasses]} {containerClasses}"></div> 