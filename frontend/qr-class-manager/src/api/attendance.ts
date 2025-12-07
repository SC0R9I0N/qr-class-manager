import { apiGet, apiPost } from "./api";

export interface AttendanceRecord {
    session_id: string;
    student_id: string;
    timestamp: string;
}

export interface AttendanceSummaryResponse {
    session_id: string;
    class_id: string;
    total_present: number;
    attendance_records: AttendanceRecord[]; // The list of records
}

export interface AttendanceQueryParams {
    session_id?: string;
    student_id?: string;
}

export function fetchAttendanceSummary(
    params: AttendanceQueryParams = {}
): Promise<AttendanceSummaryResponse> { // Changed return type
    const query = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v != null) as [string, string][]
    );
    const path = query.toString()
        ? `/attendance?${query.toString()}`
        : "/attendance";

    return apiGet<AttendanceSummaryResponse>(path);
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
  qr_code_data: string;   // JSON string
  location: string;
  device_info: string;
}

export function scanAttendance(
  input: ScanAttendanceInput
): Promise<{ success: boolean }> {
  return apiPost<{ success: boolean }>("/attendance/scan", input);
}