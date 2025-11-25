import React from "react";
import { useNavigate } from "react-router-dom";

interface SessionCardProps {
    id: string;
    date: string;
    presentCount: number;
}

const SessionCard: React.FC<SessionCardProps> = ({ id, date, presentCount }) => {
    const navigate = useNavigate();

    return (
        <div
            onClick={() => navigate(`/session/${id}`)}
            style={{
                border: "1px solid #ddd",
                padding: 16,
                marginBottom: 12,
                cursor: "pointer",
                borderRadius: 6,
            }}
        >
            <h3>{date}</h3>
            <p>Present: {presentCount}</p>
        </div>
    );
};

export default SessionCard;