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
            const allSessions = await fetchSessions();
            // filter by class_id
            const filtered = allSessions.filter(
                (s) => s.class_id === classId
            );
            setSessions(filtered);
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
                            presentCount={0 /* hook up later with attendance/analytics */}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ClassPage;