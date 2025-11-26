import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import SessionCard from "../components/SessionCard";
import { fetchSessions } from "../api/sessions";
import type { Session } from "../api/sessions";

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
        <div style={{ padding: 20 }}>
            <h1>Class: {classId}</h1>

            <button
                onClick={() => navigate("/upload")}
                style={{ padding: "10px 20px", marginBottom: 20, cursor: "pointer" }}
            >
                Upload Resource
            </button>

            <h2>Sessions</h2>

            {sessions.map((session) => (
                <SessionCard
                    key={session.session_id}
                    id={session.session_id}
                    date={session.date}
                    presentCount={0 /* hook up later with attendance/analytics */}
                />
            ))}
        </div>
    );
};

export default ClassPage;