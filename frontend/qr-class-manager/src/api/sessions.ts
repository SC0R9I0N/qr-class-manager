import { apiGet, apiPost, apiPut, apiDelete } from "./api";

export interface Session {
    session_id: string;
    class_id: string;
    title: string;
    date: string;      // ISO string
    is_active?: boolean;
}

export interface CreateSessionInput {
    class_id: string;
    title: string;
    date: string;
}

export function fetchSessions(): Promise<Session[]> {
    return apiGet<Session[]>("/sessions");
}

export function fetchSession(sessionId: string): Promise<Session> {
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