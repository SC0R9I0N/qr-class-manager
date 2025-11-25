import React from "react";
import { useNavigate } from "react-router-dom";
import { logoutUser } from "../api/auth";
import ClassCard from "../components/ClassCard";

const InstructorDashboard: React.FC = () => {
    const navigate = useNavigate();

    const handleLogout = () => {
        logoutUser();            
        navigate("/login");      
    };

    const classes = [
        { id: "class1", name: "Intro to Biology", sessionCount: 12 },
        { id: "class2", name: "Data Science 101", sessionCount: 8 }
    ];

    return (
        <div style={{ padding: 20 }}>
            {/* Logout Button */}
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button
                    onClick={handleLogout}
                    style={{
                        padding: "8px 16px",
                        cursor: "pointer",
                        marginBottom: 20,
                    }}
                >
                    Logout
                </button>
            </div>

            <h1>Instructor Dashboard</h1>

            <h2>Your Classes</h2>

            {classes.map((cls) => (
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