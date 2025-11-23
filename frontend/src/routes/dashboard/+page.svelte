<script lang="ts">
	import { onMount } from 'svelte';
	import { apiGet, apiPost, apiDelete } from '$lib/api';
	import { logout, isAuthenticated, setAuthenticated } from '$lib/auth.svelte';
	import { goto } from '$app/navigation';
	import { isEditableElement, isKey, isEscape } from '$lib/keyboard';
	import KeyboardShortcutsHelp from '$lib/components/KeyboardShortcutsHelp.svelte';

	interface Deck {
		id: number;
		name: string;
		description: string | null;
		parent_id: number | null;
	}

	type DeckNode = Deck & { subdecks: DeckNode[] };

	interface User {
		username: string;
	}

	let user = $state<User | null>(null);
	let decks = $state<Deck[]>([]);
	let showCreateModal = $state(false);
	let showSubdeckModal = $state(false);
	let deckName = $state('');
	let deckDescription = $state('');
	let subdeckName = $state('');
	let subdeckDescription = $state('');
	let parentDeckForSubdeck = $state<Deck | null>(null);
	let errorMessage = $state('');
	let isLoadingUser = $state(true);
	let isLoadingDecks = $state(true);

	// Keyboard shortcuts help modal
	let showKeyboardHelp = $state(false);
	const keyboardShortcuts = [
		{
			title: 'Actions',
			shortcuts: [{ key: 'C', description: 'Create new deck' }]
		},
		{
			title: 'Navigation',
			shortcuts: [{ key: 'Esc', description: 'Close modal' }]
		},
		{
			title: 'Help',
			shortcuts: [{ key: '?', description: 'Show keyboard shortcuts' }]
		}
	];

	function buildDeckTree(list: Deck[]): DeckNode[] {
		const map = new Map<number, DeckNode>();
		const roots: DeckNode[] = [];

		list.forEach((deck) => {
			map.set(deck.id, { ...deck, subdecks: [] });
		});

		map.forEach((node) => {
			if (node.parent_id !== null && node.parent_id !== undefined) {
				const parent = map.get(node.parent_id);
				if (parent) {
					parent.subdecks.push(node);
				} else {
					roots.push(node);
				}
			} else {
				roots.push(node);
			}
		});

		const sortByName = (a: DeckNode, b: DeckNode) => a.name.localeCompare(b.name);
		roots.sort(sortByName);
		map.forEach((node) => node.subdecks.sort(sortByName));

		return roots;
	}

	let deckTree = $derived(buildDeckTree(decks));

	async function loadUser() {
		isLoadingUser = true;
		try {
			user = await apiGet('/me');
			setAuthenticated(true);
		} catch (err) {
			console.error('Failed to load user:', err);
			await logout();
			goto('/login');
		} finally {
			isLoadingUser = false;
		}
	}

	async function loadDecks() {
		isLoadingDecks = true;
		try {
			errorMessage = '';
			decks = await apiGet('/decks');
		} catch (err) {
			console.error('Failed to load decks:', err);
			errorMessage = 'Failed to load decks. Please refresh the page.';
		} finally {
			isLoadingDecks = false;
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

	function openSubdeckModal(deck: Deck) {
		parentDeckForSubdeck = deck;
		subdeckName = '';
		subdeckDescription = '';
		showSubdeckModal = true;
	}

	function closeSubdeckModal() {
		showSubdeckModal = false;
		parentDeckForSubdeck = null;
		subdeckName = '';
		subdeckDescription = '';
	}

	async function handleCreateSubdeck(event: Event) {
		event.preventDefault();
		if (!parentDeckForSubdeck) return;
		try {
			await apiPost('/decks', {
				name: subdeckName,
				description: subdeckDescription,
				parent_id: parentDeckForSubdeck.id
			});
			await loadDecks();
			closeSubdeckModal();
		} catch (err) {
			console.error('Failed to create subdeck:', err);
			alert('Failed to create subdeck. Please try again.');
		}
	}

	async function handleDeleteDeck(deckId: number) {
		if (!confirm('Are you sure you want to delete this deck? All flashcards will be permanently deleted.')) {
			return;
		}

		try {
			await apiDelete(`/decks/${deckId}`);
			decks = decks.filter((d) => d.id !== deckId);
		} catch (err) {
			console.error('Failed to delete deck:', err);
			alert('Failed to delete deck. Please try again.');
		}
	}

	async function handleLogout() {
		await logout();
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

	function handleSubdeckModalClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			closeSubdeckModal();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		// Ignore if user is typing in an editable element
		if (isEditableElement(event.target)) {
			if (isEscape(event)) {
				event.preventDefault();
				if (showCreateModal) {
					closeModal();
				} else if (showSubdeckModal) {
					closeSubdeckModal();
				} else if (showKeyboardHelp) {
					showKeyboardHelp = false;
				}
			}
			return;
		}

		// Modal keybindings
		if (isEscape(event)) {
			event.preventDefault();
			if (showCreateModal) {
				closeModal();
			} else if (showSubdeckModal) {
				closeSubdeckModal();
			} else if (showKeyboardHelp) {
				showKeyboardHelp = false;
			}
		}

		// Navigation keybindings (only when modals are not open)
		if (!showCreateModal && !showSubdeckModal) {
			if (isKey(event, 'c')) {
				event.preventDefault();
				showCreateModal = true;
			} else if (event.key === '?') {
				event.preventDefault();
				showKeyboardHelp = true;
			}
		}
	}

	onMount(async () => {
		// Try to load user to check if authenticated
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
				{#if isLoadingUser}
					Loading...
				{:else}
					{user ? `Welcome, ${user.username}!` : 'Loading...'}
				{/if}
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
			Create new Deck <span class="text-xs opacity-75">(C)</span>
		</button>


		{#if errorMessage}
		<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
			{errorMessage}
		</div>
		{/if}

		{#if isLoadingDecks}
		<div class="text-center py-8">
			<svg class="animate-spin h-10 w-10 mx-auto text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
			</svg>
			<p class="mt-2 text-gray-600">Loading decks...</p>
		</div>
		{:else}
		<div class="space-y-3">
			{#each deckTree as deck (deck.id)}
				<div class="bg-white p-4 rounded-lg shadow">
					<div class="flex flex-wrap items-center justify-between gap-3">
						<div>
							<a href="/deck/{deck.id}" class="text-lg font-semibold text-blue-600 hover:underline block">
								{deck.name}
							</a>
							{#if deck.description}
								<p class="text-sm text-gray-500 line-clamp-2">{deck.description}</p>
							{/if}
						</div>
						<div class="flex gap-2">
							<button
								onclick={() => handleDeleteDeck(deck.id)}
								class="text-red-500 hover:text-red-700 font-semibold"
							>
								Delete
							</button>
							<button
								onclick={() => openSubdeckModal(deck)}
								class="bg-amber-500 hover:bg-amber-600 text-white font-bold px-3 py-1 rounded"
							>
								Create subdeck
							</button>
						</div>
					</div>

					{#if deck.subdecks.length > 0}
						<div class="mt-3 pl-6 border-l-2 border-dashed border-gray-200 space-y-2">
							{#each deck.subdecks as child}
								<div class="flex items-center justify-between bg-gray-50 rounded px-3 py-2">
									<div class="flex items-center gap-2">
										<span class="text-gray-400">├──</span>
										<a href="/deck/{child.id}" class="text-blue-600 hover:underline">
											{child.name}
										</a>
									</div>
									<button
										onclick={() => handleDeleteDeck(child.id)}
										class="text-sm text-red-500 hover:text-red-700"
									>
										Delete
									</button>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/each}
		</div>
		{/if}

	</div>
</div>

{#if showCreateModal}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
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
						maxlength="100"
						class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					<input
						type="text"
						placeholder="Deck Description"
						bind:value={deckDescription}
						maxlength="500"
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

{#if showSubdeckModal && parentDeckForSubdeck}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		onclick={handleSubdeckModalClick}
		class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full"
	>
		<div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
			<div class="mt-3 text-center">
				<h2 class="text-lg leading-6 font-medium text-gray-900">
					Create subdeck for “{parentDeckForSubdeck.name}”
				</h2>
				<form onsubmit={handleCreateSubdeck} class="mt-2 space-y-4">
					<input
						type="text"
						placeholder="Subdeck Name"
						bind:value={subdeckName}
						required
						maxlength="100"
						class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
					/>
					<input
						type="text"
						placeholder="Description (optional)"
						bind:value={subdeckDescription}
						maxlength="500"
						class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
					/>
					<div class="items-center gap-2">
						<button
							type="submit"
							class="w-full bg-amber-500 hover:bg-amber-600 text-white font-bold py-2 px-4 rounded"
						>
							Create Subdeck
						</button>
						<button
							type="button"
							onclick={closeSubdeckModal}
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

<!-- Keyboard Shortcuts Help -->
<KeyboardShortcutsHelp bind:show={showKeyboardHelp} sections={keyboardShortcuts} />
