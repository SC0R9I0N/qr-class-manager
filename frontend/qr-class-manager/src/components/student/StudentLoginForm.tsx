import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../../api/auth";
import "./StudentLoginForm.css";

interface StudentLoginFormProps {
    onLogin: (studentName: string, studentEmail: string, idToken: string) => void;
}

const StudentLoginForm: React.FC<StudentLoginFormProps> = ({ onLogin }) => {
    const navigate = useNavigate();

    // Form state
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // UI Feedback state
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        // Prevent default browser form refresh on Enter/Submit
        e.preventDefault();

        // Reset state before attempt
        setError(null);
        setLoading(true);

        try {
            // Authenticate with AWS Cognito
            const result = await loginUser(email.trim(), password.trim());

            if (result.AuthenticationResult) {
                const idToken = result.AuthenticationResult.IdToken;

                // Extract simple display name from email
                const name = email.split("@")[0].replace(/[._]/g, " ");

                onLogin(name, email.trim(), idToken);
            } else {
                // Display specific error inside the card instead of alert()
                setError("Login failed. Please check your credentials and try again.");
            }
        } catch (err: any) {
            console.error("Login Error:", err);

            // Map common Cognito error types to readable messages
            if (err.__type === "NotAuthorizedException") {
                setError("Incorrect email or password.");
            } else if (err.__type === "UserNotFoundException") {
                setError("No account found with this email.");
            } else {
                setError(err.message || "An unexpected network error occurred.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="student-login-container">
            <div className="login-card">
                <h1>ClassBits</h1>
                <h2>Student Login</h2>

                {/* In-page error display - Styled identical to Instructor page */}
                {error && <p className="error-message">{error}</p>}

                {/* Wrapping in <form> enables 'Enter' key submission */}
                <form onSubmit={handleSubmit}>
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
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => {
                                setPassword(e.target.value);
                                if (error) setError(null);
                            }}
                            required
                        />
                    </div>

                    <button
                        className="submit-btn"
                        type="submit"
                        disabled={loading}
                    >
                        {loading ? "Signing in..." : "Sign In"}
                    </button>
                </form>

                {/* 🟢 Identity: Identical to Instructor LoginPage register-group */}
                <div className="register-group">
                    <label htmlFor="register">Don't have an account?</label>
                    <span
                        className="register"
                        onClick={() => navigate("/student/register")}
                    >
                        Register
                    </span>
                </div>
            </div>
        </div>
    );
};

export default StudentLoginForm;