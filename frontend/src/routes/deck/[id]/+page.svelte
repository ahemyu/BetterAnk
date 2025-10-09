<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { apiGet, apiPost, apiPut, apiDelete } from '$lib/api';
	import { isAuthenticated } from '$lib/auth.svelte';

	interface Flashcard {
		id: number;
		front: string;
		back: string;
		next_review_at: string;
	}

	interface Deck {
		id: number;
		name: string;
		description: string;
	}

	interface GeneratedFlashcard {
		front: string;
		back: string;
		editing?: boolean;
	}

	let deckId = $derived($page.params.id);
	let deck = $state<Deck | null>(null);
	let allFlashcards = $state<Flashcard[]>([]);
	let dueFlashcards = $state<Flashcard[]>([]);
	let showAddModal = $state(false);
	let showAllFlashcardsModal = $state(false);
	let activeTab = $state<'manual' | 'llm'>('llm');
	let llmSubTab = $state<'text' | 'image'>('image');

	// Manual add form
	let manualFront = $state('');
	let manualBack = $state('');

	// LLM generation
	let llmText = $state('');
	let llmNumCards = $state(1);
	let llmImageFile = $state<File | null>(null);
	let imagePreview = $state('');
	let generatedFlashcards = $state<GeneratedFlashcard[]>([]);
	let isGenerating = $state(false);

	// Edit mode for flashcards table
	let editingFlashcardId = $state<number | null>(null);
	let editFront = $state('');
	let editBack = $state('');

	async function loadDeck() {
		try {
			deck = await apiGet(`/decks/${deckId}`);
		} catch (err) {
			console.error('Failed to load deck:', err);
		}
	}

	async function loadFlashcards() {
		try {
			allFlashcards = await apiGet(`/decks/${deckId}/flashcards`);
			dueFlashcards = await apiGet(`/decks/${deckId}/flashcards?due=true`);
		} catch (err) {
			console.error('Failed to load flashcards:', err);
		}
	}

	async function handleAddManualCard(event: Event) {
		event.preventDefault();
		try {
			await apiPost('/flashcards', {
				front: manualFront,
				back: manualBack,
				deck_id: parseInt(deckId)
			});
			manualFront = '';
			manualBack = '';
			await loadFlashcards();
			if (showAllFlashcardsModal) {
				await loadFlashcards();
			}
		} catch (err) {
			console.error('Failed to add flashcard:', err);
		}
	}

	async function handleGenerateFromText(event: Event) {
		event.preventDefault();
		isGenerating = true;
		try {
			const response = await apiPost('/llm/generate-from-text', {
				text: llmText,
				num_cards: llmNumCards,
				deck_id: parseInt(deckId)
			});
			generatedFlashcards = response.flashcards;
		} catch (err) {
			console.error('Failed to generate flashcards:', err);
			alert((err as Error).message || 'Failed to generate flashcards');
		} finally {
			isGenerating = false;
		}
	}

	async function handleGenerateFromImage(event: Event) {
		event.preventDefault();
		if (!llmImageFile) return;

		isGenerating = true;
		try {
			const base64 = await fileToBase64(llmImageFile);
			const base64Data = base64.split(',')[1];

			const response = await apiPost('/llm/generate-from-image', {
				image_base64: base64Data,
				num_cards: llmNumCards,
				deck_id: parseInt(deckId)
			});
			generatedFlashcards = response.flashcards;
		} catch (err) {
			console.error('Failed to generate flashcards:', err);
			alert((err as Error).message || 'Failed to generate flashcards');
		} finally {
			isGenerating = false;
		}
	}

	async function handleSaveGeneratedCards() {
		try {
			const count = generatedFlashcards.length;
			for (const card of generatedFlashcards) {
				await apiPost('/flashcards', {
					front: card.front,
					back: card.back,
					deck_id: parseInt(deckId)
				});
			}
			generatedFlashcards = [];
			showAddModal = false;
			resetModalState();
			await loadFlashcards();
			alert(`Successfully saved ${count} flashcard${count !== 1 ? 's' : ''}!`);
		} catch (err) {
			console.error('Failed to save flashcards:', err);
			alert('Failed to save some flashcards');
		}
	}

	function fileToBase64(file: File): Promise<string> {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => resolve(reader.result as string);
			reader.onerror = reject;
			reader.readAsDataURL(file);
		});
	}

	function handleImageChange(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files[0]) {
			llmImageFile = target.files[0];
			const reader = new FileReader();
			reader.onload = (e) => {
				imagePreview = e.target?.result as string;
			};
			reader.readAsDataURL(llmImageFile);
		}
	}

	async function handleDeleteFlashcard(id: number) {
		try {
			await apiDelete(`/flashcards/${id}`);
			await loadFlashcards();
		} catch (err) {
			console.error('Failed to delete flashcard:', err);
		}
	}

	function startEditing(card: Flashcard) {
		editingFlashcardId = card.id;
		editFront = card.front;
		editBack = card.back;
	}

	async function saveEdit() {
		if (editingFlashcardId === null) return;
		try {
			await apiPut(`/flashcards/${editingFlashcardId}`, {
				front: editFront,
				back: editBack
			});
			editingFlashcardId = null;
			await loadFlashcards();
		} catch (err) {
			console.error('Failed to update flashcard:', err);
		}
	}

	function cancelEdit() {
		editingFlashcardId = null;
	}

	function resetModalState() {
		activeTab = 'llm';
		llmSubTab = 'text';
		manualFront = '';
		manualBack = '';
		llmText = '';
		llmImageFile = null;
		imagePreview = '';
		generatedFlashcards = [];
	}

	function closeAddModal() {
		showAddModal = false;
		resetModalState();
	}

	function handleModalClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			if (showAddModal) closeAddModal();
			if (showAllFlashcardsModal) showAllFlashcardsModal = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			if (showAddModal) closeAddModal();
			if (showAllFlashcardsModal) showAllFlashcardsModal = false;
		}
	}

	onMount(async () => {
		if (!isAuthenticated()) {
			goto('/login');
			return;
		}

		await loadDeck();
		await loadFlashcards();
	});
</script>

<svelte:head>
	<title>{deck?.name || 'Deck'} - BetterAnk</title>
</svelte:head>

<svelte:window onkeydown={handleKeydown} />

<div class="bg-gray-100 min-h-screen">
	<div class="container mx-auto p-4">
		<h1 class="text-3xl font-bold mb-4">{deck?.name || 'Loading...'}</h1>
		<div class="flex items-center space-x-4 mb-4">
			<p class="text-lg">{allFlashcards.length} total cards</p>
			<p class="text-lg text-red-500">{dueFlashcards.length} due cards</p>
		</div>
		<div class="space-x-2 mb-4">
			<button
				onclick={() => goto(`/review/${deckId}`)}
				class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
			>
				Start Review
			</button>
			<button
				onclick={() => goto('/dashboard')}
				class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
			>
				Back to Decks
			</button>
			<button
				onclick={() => (showAddModal = true)}
				class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
			>
				Add New Flashcard
			</button>
			<button
				onclick={() => (showAllFlashcardsModal = true)}
				class="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded"
			>
				Show All Flashcards
			</button>
		</div>
	</div>
</div>

<!-- Add Flashcard Modal -->
{#if showAddModal}
	<div
		onclick={handleModalClick}
		class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full"
	>
		<div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
			<div class="mt-3">
				<h2 class="text-lg leading-6 font-medium text-gray-900 text-center">Add Flashcard</h2>

				<!-- Tab Navigation -->
				<div class="flex border-b border-gray-200 mt-4">
					<button
						type="button"
						onclick={() => (activeTab = 'manual')}
						class="flex-1 py-2 px-4 text-center border-b-2 {activeTab === 'manual'
							? 'border-blue-500 text-blue-600'
							: 'border-transparent text-gray-500'} hover:text-gray-700 font-medium"
					>
						Manual
					</button>
					<button
						type="button"
						onclick={() => (activeTab = 'llm')}
						class="flex-1 py-2 px-4 text-center border-b-2 {activeTab === 'llm'
							? 'border-blue-500 text-blue-600'
							: 'border-transparent text-gray-500'} hover:text-gray-700 font-medium"
					>
						Generate with AI
					</button>
				</div>

				<!-- Manual Tab Content -->
				{#if activeTab === 'manual'}
					<form onsubmit={handleAddManualCard} class="mt-4 space-y-4">
						<input
							type="text"
							placeholder="Front"
							bind:value={manualFront}
							required
							class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
						<input
							type="text"
							placeholder="Back"
							bind:value={manualBack}
							required
							class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
						<div class="space-y-2">
							<button
								type="submit"
								class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
							>
								Add Card
							</button>
							<button
								type="button"
								onclick={closeAddModal}
								class="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
							>
								Cancel
							</button>
						</div>
					</form>
				{/if}

				<!-- LLM Tab Content -->
				{#if activeTab === 'llm'}
					<div class="mt-4">
						<!-- Sub-tabs -->
						<div class="flex space-x-2 mb-4">
							<button
								type="button"
								onclick={() => (llmSubTab = 'text')}
								class="flex-1 py-2 px-4 rounded {llmSubTab === 'text'
									? 'bg-blue-500 text-white'
									: 'bg-gray-300 text-gray-800'} hover:opacity-80"
							>
								From Text
							</button>
							<button
								type="button"
								onclick={() => (llmSubTab = 'image')}
								class="flex-1 py-2 px-4 rounded {llmSubTab === 'image'
									? 'bg-blue-500 text-white'
									: 'bg-gray-300 text-gray-800'} hover:opacity-80"
							>
								From Image
							</button>
						</div>

						<!-- Text Generation Form -->
						{#if llmSubTab === 'text'}
							<form onsubmit={handleGenerateFromText} class="space-y-4">
								<textarea
									placeholder="Enter text to generate flashcards from..."
									bind:value={llmText}
									rows="6"
									required
									class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
								></textarea>
								<input
									type="number"
									placeholder="Number of cards"
									bind:value={llmNumCards}
									min="1"
									max="5"
									required
									class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
								<button
									type="submit"
									disabled={isGenerating}
									class="w-full bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
								>
									Generate Flashcards
								</button>
								<button
									type="button"
									onclick={closeAddModal}
									class="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
								>
									Cancel
								</button>
							</form>
						{/if}

						<!-- Image Generation Form -->
						{#if llmSubTab === 'image'}
							<form onsubmit={handleGenerateFromImage} class="space-y-4">
								<input
									type="file"
									accept="image/*"
									onchange={handleImageChange}
									required
									class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
								{#if imagePreview}
									<img
										src={imagePreview}
										alt="Preview"
										class="w-full max-h-48 object-contain border rounded"
									/>
								{/if}
								<input
									type="number"
									placeholder="Number of cards"
									bind:value={llmNumCards}
									min="1"
									max="5"
									required
									class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
								<button
									type="submit"
									disabled={isGenerating}
									class="w-full bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
								>
									Generate Flashcards
								</button>
								<button
									type="button"
									onclick={closeAddModal}
									class="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
								>
									Cancel
								</button>
							</form>
						{/if}

						<!-- Loading Spinner -->
						{#if isGenerating}
							<div class="mt-4 text-center">
								<svg
									class="animate-spin h-10 w-10 mx-auto text-blue-500"
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
								>
									<circle
										class="opacity-25"
										cx="12"
										cy="12"
										r="10"
										stroke="currentColor"
										stroke-width="4"
									></circle>
									<path
										class="opacity-75"
										fill="currentColor"
										d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
									></path>
								</svg>
								<p class="mt-2 text-gray-600">Generating flashcards...</p>
							</div>
						{/if}

						<!-- Generated Flashcards Preview -->
						{#if generatedFlashcards.length > 0 && !isGenerating}
							<div class="mt-4">
								<h3 class="text-md font-semibold mb-2">Generated Flashcards:</h3>
								<div class="space-y-2 max-h-64 overflow-y-auto">
									{#each generatedFlashcards as card, index}
										<div class="p-3 border rounded bg-gray-50">
											{#if card.editing}
												<div class="font-semibold text-sm text-gray-700 mb-2">
													Card {index + 1}
												</div>
												<div class="space-y-2">
													<div>
														<label class="text-xs text-gray-600">Front:</label>
														<input
															type="text"
															bind:value={card.front}
															class="w-full px-2 py-1 border rounded text-sm"
														/>
													</div>
													<div>
														<label class="text-xs text-gray-600">Back:</label>
														<textarea
															bind:value={card.back}
															rows="2"
															class="w-full px-2 py-1 border rounded text-sm"
														></textarea>
													</div>
													<div class="flex gap-2">
														<button
															onclick={() => (card.editing = false)}
															class="flex-1 bg-green-500 hover:bg-green-600 text-white text-xs font-bold py-1 px-2 rounded"
														>
															Save
														</button>
														<button
															onclick={() => (card.editing = false)}
															class="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 text-xs font-bold py-1 px-2 rounded"
														>
															Cancel
														</button>
													</div>
												</div>
											{:else}
												<div class="font-semibold text-sm text-gray-700">Card {index + 1}</div>
												<div class="mt-1 text-sm"><strong>Front:</strong> {card.front}</div>
												<div class="mt-1 text-sm"><strong>Back:</strong> {card.back}</div>
												<div class="flex gap-2 mt-2">
													<button
														onclick={() => (card.editing = true)}
														class="flex-1 bg-yellow-500 hover:bg-yellow-600 text-white text-xs font-bold py-1 px-2 rounded"
													>
														Edit
													</button>
													<button
														onclick={() => {
															generatedFlashcards = generatedFlashcards.filter((_, i) => i !== index);
														}}
														class="flex-1 bg-red-500 hover:bg-red-600 text-white text-xs font-bold py-1 px-2 rounded"
													>
														Discard
													</button>
												</div>
											{/if}
										</div>
									{/each}
								</div>
								<div class="mt-4 space-y-2">
									<button
										onclick={handleSaveGeneratedCards}
										class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
									>
										Save All Cards
									</button>
									<button
										onclick={() => (generatedFlashcards = [])}
										class="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
									>
										Discard All
									</button>
								</div>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<!-- Show All Flashcards Modal -->
{#if showAllFlashcardsModal}
	<div
		onclick={handleModalClick}
		class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full"
	>
		<div class="relative top-10 mx-auto p-5 border w-full max-w-6xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-hidden flex flex-col">
			<div class="flex-shrink-0">
				<h2 class="text-lg leading-6 font-medium text-gray-900 text-center mb-4">All Flashcards</h2>
			</div>
			<div class="overflow-auto flex-1">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50 sticky top-0">
						<tr>
							<th
								class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/3"
							>
								Front
							</th>
							<th
								class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/3"
							>
								Back
							</th>
							<th
								class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32"
							>
								Next Review
							</th>
							<th
								class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-40"
							>
								Actions
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each allFlashcards as card (card.id)}
							{#if editingFlashcardId === card.id}
								<tr>
									<td class="px-4 py-4">
										<textarea
											bind:value={editFront}
											rows="3"
											class="w-full px-2 py-1 border rounded-lg resize-y"
										></textarea>
									</td>
									<td class="px-4 py-4">
										<textarea
											bind:value={editBack}
											rows="3"
											class="w-full px-2 py-1 border rounded-lg resize-y"
										></textarea>
									</td>
									<td class="px-4 py-4 whitespace-nowrap text-sm">
										{new Date(card.next_review_at).toLocaleDateString()}
									</td>
									<td class="px-4 py-4 whitespace-nowrap space-x-1">
										<button
											onclick={saveEdit}
											class="bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-3 rounded text-sm"
										>
											Save
										</button>
										<button
											onclick={cancelEdit}
											class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-1 px-3 rounded text-sm"
										>
											Cancel
										</button>
									</td>
								</tr>
							{:else}
								<tr class="hover:bg-gray-50">
									<td class="px-4 py-4">
										<div class="max-h-24 overflow-y-auto overflow-x-auto text-sm break-words">
											{card.front}
										</div>
									</td>
									<td class="px-4 py-4">
										<div class="max-h-24 overflow-y-auto overflow-x-auto text-sm break-words">
											{card.back}
										</div>
									</td>
									<td class="px-4 py-4 whitespace-nowrap text-sm">
										{new Date(card.next_review_at).toLocaleDateString()}
									</td>
									<td class="px-4 py-4 whitespace-nowrap space-x-1">
										<button
											onclick={() => startEditing(card)}
											class="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-1 px-3 rounded text-sm"
										>
											Edit
										</button>
										<button
											onclick={() => handleDeleteFlashcard(card.id)}
											class="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-3 rounded text-sm"
										>
											Delete
										</button>
									</td>
								</tr>
							{/if}
						{/each}
					</tbody>
				</table>
			</div>
			<div class="mt-4 text-right flex-shrink-0">
				<button
					onclick={() => (showAllFlashcardsModal = false)}
					class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
				>
					Close
				</button>
			</div>
		</div>
	</div>
{/if}
