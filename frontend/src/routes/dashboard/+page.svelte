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
		parent_deck_id?: number | null;
	}

	interface DeckWithSubdecks extends Deck {
		subdecks?: Deck[];
	}

	interface User {
		username: string;
	}

	let user = $state<User | null>(null);
	let decks = $state<DeckWithSubdecks[]>([]);
	let showCreateModal = $state(false);
	let deckName = $state('');
	let deckDescription = $state('');
	let parentDeckId = $state<number | null>(null);
	let errorMessage = $state('');
	let isLoadingUser = $state(true);
	let isLoadingDecks = $state(true);
	let deckNameInput: HTMLInputElement;

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
			const topLevelDecks = await apiGet('/decks');

			// Load subdecks for each deck
			const decksWithSubdecks = await Promise.all(
				topLevelDecks.map(async (deck: Deck) => {
					try {
						const subdecks = await apiGet(`/decks/${deck.id}/subdecks`);
						return { ...deck, subdecks };
					} catch (err) {
						console.error(`Failed to load subdecks for deck ${deck.id}:`, err);
						return { ...deck, subdecks: [] };
					}
				})
			);

			decks = decksWithSubdecks;
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
			const newDeck = await apiPost('/decks', {
				name: deckName,
				description: deckDescription,
				parent_deck_id: parentDeckId
			});

			if (parentDeckId) {
				// If creating a subdeck, reload decks to update the subdeck list
				await loadDecks();
			} else {
				// If creating a top-level deck, add it to the list with empty subdecks
				decks = [...decks, { ...newDeck, subdecks: [] }];
			}

			deckName = '';
			deckDescription = '';
			parentDeckId = null;
			showCreateModal = false;
		} catch (err) {
			console.error('Failed to create deck:', err);
			alert('Failed to create deck. Please try again.');
		}
	}

	async function handleDeleteDeck(deckId: number) {
		if (!confirm('Are you sure you want to delete this deck? All flashcards will be permanently deleted.')) {
			return;
		}

		try {
			await apiDelete(`/decks/${deckId}`);

			// Check if this is a top-level deck or a subdeck
			const isTopLevel = decks.some(d => d.id === deckId);

			if (isTopLevel) {
				// Remove from top-level decks
				decks = decks.filter((d) => d.id !== deckId);
			} else {
				// Remove from subdecks - find parent and update its subdecks array
				decks = decks.map(deck => {
					if (deck.subdecks && deck.subdecks.some(s => s.id === deckId)) {
						return {
							...deck,
							subdecks: deck.subdecks.filter(s => s.id !== deckId)
						};
					}
					return deck;
				});
			}
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
		parentDeckId = null;
	}

	function openCreateSubdeckModal(parentId: number) {
		parentDeckId = parentId;
		showCreateModal = true;
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

	// Auto-focus the deck name input when modal opens
	$effect(() => {
		if (showCreateModal && deckNameInput) {
			deckNameInput.focus();
		}
	});

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
			{#each decks as deck (deck.id)}
				<div class="bg-white rounded-lg shadow">
					<!-- Parent Deck -->
					<div class="p-4 flex justify-between items-center border-b border-gray-200">
						<a href="/deck/{deck.id}" class="text-blue-600 hover:underline flex-1 truncate font-medium text-lg">
							{deck.name}
						</a>
						<div class="flex items-center gap-2">
							<button
								onclick={() => openCreateSubdeckModal(deck.id)}
								class="text-green-600 hover:text-green-700 px-3 py-1 rounded-md hover:bg-green-50 text-sm font-medium transition-colors"
								aria-label="Add subdeck"
								title="Add subdeck"
							>
								+ Subdeck
							</button>
							<button
								onclick={() => handleDeleteDeck(deck.id)}
								class="text-red-500 hover:text-red-700 cursor-pointer"
								aria-label="Delete deck"
								title="Delete deck"
							>
								❌
							</button>
						</div>
					</div>

					<!-- Subdecks -->
					{#if deck.subdecks && deck.subdecks.length > 0}
						<div class="bg-gray-50 p-2">
							{#each deck.subdecks as subdeck (subdeck.id)}
								<div class="ml-6 p-3 bg-white rounded-md shadow-sm mb-2 flex justify-between items-center border-l-4 border-blue-400">
									<a href="/deck/{subdeck.id}" class="text-blue-500 hover:underline flex-1 truncate">
										{subdeck.name}
									</a>
									<button
										onclick={() => handleDeleteDeck(subdeck.id)}
										class="text-red-500 hover:text-red-700 ml-4 cursor-pointer"
										aria-label="Delete subdeck"
										title="Delete subdeck"
									>
										❌
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
				<h2 class="text-lg leading-6 font-medium text-gray-900">
					{parentDeckId ? 'Create Subdeck' : 'Create Deck'}
				</h2>
				{#if parentDeckId}
					<p class="text-sm text-gray-600 mt-1">
						Creating a subdeck under "{decks.find((d) => d.id === parentDeckId)?.name || 'Unknown'}"
					</p>
				{/if}
				<form onsubmit={handleCreateDeck} class="mt-2 space-y-4">
					<input
						bind:this={deckNameInput}
						type="text"
						placeholder={parentDeckId ? 'Subdeck Name' : 'Deck Name'}
						bind:value={deckName}
						required
						maxlength="100"
						class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					<input
						type="text"
						placeholder={parentDeckId ? 'Subdeck Description' : 'Deck Description'}
						bind:value={deckDescription}
						maxlength="500"
						class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					<div class="items-center gap-2">
						<button
							type="submit"
							class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
						>
							{parentDeckId ? 'Create Subdeck' : 'Create Deck'}
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
