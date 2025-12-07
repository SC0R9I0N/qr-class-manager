import React, { useState } from "react";
import StudentLoginForm from "../../components/student/StudentLoginForm";
import QRScanner from "../../components/student/QRScanner";
import AttendanceSuccess from "../../components/student/AttendanceSuccess";
import { getValidIdToken } from "../../api/auth";

interface StudentInfo {
    name: string;
    email: string;
    idToken?: string;
}

interface AttendanceResult {
    className: string;
    classId: string;
    sessionDate: string;
    downloadUrl?: string;
    message?: string;
}

const StudentAttendancePage: React.FC = () => {
    const [step, setStep] = useState<"login" | "scan" | "success">("login");
    const [studentInfo, setStudentInfo] = useState<StudentInfo | null>(null);
    const [attendanceResult, setAttendanceResult] = useState<AttendanceResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleLogin = (name: string, email: string, idToken: string) => {
      // Store the token for later API calls
      localStorage.setItem("idToken", idToken);

      setStudentInfo({ name, email, idToken });
      setStep("scan");
    };

    const handleScanSuccess = async (qrData: string) => {
        setLoading(true);
        setError("");

        try {
            const token = await getValidIdToken();
            if (!token) throw new Error("Session expired, please log in again");

            // --- Simplified QR Data Preparation ---
            // 1. Parse into object for validation
            const qrObject = JSON.parse(qrData.trim());
            // 2. Stringify back into string (necessary for correct escaping in body)
            const qrCodeData = JSON.stringify(qrObject);

            // PRODUCTION MODE: Call real API
            const response = await fetch(
              "https://7ql71igsye.execute-api.us-east-1.amazonaws.com/prod/attendance/scan",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({
                    qr_code_data: qrCodeData,
                    location: "web client",
                    device_info: navigator.userAgent,
                }),
              }
            );

            const raw = await response.text();
            console.log("Attendance API status:", response.status);
            console.log("Attendance API raw response:", raw);

            let result;
            let finalMessage: string | undefined;

            if (response.status === 409) {
                // Attendance already recorded
                try {
                    const errorData = JSON.parse(raw);
                    finalMessage = errorData.message || "Attendance already recorded for this session.";

                    // We must generate a minimal result structure for the success screen
                    result = {
                        class_name: "Class",
                        scan_timestamp: new Date().toISOString(), // Fallback timestamp
                        message: finalMessage
                    };
                } catch {
                    throw new Error("Conflict (409) received, but response body was unreadable.");
                }

            } else if (!response.ok) {
                // Handle all other HTTP errors (400, 401, 500, etc.)
                let msg = "Failed to mark attendance";
                try {
                    const errJson = JSON.parse(raw);
                    msg = errJson.message || msg;
                } catch {
                    msg = raw || msg;
                }
                throw new Error(msg);
            } else {
                // HTTP 200 OK (Successful new attendance record)
                result = JSON.parse(raw);
                finalMessage = result.message;
            }

            // Store attendance result
            setAttendanceResult({
                className: result.class_name || "Class",
                classId: result.class_id,
                sessionDate: new Date(result.scan_timestamp).toLocaleDateString(),
                downloadUrl: result.download_url,
                message: finalMessage, // Pass the specific message to the success screen
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
                    classId={attendanceResult.classId}
                    sessionDate={attendanceResult.sessionDate}
                    downloadUrl={attendanceResult.downloadUrl}
                />
            )}
        </>
    );
};

export default StudentAttendancePage;
