import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	optimizeDeps: {
		exclude: ['@lucide/svelte']
	},
	server: {
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://localhost:9000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: (process.env.BACKEND_URL || 'http://localhost:9000').replace(/^http/, 'ws'),
        ws: true,
        changeOrigin: true,
        secure: false
      }
    }
  }
});
