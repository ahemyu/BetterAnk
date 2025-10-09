// Auth state management using Svelte 5 runes

let authTokenValue = $state<string | null>(
	typeof window !== 'undefined' ? localStorage.getItem('authToken') : null
);

export function setAuthToken(token: string | null) {
	authTokenValue = token;
	if (typeof window !== 'undefined') {
		if (token) {
			localStorage.setItem('authToken', token);
		} else {
			localStorage.removeItem('authToken');
		}
	}
}

export function getAuthToken(): string | null {
	return authTokenValue;
}

export function isAuthenticated(): boolean {
	return authTokenValue !== null;
}

export function logout() {
	setAuthToken(null);
}
