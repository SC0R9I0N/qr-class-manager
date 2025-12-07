import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { logoutUser } from "../../api/auth";
import { fetchAnalytics } from "../../api/analytics";
import type { ClassAnalytics } from "../../api/analytics";
import ClassCard from "../../components/instructor/ClassCard";
import "./InstructorDashboard.css";

// Import your QR code API helper + QRCode component
import { generateSessionQRCode } from "../../api/sessions";
import QRCode from "react-qr-code";

const InstructorDashboard: React.FC = () => {
    const navigate = useNavigate();

    const [classes, setClasses] = useState<ClassAnalytics[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Add state for QR code
    const [qrCodeData, setQrCodeData] = useState<string | null>(null);

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

    // Add handlers for new actions
    const handleUploadMaterials = () => {
        navigate("/instructor/upload");
    };

    const handleViewAttendance = (classId: string) => {
        navigate(`/instructor/class/${classId}`);
    };

    const handleGenerateQR = async (classId: string) => {
        try {
            console.log("Calling QR endpoint:", `${import.meta.env.VITE_API_BASE_URL}/sessions/${classId}/generate-qr`)
            const data = await generateSessionQRCode(classId);
            console.log("QR response:", data);
            setQrCodeData(data.qr_data); // backend should return { qr_data: "..." }
        } catch (err) {
            setError((err as Error).message);
        }
    };

    return (
        <div className="dashboard-container">
            <div className="dashboard-card">
                <button
                    className="logout-btn"
                    onClick={handleLogout}
                >
                    Logout
                </button>

                <h1>Instructor Dashboard</h1>

                {loading && <p>Loading analytics</p>}
                {error && <p style={{color: "red"}}>Error: {error}</p>}

                {!loading && !error && (
                    <>
                        <h2>Your Classes</h2>

                        {classes.length === 0 && (
                            <p>No classes found.</p>
                        )}
                        <div className="classes-card">

                            {classes.map((cls) => (
                                <div key={cls.class_id} className="class-item-row">
                                    <ClassCard
                                        id={cls.class_id}
                                        name={cls.class_name}
                                        sessionCount={cls.total_sessions}
                                    />

                                    {/* Add action buttons here */}
                                    <div className="action-buttons">
                                        <button
                                            className="dashboard-btn"
                                            onClick={() => handleViewAttendance(cls.class_id)}
                                        >
                                            View Attendance
                                        </button>

                                        <button
                                            className="dashboard-btn"
                                            onClick={handleUploadMaterials}
                                        >
                                            Upload Materials
                                        </button>

                                        <button
                                            className="dashboard-btn"
                                            onClick={() => handleGenerateQR(cls.class_id)}
                                        >
                                            Generate QR Code
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}

                {/* Render QR code if generated */}
                {qrCodeData && (
                    <div className="qr-code-container">
                        <h2>Generated QR Code</h2>
                        <QRCode value={qrCodeData} size={256}/>
                    </div>
                )}
            </div>
        </div>
    );
};

export default InstructorDashboard;