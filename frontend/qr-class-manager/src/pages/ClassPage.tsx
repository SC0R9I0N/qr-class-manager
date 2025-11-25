import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import SessionCard from "../components/SessionCard";

const ClassPage: React.FC = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    // Placeholder class + sessions
    const className = id === "class1" ? "Intro to Biology" : "Data Science 101";

    const sessions = [
        { id: "session1", date: "2024-09-12", presentCount: 28 },
        { id: "session2", date: "2024-09-10", presentCount: 26 }
    ];

    return (
        <div style={{ padding: 20 }}>
            <h1>{className}</h1>

            <button
                onClick={() => navigate("/upload")}
                style={{
                    padding: "10px 20px",
                    marginBottom: 20,
                    cursor: "pointer",
                }}
            >
                Upload Resource
            </button>

            <h2>Sessions</h2>

            {sessions.map(session => (
                <SessionCard
                    key={session.id}
                    id={session.id}
                    date={session.date}
                    presentCount={session.presentCount}
                />
            ))}
        </div>
    );
};

export default ClassPage;