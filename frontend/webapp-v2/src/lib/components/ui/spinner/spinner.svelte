<script lang="ts">
  interface $$Props {
    size?: 'sm' | 'md' | 'lg';
    color?: 'gray' | 'blue' | 'purple' | 'primary';
  }

  let { size = 'md', color = 'gray' } = $props();

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6', 
    lg: 'h-8 w-8'
  };

  const colorClasses = {
    gray: 'border-gray-900',
    blue: 'border-blue-600',
    purple: 'border-purple-600',
    primary: 'border-primary'
  };
</script>

<div class="animate-spin rounded-full border-b-2 {sizeClasses[size as keyof typeof sizeClasses]} {colorClasses[color as keyof typeof colorClasses]}"></div> 