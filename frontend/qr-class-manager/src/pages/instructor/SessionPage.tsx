import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchAttendanceSummary, type AttendanceSummaryResponse } from "../../api/attendance";
import { fetchSession, type Session } from "../../api/sessions";
import "./SessionPage.css";

interface DisplayAttendanceRecord {
    studentId: string;
    studentEmail: string; // Enriched email from Cognito
    scanTime: string;
}

const SessionPage: React.FC = () => {
    const { id: sessionId } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [sessionDetails, setSessionDetails] = useState<Session | null>(null);
    const [attendanceRecords, setAttendanceRecords] = useState<DisplayAttendanceRecord[]>([]);
    const [totalPresentCount, setTotalPresentCount] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!sessionId) {
            setError("Session ID is missing.");
            setLoading(false);
            return;
        }

        const fetchData = async () => {
            try {
                // 1. Fetch Session Details (Contains the QR URL)
                const sessionData = await fetchSession(sessionId);
                setSessionDetails(sessionData);

                // 2. Fetch Attendance Summary
                const summaryData: AttendanceSummaryResponse = await fetchAttendanceSummary({ session_id: sessionId });
                setTotalPresentCount(summaryData.total_present ?? 0);

                // 3. Transform Data to include student_email
                const transformedRecords: DisplayAttendanceRecord[] = (summaryData.attendance_records || []).map(record => ({
                    studentId: record.student_id,
                    studentEmail: (record as any).student_email || record.student_id,
                    scanTime: new Date((record as any).scan_timestamp).toLocaleTimeString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit'
                    }),
                }));

                setAttendanceRecords(transformedRecords);

            } catch (err) {
                console.error("Failed to fetch session data:", err);
                setError("Failed to load session details or attendance records.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [sessionId]);

    if (loading) {
        return <div className="session-container"><p>Loading session data...</p></div>;
    }

    if (error) {
        return <div className="session-container"><p className="error-message">Error: {error}</p></div>;
    }

    if (!sessionDetails) {
        return <div className="session-container"><p>Session not found.</p></div>;
    }

    const displayDate = sessionDetails.date || (sessionDetails as any).session_date || 'N/A';

    return (
        <div className="session-container">
            <div className="session-card">
                <h1>Session: {sessionDetails.title || sessionId}</h1>
                <p>Date: {displayDate}</p>

                <button className="back-btn" onClick={() => navigate(-1)}>
                    Back to Class
                </button>

                {/* 🟢 QR CODE SECTION */}
                {(sessionDetails as any).qr_code_url && (
                    <div className="session-qr-section">
                        <h2>Session QR Code</h2>
                        <p>Display this for students to scan during the session</p>
                        <div className="qr-wrapper">
                            <img
                                src={(sessionDetails as any).qr_code_url}
                                alt="Session QR"
                                className="session-qr-image"
                            />
                        </div>
                    </div>
                )}

                <h2>Attendance</h2>
                <p>Total Present: {totalPresentCount}</p>

                <div className="attendance-card">
                    {attendanceRecords.map((record) => (
                        <div className="individual-attendance-card" key={record.studentId}>
                            <p>
                                <strong>{record.studentEmail}</strong>
                            </p>
                            <p>
                                <span>Scanned at: {record.scanTime}</span>
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default SessionPage;