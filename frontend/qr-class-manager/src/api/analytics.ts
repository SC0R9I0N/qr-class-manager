import { apiGet } from "./api";

export interface ClassAnalytics {
    class_id: string;
    class_name: string;
    total_sessions: number;
    total_students: number;
    average_attendance_rate: number; // %
}

export interface AnalyticsResponse {
    classes: ClassAnalytics[];
}

export function fetchAnalytics(): Promise<AnalyticsResponse> {
    return apiGet<AnalyticsResponse>("/analytics");
}