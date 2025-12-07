import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CognitoConfirmSignUpResponse } from "../../api/auth";
import { confirmUser } from "../../api/auth";
import "./StudentConfirmPage.css"

const StudentConfirmPage: React.FC = () => {
    const navigate = useNavigate();

    // Form state
    const [email, setEmail] = useState("");
    const [code, setCode] = useState("");

    // UI feedback state
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleConfirm = async (e: React.FormEvent) => {
        // Prevent default browser refresh on Enter/Submit
        e.preventDefault();

        setError(null);
        setLoading(true);

        try {
            const result: CognitoConfirmSignUpResponse = await confirmUser(email.trim(), code.trim());

            // Success response from Cognito typically doesn't include a message
            if (!result.message) {
                // Return to student login/scan page on success
                navigate("/student");
            } else {
                setError(result.message);
            }
        } catch (err: any) {
            console.error("Confirmation Error:", err);
            setError(err.message || "Invalid code. Please check your email and try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="student-confirm-container">
            <div className="student-confirm-card">
                <h1>ClassBits</h1>
                <h2>Confirm Student Account</h2>
                <p className="instruction">Enter the verification code sent to your email</p>

                {/* In-page error display instead of pop-up alert */}
                {error && <p className="error-message">{error}</p>}

                {/* Wrapping in <form> enables 'Enter' key submission */}
                <form onSubmit={handleConfirm}>
                    <div className="form-group">
                        <label htmlFor="email">Email Address</label>
                        <input
                            id="email"
                            type="email"
                            placeholder="student1@example.com"
                            value={email}
                            onChange={(e) => {
                                setEmail(e.target.value);
                                if (error) setError(null);
                            }}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="verification">Verification Code</label>
                        <input
                            id="verification"
                            type="text"
                            placeholder="000000"
                            value={code}
                            onChange={(e) => {
                                setCode(e.target.value);
                                if (error) setError(null);
                            }}
                            required
                        />
                    </div>

                    <button
                        className="confirm-verification-btn"
                        type="submit"
                        disabled={loading}
                    >
                        {loading ? "Confirming..." : "Confirm Account"}
                    </button>
                </form>

                {/* Standardized 'Back to Login' button */}
                <button
                    className="back-btn"
                    onClick={() => navigate("/student")}
                >
                    Back to Login
                </button>
            </div>
        </div>
    );
};

export default StudentConfirmPage;