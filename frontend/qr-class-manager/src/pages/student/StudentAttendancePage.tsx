import React, { useState } from "react";
import StudentLoginForm from "../../components/student/StudentLoginForm";
import QRScanner from "../../components/student/QRScanner";
import AttendanceSuccess from "../../components/student/AttendanceSuccess";

interface StudentInfo {
    name: string;
    email: string;
    idToken?: string;
}

interface AttendanceResult {
    className: string;
    sessionDate: string;
    downloadUrl?: string;
}

const StudentAttendancePage: React.FC = () => {
    const [step, setStep] = useState<"login" | "scan" | "success">("login");
    const [studentInfo, setStudentInfo] = useState<StudentInfo | null>(null);
    const [attendanceResult, setAttendanceResult] = useState<AttendanceResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleLogin = (name: string, email: string, idToken: string) => {
        setStudentInfo({ name, email, idToken });
        setStep("scan");
    };

    const handleScanSuccess = async (qrData: string) => {
        setLoading(true);
        setError("");

        try {
            // Parse QR code data
            const qrCodeData = JSON.parse(qrData);

            // DEVELOPMENT MODE: Use mock data if API fails
            // Set to false when backend is ready
            const USE_MOCK_DATA = true;

            if (USE_MOCK_DATA) {
                // Simulate API delay
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Mock successful response
                setAttendanceResult({
                    className: "Computer Science 101",
                    sessionDate: new Date().toLocaleDateString(),
                    downloadUrl: undefined, // Set to a URL when testing download
                });

                setStep("success");
                return;
            }

            // PRODUCTION MODE: Call real API
            // According to README.md, the API endpoint is:
            // POST /attendance/scan
            const response = await fetch(
                "https://7ql71igsye.execute-api.us-east-1.amazonaws.com/prod/attendance/scan",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${studentInfo?.idToken}`,
                    },
                    body: JSON.stringify({
                        qr_code_data: qrData,
                        student_name: studentInfo?.name,
                        student_email: studentInfo?.email,
                    }),
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || "Failed to mark attendance");
            }

            const result = await response.json();

            // Store attendance result
            setAttendanceResult({
                className: result.class_name || "Class",
                sessionDate: new Date(result.scan_timestamp).toLocaleDateString(),
                downloadUrl: result.download_url, // If materials are available
            });

            setStep("success");
        } catch (err) {
            // Better error messages
            let errorMessage = "An error occurred";
            
            if (err instanceof Error) {
                if (err.message.includes("Failed to fetch")) {
                    errorMessage = "Cannot connect to server. Please check if the backend is running or set USE_MOCK_DATA to true for testing.";
                } else {
                    errorMessage = err.message;
                }
            }
            
            setError(errorMessage);
            console.error("Attendance error:", err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div style={{ 
                display: "flex", 
                justifyContent: "center", 
                alignItems: "center", 
                height: "100vh",
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
            }}>
                <div style={{
                    background: "white",
                    padding: "2rem",
                    borderRadius: "12px",
                    boxShadow: "0 10px 40px rgba(0, 0, 0, 0.1)"
                }}>
                    <h2 style={{ margin: 0 }}>Processing attendance...</h2>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ 
                display: "flex", 
                flexDirection: "column",
                justifyContent: "center", 
                alignItems: "center", 
                height: "100vh",
                padding: "2rem",
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
            }}>
                <div style={{
                    background: "white",
                    padding: "2rem",
                    borderRadius: "12px",
                    boxShadow: "0 10px 40px rgba(0, 0, 0, 0.1)",
                    textAlign: "center",
                    maxWidth: "500px"
                }}>
                    <h2 style={{ color: "#c33", margin: "0 0 1rem 0" }}>Error</h2>
                    <p style={{ marginBottom: "1.5rem" }}>{error}</p>
                    <button 
                        onClick={() => window.location.reload()}
                        style={{
                            padding: "0.875rem 2rem",
                            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            color: "white",
                            border: "none",
                            borderRadius: "8px",
                            fontSize: "1rem",
                            fontWeight: 600,
                            cursor: "pointer"
                        }}
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <>
            {step === "login" && <StudentLoginForm onLogin={handleLogin} />}
            
            {step === "scan" && studentInfo && (
                <QRScanner
                    studentName={studentInfo.name}
                    studentEmail={studentInfo.email}
                    onScanSuccess={handleScanSuccess}
                />
            )}
            
            {step === "success" && studentInfo && attendanceResult && (
                <AttendanceSuccess
                    studentName={studentInfo.name}
                    className={attendanceResult.className}
                    sessionDate={attendanceResult.sessionDate}
                    downloadUrl={attendanceResult.downloadUrl}
                />
            )}
        </>
    );
};

export default StudentAttendancePage;
