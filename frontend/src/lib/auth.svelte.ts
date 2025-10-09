// Auth state management using Svelte 5 runes
// Token is stored in HttpOnly cookie by the backend

let isAuthenticatedValue = $state<boolean>(false);

export function setAuthenticated(authenticated: boolean): void {
	isAuthenticatedValue = authenticated;
}

export function isAuthenticated(): boolean {
	return isAuthenticatedValue;
}

export async function logout(): Promise<void> {
	try {
		await fetch('/logout', {
			method: 'POST',
			credentials: 'include'
		});
	} catch (err) {
		console.error('Logout request failed:', err);
	} finally {
		setAuthenticated(false);
	}
}
