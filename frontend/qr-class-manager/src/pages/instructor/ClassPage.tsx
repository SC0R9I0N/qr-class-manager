import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import SessionCard from "../../components/instructor/SessionCard";
import { fetchSessions } from "../../api/sessions";
import type { Session } from "../../api/sessions";
import "./ClassPage.css"

const ClassPage: React.FC = () => {
    const { id: classId } = useParams();
    const navigate = useNavigate();
    const [sessions, setSessions] = useState<Session[]>([]);

    useEffect(() => {
        (async () => {
            if (classId) {
                // 1. fetchSessions now passes classId to the backend
                // 2. fetchSessions now returns only the array of sessions
                const sessions = await fetchSessions(classId);

                // 3. Remove client-side filtering
                setSessions(sessions);
            }
        })();
    }, [classId]);

    return (
        <div className="class-container">
            <div className="class-card">
                <h1>Class: {classId}</h1>

                <button
                    className="upload-btn"
                    onClick={() => navigate("/upload")}
                >
                    Upload Resource
                </button>

                <h2>Sessions</h2>

                <div className="sessions-card">
                    {sessions.map((session) => (
                        <SessionCard
                            key={session.session_id}
                            id={session.session_id}
                            date={session.date}
                            presentCount={session.attendance_count}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ClassPage;