const BASE_URL = import.meta.env.VITE_API_BASE_URL;

function getAuthToken(): string | null {
    return localStorage.getItem("idToken");
}

async function request<T>(
    path: string,
    options: RequestInit = {}
): Promise<T> {
    const token = getAuthToken();

    // Use a normal object for headers
    const headers: Record<string, string> = {
        ...(options.headers as Record<string, string> || {})
    };

    if (!(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
    }

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${BASE_URL}${path}`, {
        ...options,
        headers,
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
    }

    return res.json() as Promise<T>;
}

export function apiGet<T>(path: string): Promise<T> {
    return request<T>(path, { method: "GET" });
}

export function apiPost<T>(
    path: string,
    body: unknown
): Promise<T> {
    return request<T>(path, {
        method: "POST",
        body: JSON.stringify(body),
    });
}

export function apiPut<T>(
    path: string,
    body: unknown
): Promise<T> {
    return request<T>(path, {
        method: "PUT",
        body: JSON.stringify(body),
    });
}

export function apiDelete<T>(path: string): Promise<T> {
    return request<T>(path, { method: "DELETE" });
}

// For multipart/form-data (file upload)
export function apiUpload<T>(
    path: string,
    formData: FormData
): Promise<T> {
    const token = getAuthToken();

    const headers: HeadersInit = {};

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    return fetch(`${BASE_URL}${path}`, {
        method: "POST",
        headers,
        body: formData,
    }).then(async (res) => {
        if (!res.ok) {
            const text = await res.text();
            throw new Error(`Upload failed: ${res.status} ${text}`);
        }
        return res.json() as Promise<T>;
    });
}