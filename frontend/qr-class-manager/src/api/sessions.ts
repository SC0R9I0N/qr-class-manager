import { apiGet, apiPost, apiPut, apiDelete } from "./api";

export interface Session {
    session_id: string;
    class_id: string;
    title: string;
    date: string;      // ISO string
    is_active?: boolean;
    attendance_count: number;
}

export interface CreateSessionInput {
    class_id: string;
    title: string;
    date: string;
}

export async function fetchSessions(classId: string): Promise<Session[]> {
    // apiGet likely returns the full JSON object: { class_id, sessions, count }
    const responseData = await apiGet<any>(`/sessions?class_id=${classId}`);

    // Check if the response contains the 'sessions' array
    if (responseData && Array.isArray(responseData.sessions)) {
        return responseData.sessions as Session[];
    }

    // Return an empty array if the expected structure isn't found
    return [];
}

export function fetchSession(sessionId: string): Promise<Session> {
    // This call returns a single session object, not wrapped in a list
    return apiGet<Session>(`/sessions/${sessionId}`);
}

export function createSession(input: CreateSessionInput): Promise<Session> {
    return apiPost<Session>("/sessions", input);
}

export function updateSession(
    sessionId: string,
    update: Partial<CreateSessionInput>
): Promise<Session> {
    return apiPut<Session>(`/sessions/${sessionId}`, update);
}

export function deleteSession(sessionId: string): Promise<{ success: boolean }> {
    return apiDelete<{ success: boolean }>(`/sessions/${sessionId}`);
}

const baseUrl = import.meta.env.VITE_API_BASE_URL;

export async function generateSessionQRCode(classId: string) {
  const token = localStorage.getItem("idToken");
  console.log("Using token:", token);
  const response = await fetch(`${baseUrl}/sessions/${classId}/generate-qr`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  console.log("Raw response:", response);
  if (!response.ok) throw new Error("Failed to generate QR code");
  return response.json();
}