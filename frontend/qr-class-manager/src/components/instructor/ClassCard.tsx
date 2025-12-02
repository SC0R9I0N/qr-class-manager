import React from "react";
import { useNavigate } from "react-router-dom";
import "./ClassCard.css"

interface ClassCardProps {
    id: string;
    name: string;
    sessionCount: number;
}

const ClassCard: React.FC<ClassCardProps> = ({ id, name, sessionCount }) => {
    const navigate = useNavigate();

    return (
        <div className="class-card"
            onClick={() => navigate(`/class/${id}`)}
        >
            <h3>{name}</h3>
            <p>Sessions: {sessionCount}</p>
        </div>
    );
};

export default ClassCard;