<script lang="ts">
	interface Shortcut {
		key: string;
		description: string;
	}

	interface ShortcutSection {
		title: string;
		shortcuts: Shortcut[];
	}

	let { show = $bindable(false), sections }: { show?: boolean; sections: ShortcutSection[] } =
		$props();

	function handleModalClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			show = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (show && (event.key === 'Escape' || event.key === '?')) {
			event.preventDefault();
			show = false;
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if show}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		onclick={handleModalClick}
		class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
	>
		<div class="relative top-20 mx-auto p-6 border w-full max-w-2xl shadow-lg rounded-md bg-white">
			<div class="flex justify-between items-center mb-4">
				<h2 class="text-2xl font-bold text-gray-900">Keyboard Shortcuts</h2>
				<button
					onclick={() => (show = false)}
					class="text-gray-500 hover:text-gray-700 text-2xl font-bold"
					aria-label="Close"
				>
					&times;
				</button>
			</div>

			<div class="space-y-6">
				{#each sections as section}
					<div>
						<h3 class="text-lg font-semibold text-gray-800 mb-2">{section.title}</h3>
						<div class="space-y-2">
							{#each section.shortcuts as shortcut}
								<div class="flex justify-between items-center py-1">
									<span class="text-gray-700">{shortcut.description}</span>
									<kbd
										class="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono"
									>
										{shortcut.key}
									</kbd>
								</div>
							{/each}
						</div>
					</div>
				{/each}
			</div>

			<div class="mt-6 text-center">
				<button
					onclick={() => (show = false)}
					class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded"
				>
					Close
				</button>
			</div>
		</div>
	</div>
{/if}
