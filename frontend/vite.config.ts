import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			'/login': 'http://localhost:8080',
			'/register': 'http://localhost:8080',
			'/me': 'http://localhost:8080',
			'/decks': 'http://localhost:8080',
			'/flashcards': 'http://localhost:8080',
			'/llm': 'http://localhost:8080'
		}
	}
});
