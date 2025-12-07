import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerUser } from "../../api/auth";
import "./StudentRegisterPage.css";

const StudentRegisterPage: React.FC = () => {
    const navigate = useNavigate();

    // Form state
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // UI Feedback state
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleRegister = async (e: React.FormEvent) => {
        // Prevent default browser form refresh
        e.preventDefault();

        // Reset state before attempt
        setError(null);
        setLoading(true);

        try {
            // Call existing registerUser API helper
            await registerUser(email.trim(), password.trim());

            // Inform user and redirect
            alert("Registration successful! Please check your email for confirmation before logging in.");
            navigate("/student/confirm");
        } catch (err: any) {
            console.error("Registration Error:", err);
            setError(err.message || "Registration failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="student-register-container">
            <div className="register-card">
                <h1>ClassBits</h1>
                <h2>Student Registration</h2>

                {/* In-page error display */}
                {error && <p className="error-message">{error}</p>}

                <form onSubmit={handleRegister}>
                    <div className="form-group">
                        <label htmlFor="email">Email Address</label>
                        <input
                            id="email"
                            type="email"
                            placeholder="student1@example.com" // 🟢 Added placeholder
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
                            placeholder="Enter your password" // 🟢 Added placeholder
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
                        {loading ? "Creating Account..." : "Register"}
                    </button>
                </form>

                <button
                    className="back-btn"
                    onClick={() => navigate(-1)}
                >
                    Back to Login
                </button>
            </div>
        </div>
    );
};

export default StudentRegisterPage;