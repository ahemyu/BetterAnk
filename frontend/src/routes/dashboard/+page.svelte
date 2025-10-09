<script lang="ts">
	import { onMount } from 'svelte';
	import { apiGet, apiPost, apiDelete } from '$lib/api';
	import { logout, isAuthenticated } from '$lib/auth.svelte';
	import { goto } from '$app/navigation';

	interface Deck {
		id: number;
		name: string;
		description: string;
	}

	interface User {
		username: string;
	}

	let user = $state<User | null>(null);
	let decks = $state<Deck[]>([]);
	let showCreateModal = $state(false);
	let deckName = $state('');
	let deckDescription = $state('');

	async function loadUser() {
		try {
			user = await apiGet('/me');
		} catch (err) {
			console.error('Failed to load user:', err);
			logout();
			goto('/login');
		}
	}

	async function loadDecks() {
		try {
			decks = await apiGet('/decks');
		} catch (err) {
			console.error('Failed to load decks:', err);
		}
	}

	async function handleCreateDeck(event: Event) {
		event.preventDefault();
		try {
			const newDeck = await apiPost('/decks', { name: deckName, description: deckDescription });
			decks = [...decks, newDeck];
			deckName = '';
			deckDescription = '';
			showCreateModal = false;
		} catch (err) {
			console.error('Failed to create deck:', err);
		}
	}

	async function handleDeleteDeck(deckId: number) {
		try {
			await apiDelete(`/decks/${deckId}`);
			decks = decks.filter((d) => d.id !== deckId);
		} catch (err) {
			console.error('Failed to delete deck:', err);
		}
	}

	function handleLogout() {
		logout();
		goto('/login');
	}

	function closeModal() {
		showCreateModal = false;
		deckName = '';
		deckDescription = '';
	}

	function handleModalClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			closeModal();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && showCreateModal) {
			closeModal();
		}
	}

	onMount(async () => {
		if (!isAuthenticated()) {
			goto('/login');
			return;
		}

		await loadUser();
		await loadDecks();
	});
</script>

<svelte:head>
	<title>Dashboard - BetterAnk</title>
</svelte:head>

<svelte:window onkeydown={handleKeydown} />

<div class="bg-gray-100 min-h-screen">
	<div class="container mx-auto p-4">
		<div class="flex justify-between items-center mb-6">
			<h1 class="text-3xl font-bold">
				{user ? `Welcome, ${user.username}!` : 'Loading...'}
			</h1>
			<button
				onclick={handleLogout}
				class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
			>
				Log out
			</button>
		</div>

		<button
			onclick={() => (showCreateModal = true)}
			class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4"
		>
			Create new Deck
		</button>

		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			<ul class="space-y-2">
				{#each decks as deck (deck.id)}
					<li class="bg-white p-4 rounded-lg shadow flex justify-between items-center">
						<a href="/deck/{deck.id}" class="text-blue-500 hover:underline flex-1">
							{deck.name}
						</a>
						<button
							onclick={() => handleDeleteDeck(deck.id)}
							class="text-red-500 hover:text-red-700 ml-4 cursor-pointer"
							aria-label="Delete deck"
						>
							❌
						</button>
					</li>
				{/each}
			</ul>
		</div>
	</div>
</div>

{#if showCreateModal}
	<div
		onclick={handleModalClick}
		class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full"
	>
		<div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
			<div class="mt-3 text-center">
				<h2 class="text-lg leading-6 font-medium text-gray-900">Create Deck</h2>
				<form onsubmit={handleCreateDeck} class="mt-2 space-y-4">
					<input
						type="text"
						placeholder="Deck Name"
						bind:value={deckName}
						required
						class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					<input
						type="text"
						placeholder="Deck Description"
						bind:value={deckDescription}
						class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					<div class="items-center gap-2">
						<button
							type="submit"
							class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
						>
							Create Deck
						</button>
						<button
							type="button"
							onclick={closeModal}
							class="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mt-2"
						>
							Cancel
						</button>
					</div>
				</form>
			</div>
		</div>
	</div>
{/if}
