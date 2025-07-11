import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	optimizeDeps: {
		exclude: ['@lucide/svelte']
	},
	server: {
    allowedHosts: ['nuggets.puppy9.com'],
    proxy: {
      '/api': {
        target: 'https://nuggets.puppy9.com',
        changeOrigin: true,
        secure: false // set to true if your server uses a valid SSL cert
      },
      '/ws': {
        target: 'wss://nuggets.puppy9.com',
        ws: true,
        changeOrigin: true,
        secure: false
      }
    }
  }
});
