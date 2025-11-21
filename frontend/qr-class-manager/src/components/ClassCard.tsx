import React from "react";
import { useNavigate } from "react-router-dom";

interface ClassCardProps {
    id: string;
    name: string;
    sessionCount: number;
}

const ClassCard: React.FC<ClassCardProps> = ({ id, name, sessionCount }) => {
    const navigate = useNavigate();

    return (
        <div
            onClick={() => navigate(`/class/${id}`)}
            style={{
                border: "1px solid #ddd",
                padding: 16,
                marginBottom: 12,
                cursor: "pointer",
                borderRadius: 6,
            }}
        >
            <h3>{name}</h3>
            <p>Sessions: {sessionCount}</p>
        </div>
    );
};

export default ClassCard;