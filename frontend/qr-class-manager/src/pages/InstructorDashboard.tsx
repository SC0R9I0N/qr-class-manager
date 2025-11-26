import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { logoutUser } from "../api/auth";
import { fetchAnalytics } from "../api/analytics";
import type { ClassAnalytics } from "../api/analytics";
import ClassCard from "../components/ClassCard";

const InstructorDashboard: React.FC = () => {
    const navigate = useNavigate();

    const [classes, setClasses] = useState<ClassAnalytics[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const handleLogout = () => {
        logoutUser();
        navigate("/login");
    };

    useEffect(() => {
        const loadAnalytics = async () => {
            try {
                const data = await fetchAnalytics();   // GET /analytics
                setClasses(data.classes);
            } catch (e) {
                const err = e as Error;
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        loadAnalytics();
    }, []);

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

            {loading && <p>Loading analytics…</p>}
            {error && <p style={{ color: "red" }}>Error: {error}</p>}

            {!loading && !error && (
                <>
                    <h2>Your Classes</h2>

                    {classes.length === 0 && (
                        <p>No classes found.</p>
                    )}

                    {classes.map((cls) => (
                        <ClassCard
                            key={cls.class_id}
                            id={cls.class_id}
                            name={cls.class_name}
                            sessionCount={cls.total_sessions}
                        />
                    ))}
                </>
            )}
        </div>
    );
};

export default InstructorDashboard;