import { apiGet, apiPost } from "./api";

export interface AttendanceRecord {
    session_id: string;
    student_id: string;
    timestamp: string;
}

export interface AttendanceQueryParams {
    session_id?: string;
    student_id?: string;
}

export function fetchAttendance(
    params: AttendanceQueryParams = {}
): Promise<AttendanceRecord[]> {
    const query = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v != null) as [string, string][]
    );
    const path = query.toString()
        ? `/attendance?${query.toString()}`
        : "/attendance";

    return apiGet<AttendanceRecord[]>(path);
}

export interface ScanAttendanceInput {
    session_id: string;
    qr_payload: string; // or student_id, etc., depending on backend
}

export function scanAttendance(
    input: ScanAttendanceInput
): Promise<{ success: boolean }> {
    return apiPost<{ success: boolean }>("/attendance/scan", input);
}