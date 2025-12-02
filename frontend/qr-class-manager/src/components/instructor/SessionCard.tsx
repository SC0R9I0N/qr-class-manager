import React from "react";
import { useNavigate } from "react-router-dom";
import "./SessionCard.css"

interface SessionCardProps {
    id: string;
    date: string;
    presentCount: number;
}

const SessionCard: React.FC<SessionCardProps> = ({ id, date, presentCount }) => {
    const navigate = useNavigate();

    return (
        <div
            className="session-card"
            onClick={() => navigate(`/session/${id}`)}
        >
            <h3>{date}</h3>
            <p>Present: {presentCount}</p>
        </div>
    );
};

export default SessionCard;