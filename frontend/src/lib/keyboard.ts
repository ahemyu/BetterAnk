/**
 * Keyboard utility functions for handling keyboard shortcuts
 */

/**
 * Check if the event target is an editable element
 * @param target - The event target element
 * @returns true if the target is editable (input, textarea, contenteditable, etc.)
 */
export function isEditableElement(target: EventTarget | null): boolean {
	if (!target || !(target instanceof HTMLElement)) {
		return false;
	}

	return (
		target.tagName === 'INPUT' ||
		target.tagName === 'TEXTAREA' ||
		target.tagName === 'SELECT' ||
		target.isContentEditable ||
		target.getAttribute('role') === 'textbox'
	);
}

/**
 * Check if a key matches (case-insensitive) without modifier keys
 * @param event - The keyboard event
 * @param key - The key to match (e.g., 'a', 'z')
 * @returns true if the key matches without Ctrl/Cmd modifiers
 */
export function isKey(event: KeyboardEvent, key: string): boolean {
	return (
		(event.key.toLowerCase() === key.toLowerCase()) &&
		!event.ctrlKey &&
		!event.metaKey
	);
}

/**
 * Check if a key matches with Shift modifier
 * @param event - The keyboard event
 * @param key - The key to match
 * @returns true if the key matches with Shift pressed
 */
export function isShiftKey(event: KeyboardEvent, key: string): boolean {
	return (
		event.key.toLowerCase() === key.toLowerCase() &&
		event.shiftKey &&
		!event.ctrlKey &&
		!event.metaKey
	);
}

/**
 * Check if Escape key is pressed
 * @param event - The keyboard event
 * @returns true if Escape is pressed
 */
export function isEscape(event: KeyboardEvent): boolean {
	return event.key === 'Escape';
}

/**
 * Check if Enter key is pressed
 * @param event - The keyboard event
 * @returns true if Enter is pressed
 */
export function isEnter(event: KeyboardEvent): boolean {
	return event.key === 'Enter';
}
