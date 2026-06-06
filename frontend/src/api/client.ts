const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data: unknown
  ) {
    super(`${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('access_token');
      sessionStorage.setItem('login_redirect', window.location.pathname + window.location.search);
      window.location.href = '/login';
      return new Promise(() => {});
    }
    const data = await response.json().catch(() => ({}));
    throw new ApiError(response.status, response.statusText, data);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const apiClient = {
  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    });
    return handleResponse<T>(response);
  },

  async post<T>(path: string, body?: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(response);
  },

  async postFormData<T>(path: string, formData: FormData): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
      },
      body: formData,
    });
    return handleResponse<T>(response);
  },

  async put<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify(body),
    });
    return handleResponse<T>(response);
  },

  async delete<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'DELETE',
      headers: {
        ...getAuthHeaders(),
      },
    });
    return handleResponse<T>(response);
  },
};
