import React from "react";
import { useNavigate } from "react-router-dom";
import ClassCard from "../components/ClassCard";

const InstructorDashboard: React.FC = () => {
    const navigate = useNavigate();

    // Placeholder classes — you can replace this with API data later
    const classes = [
        { id: "class1", name: "Intro to Biology", sessionCount: 12 },
        { id: "class2", name: "Data Science 101", sessionCount: 8 }
    ];

    return (
        <div style={{ padding: 20 }}>
            <h1>Instructor Dashboard</h1>

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

            <h2>Your Classes</h2>

            {classes.map(cls => (
                <ClassCard
                    key={cls.id}
                    id={cls.id}
                    name={cls.name}
                    sessionCount={cls.sessionCount}
                />
            ))}
        </div>
    );
};

export default InstructorDashboard;