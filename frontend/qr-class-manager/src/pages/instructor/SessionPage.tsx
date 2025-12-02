import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./SessionPage.css"

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
        <div className="session-container">
            <div className="session-card">
                <h1>Session: {id}</h1>
                <p>Date: {sessionDate}</p>

                <button
                    className="back-btn"
                    onClick={() => navigate(-1)}
                >
                    Back to Class
                </button>

                <h2>Attendance</h2>
                <p>Total Present: {attendanceRecords.length}</p>

                <div className="attendance-card">
                    {attendanceRecords.map((record) => (
                        <div
                            className="individual-attendance-card"
                            key={record.studentId}
                        >
                            <p>
                                <strong>{record.studentId}</strong>
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