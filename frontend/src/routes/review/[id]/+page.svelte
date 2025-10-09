<script lang="ts">
	import { onMount, onDestroy, untrack } from 'svelte';
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

			if (currentIndex >= reviewQueue.length) {
				isReviewFinished = true;
			} else {
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
		if (event.key === 'Enter' && !showBack && !isReviewFinished) {
			handleShowAnswer();
		} else if (event.key === 'Escape' && showEditModal) {
			showEditModal = false;
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
				Back to Start Menu
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
						Show Answer
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
							Good
						</button>
						<button
							onclick={() => handleFeedback('mid')}
							class="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded"
						>
							Mid
						</button>
						<button
							onclick={() => handleFeedback('bad')}
							class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
						>
							Bad
						</button>
					</div>
					<div class="mt-4 space-x-2">
						<button
							onclick={handleEdit}
							class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-1 px-2 rounded"
						>
							Edit
						</button>
						<button
							onclick={handleDelete}
							class="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded"
						>
							Delete
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
