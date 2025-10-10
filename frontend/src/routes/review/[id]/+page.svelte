<script lang="ts">
	import { onMount, onDestroy, untrack } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { apiGet, apiPost, apiPut, apiDelete } from '$lib/api';
	import { isAuthenticated } from '$lib/auth.svelte';
	import { isEditableElement, isKey, isShiftKey, isEscape, isEnter } from '$lib/keyboard';
	import KeyboardShortcutsHelp from '$lib/components/KeyboardShortcutsHelp.svelte';

	interface Flashcard {
		id: number;
		front: string;
		back: string;
		next_review_at: string;
	}

	let deckId = $derived($page.params.id);
	let reviewQueue = $state<Flashcard[]>([]);
	let currentIndex = $state(0);
	let showBack = $state(false);
	let isReviewFinished = $state(false);
	let startTime: Date | null = null;
	let timeInterval: ReturnType<typeof setInterval> | null = null;
	let elapsedSeconds = $state(0);
	let timerColor = $state('black');

	// Edit modal
	let showEditModal = $state(false);
	let editFront = $state('');
	let editBack = $state('');

	// Keyboard shortcuts help modal
	let showKeyboardHelp = $state(false);
	const keyboardShortcuts = [
		{
			title: 'Review Actions',
			shortcuts: [
				{ key: 'Enter', description: 'Show answer' },
				{ key: '1', description: 'Mark as Good' },
				{ key: '2', description: 'Mark as Mid' },
				{ key: '3', description: 'Mark as Bad' },
				{ key: 'E', description: 'Edit flashcard' },
				{ key: 'Shift+D', description: 'Delete flashcard' }
			]
		},
		{
			title: 'Navigation',
			shortcuts: [
				{ key: 'Z', description: 'Back to dashboard' },
				{ key: 'Esc', description: 'Close modal' }
			]
		},
		{
			title: 'Help',
			shortcuts: [{ key: '?', description: 'Show keyboard shortcuts' }]
		}
	];

	let currentFlashcard = $derived(reviewQueue[currentIndex]);

	async function loadDueFlashcards() {
		try {
			const flashcards = await apiGet(`/decks/${deckId}/flashcards?due=true`);
			reviewQueue = flashcards.sort(
				(a: Flashcard, b: Flashcard) =>
					new Date(a.next_review_at).getTime() - new Date(b.next_review_at).getTime()
			);
			isReviewFinished = reviewQueue.length === 0;
		} catch (err) {
			console.error('Failed to load flashcards:', err);
		}
	}

	function startTimer() {
		startTime = new Date();
		elapsedSeconds = 0;
		timerColor = 'black';
		timeInterval = setInterval(() => {
			if (startTime) {
				elapsedSeconds = Math.floor((new Date().getTime() - startTime.getTime()) / 1000);
			}
		}, 1000);
	}

	function stopTimer() {
		if (timeInterval) {
			clearInterval(timeInterval);
			timeInterval = null;
		}
		if (startTime) {
			elapsedSeconds = Math.floor((new Date().getTime() - startTime.getTime()) / 1000);
			if (elapsedSeconds <= 5) {
				timerColor = 'green';
			} else if (elapsedSeconds <= 10) {
				timerColor = 'goldenrod';
			} else {
				timerColor = 'red';
			}
		}
	}

	function handleShowAnswer() {
		stopTimer();
		showBack = true;
	}

	async function handleFeedback(feedback: 'good' | 'mid' | 'bad') {
		try {
			await apiPost(`/flashcards/${currentFlashcard.id}/review`, { feedback });
			currentIndex++;
			showBack = false;

			if (currentIndex >= reviewQueue.length) {
				isReviewFinished = true;
			} else {
				startTimer();
			}
		} catch (err) {
			console.error('Failed to submit feedback:', err);
		}
	}

	function handleEdit() {
		editFront = currentFlashcard.front;
		editBack = currentFlashcard.back;
		showEditModal = true;
	}

	async function handleDelete() {
		if (!confirm('Are you sure you want to delete this card?')) return;

		try {
			await apiDelete(`/flashcards/${currentFlashcard.id}`);
			reviewQueue = reviewQueue.filter((_, i) => i !== currentIndex);

			// Check if there are any cards remaining
			if (reviewQueue.length === 0) {
				// No cards left, mark review as finished
				isReviewFinished = true;
			} else if (currentIndex >= reviewQueue.length) {
				// Current index is out of bounds, move to the last card
				currentIndex = reviewQueue.length - 1;
				showBack = false;
				startTimer();
			} else {
				// Current index is still valid, continue with the next card at the same index
				showBack = false;
				startTimer();
			}
		} catch (err) {
			console.error('Failed to delete flashcard:', err);
		}
	}

	async function handleSaveEdit(event: Event) {
		event.preventDefault();
		try {
			const updated = await apiPut(`/flashcards/${currentFlashcard.id}`, {
				front: editFront,
				back: editBack
			});
			reviewQueue[currentIndex] = updated;
			showEditModal = false;
			showBack = false;
			startTimer();
		} catch (err) {
			console.error('Failed to update flashcard:', err);
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		// Ignore if user is typing in an editable element
		if (isEditableElement(event.target)) {
			if (isEscape(event)) {
				event.preventDefault();
				if (showEditModal) {
					showEditModal = false;
				} else if (showKeyboardHelp) {
					showKeyboardHelp = false;
				}
			}
			return;
		}

		// Review flow keybindings
		if (isEnter(event) && !showBack && !isReviewFinished) {
			event.preventDefault();
			handleShowAnswer();
		} else if (isEscape(event)) {
			event.preventDefault();
			if (showEditModal) {
				showEditModal = false;
			} else if (showKeyboardHelp) {
				showKeyboardHelp = false;
			}
		} else if (showBack && !showEditModal) {
			// Feedback keybindings
			if (event.key === '1') {
				event.preventDefault();
				handleFeedback('good');
			} else if (event.key === '2') {
				event.preventDefault();
				handleFeedback('mid');
			} else if (event.key === '3') {
				event.preventDefault();
				handleFeedback('bad');
			} else if (isKey(event, 'e')) {
				event.preventDefault();
				handleEdit();
			} else if (isShiftKey(event, 'd')) {
				// Require Shift+D for delete (destructive action)
				event.preventDefault();
				handleDelete();
			}
		}

		// Navigation keybindings
		if (isKey(event, 'z') && !showEditModal) {
			event.preventDefault();
			goto('/dashboard');
		}

		// Help modal
		if (event.key === '?' && !showEditModal) {
			event.preventDefault();
			showKeyboardHelp = true;
		}
	}

	onMount(async () => {
		if (!isAuthenticated()) {
			goto('/login');
			return;
		}

		await loadDueFlashcards();
		if (!isReviewFinished) {
			startTimer();
		}
	});

	onDestroy(() => {
		if (timeInterval) {
			clearInterval(timeInterval);
		}
		timeInterval = null;
		startTime = null;
	});

	// Reload review queue when deckId changes (route navigation)
	$effect(() => {
		// Access deckId to track it
		deckId;

		// Use untrack to prevent infinite loops
		untrack(() => {
			if (isAuthenticated()) {
				// Clean up existing timer
				if (timeInterval) {
					clearInterval(timeInterval);
					timeInterval = null;
				}
				startTime = null;
				showBack = false;
				currentIndex = 0;

				// Load new deck's flashcards
				loadDueFlashcards().then(() => {
					if (!isReviewFinished) {
						startTimer();
					}
				});
			}
		});
	});
</script>

<svelte:head>
	<title>Review - BetterAnk</title>
</svelte:head>

<svelte:window onkeydown={handleKeydown} />

<div class="bg-gray-100 flex items-center justify-center h-screen">
	{#if isReviewFinished}
		<div class="text-center">
			<p class="text-2xl font-bold mb-4">Congrats, you finished the review for this Deck!</p>
			<button
				onclick={() => goto('/dashboard')}
				class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
			>
				Back to Start Menu <span class="text-xs opacity-75">(Z)</span>
			</button>
		</div>
	{:else if currentFlashcard}
		<div class="w-full max-w-lg">
			<div class="bg-white p-8 rounded-lg shadow-md text-center">
				<p class="text-3xl">{currentFlashcard.front}</p>
				<div class="text-sm text-gray-500 mt-2" style="color: {timerColor}">
					{elapsedSeconds}s
				</div>
				<br />
				{#if !showBack}
					<button
						onclick={handleShowAnswer}
						class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
					>
						Show Answer <span class="text-xs opacity-75">(Enter)</span>
					</button>
				{/if}
			</div>

			{#if showBack}
				<br />
				<div class="bg-white p-8 rounded-lg shadow-md text-center">
					<p class="text-3xl">{currentFlashcard.back}</p>
					<div class="mt-4 space-x-2">
						<button
							onclick={() => handleFeedback('good')}
							class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
						>
							Good <span class="text-xs opacity-75">(1)</span>
						</button>
						<button
							onclick={() => handleFeedback('mid')}
							class="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded"
						>
							Mid <span class="text-xs opacity-75">(2)</span>
						</button>
						<button
							onclick={() => handleFeedback('bad')}
							class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
						>
							Bad <span class="text-xs opacity-75">(3)</span>
						</button>
					</div>
					<div class="mt-4 space-x-2">
						<button
							onclick={handleEdit}
							class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-1 px-2 rounded"
						>
							Edit <span class="text-xs opacity-75">(E)</span>
						</button>
						<button
							onclick={handleDelete}
							class="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded"
						>
							Delete <span class="text-xs opacity-75">(Shift+D)</span>
						</button>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<!-- Edit Modal -->
{#if showEditModal}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		onclick={(e) => e.target === e.currentTarget && (showEditModal = false)}
		class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full"
	>
		<div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
			<div class="mt-3">
				<h2 class="text-lg leading-6 font-medium text-gray-900 text-center">Edit Flashcard</h2>
				<form onsubmit={handleSaveEdit} class="mt-2 space-y-4">
					<div>
						<label for="edit-front" class="block text-sm font-medium text-gray-700">Front:</label>
						<textarea
							id="edit-front"
							bind:value={editFront}
							required
							maxlength="1000"
							rows="3"
							class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
						></textarea>
					</div>
					<div>
						<label for="edit-back" class="block text-sm font-medium text-gray-700">Back:</label>
						<textarea
							id="edit-back"
							bind:value={editBack}
							required
							maxlength="2000"
							rows="3"
							class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
						></textarea>
					</div>
					<button
						type="submit"
						class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
					>
						Save Changes
					</button>
				</form>
			</div>
		</div>
	</div>
{/if}

<!-- Keyboard Shortcuts Help -->
<KeyboardShortcutsHelp bind:show={showKeyboardHelp} sections={keyboardShortcuts} />
