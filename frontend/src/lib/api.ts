// API service layer

interface RequestOptions extends RequestInit {
	headers?: HeadersInit;
}

function getAuthHeaders(): HeadersInit {
	return {
		'Content-Type': 'application/json'
	};
}

async function handleResponse(res: Response) {
	if (!res.ok) {
		let errorMessage = 'An unexpected error occurred';
		try {
			const errorData = await res.json();
			errorMessage = errorData.detail || errorMessage;
		} catch {
			// If JSON parsing fails, provide status-specific messages
			if (res.status === 401) {
				errorMessage = 'Please log in to continue';
			} else if (res.status === 403) {
				errorMessage = 'You do not have permission to perform this action';
			} else if (res.status === 404) {
				errorMessage = 'The requested resource was not found';
			} else if (res.status === 500) {
				errorMessage = 'Server error. Please try again later';
			} else {
				errorMessage = `Request failed with status ${res.status}`;
			}
		}
		throw new Error(errorMessage);
	}
	return res.json();
}

export async function apiGet(path: string): Promise<any> {
	const res = await fetch(path, {
		headers: getAuthHeaders(),
		credentials: 'include'
	});
	return handleResponse(res);
}

export async function apiPost(path: string, body: any): Promise<any> {
	const res = await fetch(path, {
		method: 'POST',
		headers: getAuthHeaders(),
		body: JSON.stringify(body),
		credentials: 'include'
	});
	return handleResponse(res);
}

export async function apiPut(path: string, body: any): Promise<any> {
	const res = await fetch(path, {
		method: 'PUT',
		headers: getAuthHeaders(),
		body: JSON.stringify(body),
		credentials: 'include'
	});
	return handleResponse(res);
}

export async function apiDelete(path: string): Promise<any> {
	const res = await fetch(path, {
		method: 'DELETE',
		headers: getAuthHeaders(),
		credentials: 'include'
	});
	return handleResponse(res);
}

// Auth specific
export async function login(username: string, password: string): Promise<{ message: string }> {
	const body = new URLSearchParams();
	body.append('username', username);
	body.append('password', password);

	const res = await fetch('/login', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded'
		},
		body: body.toString(),
		credentials: 'include'
	});

	return handleResponse(res);
}

export async function register(username: string, password: string, email: string): Promise<any> {
	const res = await fetch('/register', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ email, username, password }),
		credentials: 'include'
	});

	return handleResponse(res);
}
