<script lang="ts">
	import { login } from '$lib/api';
	import { setAuthToken } from '$lib/auth.svelte';
	import { goto } from '$app/navigation';

	let username = $state('');
	let password = $state('');
	let error = $state('');

	async function handleSubmit(event: Event) {
		event.preventDefault();
		error = '';

		try {
			const data = await login(username, password);
			setAuthToken(data.access_token);
			goto('/dashboard');
		} catch (err) {
			console.error('Login failed:', err);
			error = 'Login failed. Please check your credentials.';
		}
	}
</script>

<svelte:head>
	<title>Login - BetterAnk</title>
</svelte:head>

<div class="bg-gray-100 flex items-center justify-center h-screen">
	<div class="bg-white p-8 rounded-lg shadow-md w-full max-w-sm">
		<h2 class="text-2xl font-bold mb-6 text-center">Login</h2>
		<form onsubmit={handleSubmit} class="space-y-4">
			<input
				type="text"
				placeholder="Enter username"
				bind:value={username}
				required
				class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
			<input
				type="password"
				placeholder="Type in your password"
				bind:value={password}
				required
				class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
			{#if error}
				<p class="text-red-500 text-sm">{error}</p>
			{/if}
			<button
				type="submit"
				class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg"
			>
				Login
			</button>
		</form>
		<p class="text-center text-sm text-gray-600 mt-4">
			Don't have an account? <a href="/register" class="text-blue-500 hover:underline"
				>Register here</a
			>
		</p>
	</div>
</div>
