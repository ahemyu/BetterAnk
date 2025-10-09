import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			'/login': {
				target: process.env.VITE_API_URL || 'http://localhost:8080',
				changeOrigin: true
			},
			'/logout': {
				target: process.env.VITE_API_URL || 'http://localhost:8080',
				changeOrigin: true
			},
			'/register': {
				target: process.env.VITE_API_URL || 'http://localhost:8080',
				changeOrigin: true
			},
			'/me': {
				target: process.env.VITE_API_URL || 'http://localhost:8080',
				changeOrigin: true
			},
			'/decks': {
				target: process.env.VITE_API_URL || 'http://localhost:8080',
				changeOrigin: true
			},
			'/flashcards': {
				target: process.env.VITE_API_URL || 'http://localhost:8080',
				changeOrigin: true
			},
			'/llm': {
				target: process.env.VITE_API_URL || 'http://localhost:8080',
				changeOrigin: true
			}
		}
	}
});
