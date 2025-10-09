<script lang="ts">
	import { register, login } from '$lib/api';
	import { setAuthToken } from '$lib/auth.svelte';
	import { goto } from '$app/navigation';

	let email = $state('');
	let username = $state('');
	let password = $state('');
	let error = $state('');

	async function handleSubmit(event: Event) {
		event.preventDefault();
		error = '';

		try {
			// Register the user
			await register(username, password, email);

			// Automatically log them in
			const loginData = await login(username, password);
			setAuthToken(loginData.access_token);
			goto('/dashboard');
		} catch (err) {
			console.error('Registration failed:', err);
			error = 'Registration failed. Please try again.';
		}
	}
</script>

<svelte:head>
	<title>Register - BetterAnk</title>
</svelte:head>

<div class="bg-gray-100 flex items-center justify-center h-screen">
	<div class="bg-white p-8 rounded-lg shadow-md w-full max-w-sm">
		<h2 class="text-2xl font-bold mb-6 text-center">Register</h2>
		<form onsubmit={handleSubmit} class="space-y-4">
			<input
				type="email"
				placeholder="Enter your email"
				bind:value={email}
				required
				maxlength="100"
				class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
			<input
				type="text"
				placeholder="Enter username"
				bind:value={username}
				required
				maxlength="50"
				class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
			<input
				type="password"
				placeholder="Type in your password"
				bind:value={password}
				required
				maxlength="100"
				class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
			{#if error}
				<p class="text-red-500 text-sm">{error}</p>
			{/if}
			<button
				type="submit"
				class="w-full bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg"
			>
				Register
			</button>
		</form>
		<p class="text-center text-sm text-gray-600 mt-4">
			Already have an account? <a href="/login" class="text-blue-500 hover:underline"
				>Login here</a
			>
		</p>
	</div>
</div>
