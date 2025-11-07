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
		description: string;
		parent_deck_id?: number;
	}

	interface DeckTree {
		id: number;
		name: string;
		description: string;
		parent_deck_id?: number;
		children: DeckTree[];
	}

	interface User {
		username: string;
	}

	let user = $state<User | null>(null);
	let deckTree = $state<DeckTree[]>([]);
	let expandedDecks = $state<Set<number>>(new Set());
	let showCreateModal = $state(false);
	let deckName = $state('');
	let deckDescription = $state('');
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
			deckTree = await apiGet('/decks/tree/all');
			// Expand all decks by default
			expandAllDecks(deckTree);
		} catch (err) {
			console.error('Failed to load decks:', err);
			errorMessage = 'Failed to load decks. Please refresh the page.';
		} finally {
			isLoadingDecks = false;
		}
	}

	function expandAllDecks(tree: DeckTree[]) {
		tree.forEach(deck => {
			expandedDecks.add(deck.id);
			if (deck.children && deck.children.length > 0) {
				expandAllDecks(deck.children);
			}
		});
	}

	function toggleDeckExpansion(deckId: number) {
		if (expandedDecks.has(deckId)) {
			expandedDecks.delete(deckId);
		} else {
			expandedDecks.add(deckId);
		}
		expandedDecks = expandedDecks; // Trigger reactivity
	}

	async function handleCreateDeck(event: Event) {
		event.preventDefault();
		try {
			await apiPost('/decks', { name: deckName, description: deckDescription });
			deckName = '';
			deckDescription = '';
			showCreateModal = false;
			// Reload the tree to show the new deck
			await loadDecks();
		} catch (err) {
			console.error('Failed to create deck:', err);
		}
	}

	async function handleDeleteDeck(deckId: number, hasChildren: boolean) {
		const warningMessage = hasChildren
			? 'Are you sure you want to delete this deck? All subdecks and flashcards will be permanently deleted.'
			: 'Are you sure you want to delete this deck? All flashcards will be permanently deleted.';

		if (!confirm(warningMessage)) {
			return;
		}

		try {
			await apiDelete(`/decks/${deckId}`);
			// Reload the tree to reflect deletion
			await loadDecks();
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

	function handleKeydown(event: KeyboardEvent) {
		// Ignore if user is typing in an editable element
		if (isEditableElement(event.target)) {
			if (isEscape(event)) {
				event.preventDefault();
				if (showCreateModal) {
					closeModal();
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
			} else if (showKeyboardHelp) {
				showKeyboardHelp = false;
			}
		}

		// Navigation keybindings (only when modal is not open)
		if (!showCreateModal) {
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
		<div class="bg-white rounded-lg shadow p-4">
			{#if deckTree.length === 0}
				<p class="text-gray-500 text-center py-4">No decks yet. Create your first deck to get started!</p>
			{:else}
				{#snippet renderDeckTree(decks: DeckTree[], level: number)}
					<ul class="space-y-1">
						{#each decks as deck (deck.id)}
							<li>
								<div class="flex items-center py-2 hover:bg-gray-50 rounded" style="padding-left: {level * 1.5}rem">
									{#if deck.children && deck.children.length > 0}
										<button
											onclick={() => toggleDeckExpansion(deck.id)}
											class="mr-2 text-gray-600 hover:text-gray-800 w-6 h-6 flex items-center justify-center"
											aria-label={expandedDecks.has(deck.id) ? 'Collapse' : 'Expand'}
										>
											{expandedDecks.has(deck.id) ? '▼' : '▶'}
										</button>
									{:else}
										<span class="mr-2 w-6"></span>
									{/if}

									<span class="mr-2 text-xl">{deck.children && deck.children.length > 0 ? '📁' : '📄'}</span>

									<a
										href="/deck/{deck.id}"
										class="text-blue-500 hover:underline flex-1 truncate"
									>
										{deck.name}
									</a>

									<button
										onclick={() => handleDeleteDeck(deck.id, deck.children.length > 0)}
										class="text-red-500 hover:text-red-700 ml-4 cursor-pointer flex-shrink-0 px-2"
										aria-label="Delete deck"
									>
										❌
									</button>
								</div>

								{#if deck.children && deck.children.length > 0 && expandedDecks.has(deck.id)}
									{@render renderDeckTree(deck.children, level + 1)}
								{/if}
							</li>
						{/each}
					</ul>
				{/snippet}

				{@render renderDeckTree(deckTree, 0)}
			{/if}
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

<!-- Keyboard Shortcuts Help -->
<KeyboardShortcutsHelp bind:show={showKeyboardHelp} sections={keyboardShortcuts} />
