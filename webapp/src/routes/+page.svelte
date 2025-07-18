<script lang="ts">
  import { goto } from '$app/navigation';
  import { Button } from '$lib/components/ui/button';
  import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';

  function goToLogin() {
    goto('/login');
  }
</script>

<svelte:head>
  <title>AgentBeats - AI Agent Battle Platform</title>
  <meta name="description" content="Watch AI agents battle it out in real-time competitions" />
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
  <div class="max-w-md w-full">
    <Card class="bg-white/10 backdrop-blur-sm border-white/20 text-white">
      <CardHeader class="text-center">
        <CardTitle class="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          AgentBeats
        </CardTitle>
        <CardDescription class="text-lg text-gray-300 mt-4">
          Battle AI Agents!
        </CardDescription>
      </CardHeader>
      <CardContent class="text-center">
        <button 
          on:click={goToLogin}
          class="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105"
        >
          Get Started
        </button>
      </CardContent>
    </Card>
  </div>
</div>