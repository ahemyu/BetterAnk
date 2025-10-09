// API service layer
import { getAuthToken } from './auth.svelte';

interface RequestOptions extends RequestInit {
	headers?: HeadersInit;
}

function getAuthHeaders(): HeadersInit {
	const authToken = typeof window !== 'undefined' ? getAuthToken() : null;
	return {
		Authorization: `Bearer ${authToken}`,
		'Content-Type': 'application/json'
	};
}

async function handleResponse(res: Response) {
	if (!res.ok) {
		let errorMessage = `Request failed with status ${res.status}`;
		try {
			const errorData = await res.json();
			errorMessage = errorData.detail || errorMessage;
		} catch {
			// If JSON parsing fails, use the default error message
		}
		throw new Error(errorMessage);
	}
	return res.json();
}

export async function apiGet(path: string): Promise<any> {
	const res = await fetch(path, {
		headers: getAuthHeaders()
	});
	return handleResponse(res);
}

export async function apiPost(path: string, body: any): Promise<any> {
	const res = await fetch(path, {
		method: 'POST',
		headers: getAuthHeaders(),
		body: JSON.stringify(body)
	});
	return handleResponse(res);
}

export async function apiPut(path: string, body: any): Promise<any> {
	const res = await fetch(path, {
		method: 'PUT',
		headers: getAuthHeaders(),
		body: JSON.stringify(body)
	});
	return handleResponse(res);
}

export async function apiDelete(path: string): Promise<any> {
	const res = await fetch(path, {
		method: 'DELETE',
		headers: getAuthHeaders()
	});
	return handleResponse(res);
}

// Auth specific
export async function login(username: string, password: string): Promise<{ access_token: string }> {
	const body = new URLSearchParams();
	body.append('username', username);
	body.append('password', password);

	const res = await fetch('/login', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded'
		},
		body: body.toString()
	});

	return handleResponse(res);
}

export async function register(username: string, password: string, email: string): Promise<any> {
	const res = await fetch('/register', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ email, username, password })
	});

	return handleResponse(res);
}
