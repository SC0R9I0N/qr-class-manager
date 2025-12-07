import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerUser } from "../../api/auth";
import "./RegisterPage.css"

const RegisterPage: React.FC = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // UI Feedback state
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleRegister = async (e: React.FormEvent) => {
        // Prevent default browser refresh
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const result = await registerUser(email.trim(), password.trim());

            if (result.UserConfirmed === false) {
                navigate("/confirm");
            } else {
                setError("Registration encountered an unexpected issue.");
            }
        } catch (err: any) {
            console.error("Registration Error:", err);
            setError(err.message || "Registration failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="instructor-register-container">
            <div className="register-card">
                <h1>ClassBits</h1>
                <h2>Instructor Account Creation</h2>

                {/* In-page error display */}
                {error && <p className="error-message">{error}</p>}

                <form onSubmit={handleRegister}>
                    <div className="form-group">
                        <label htmlFor="email">Email Address</label>
                        <input
                            id="email"
                            type="email"
                            placeholder="instructor1@example.com"
                            value={email}
                            onChange={(e) => {
                                setEmail(e.target.value);
                                if (error) setError(null);
                            }}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Enter Password</label>
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
                        className="register-btn"
                        type="submit"
                        disabled={loading}
                    >
                        {loading ? "Creating Account..." : "Register"}
                    </button>
                </form>

                {/* 🟢 NEW: Back to Login button to match Student page */}
                <button
                    className="back-btn"
                    onClick={() => navigate("/instructor/login")}
                >
                    Back to Login
                </button>
            </div>
        </div>
    );
};

export default RegisterPage;