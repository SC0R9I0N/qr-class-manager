import React from "react";
import { useNavigate, useParams } from "react-router-dom";

interface AttendanceRecord {
    studentId: string;
    scanTime: string;
}

const SessionPage: React.FC = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    // Placeholder analytics and scan data
    const sessionDate = "2024-09-12";

    const attendanceRecords: AttendanceRecord[] = [
        { studentId: "student01", scanTime: "09:03 AM" },
        { studentId: "student02", scanTime: "09:05 AM" },
        { studentId: "student03", scanTime: "09:07 AM" },
    ];

    return (
        <div style={{ padding: 20 }}>
            <h1>Session: {id}</h1>
            <p>Date: {sessionDate}</p>

            <button
                onClick={() => navigate(-1)}
                style={{
                    marginTop: 10,
                    marginBottom: 20,
                    padding: "8px 14px",
                    cursor: "pointer",
                }}
            >
                Back to Class
            </button>

            <h2>Attendance</h2>
            <p>Total Present: {attendanceRecords.length}</p>

            <div style={{ marginTop: 20 }}>
                {attendanceRecords.map((record) => (
                    <div
                        key={record.studentId}
                        style={{
                            border: "1px solid #ddd",
                            padding: 12,
                            marginBottom: 10,
                            borderRadius: 6,
                        }}
                    >
                        <strong>{record.studentId}</strong>
                        <br />
                        <span>Scanned at: {record.scanTime}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SessionPage;