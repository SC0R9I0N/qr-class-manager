import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../../api/auth";
import "./LoginPage.css";

const LoginPage: React.FC = () => {
    const navigate = useNavigate();

    // Form state
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // UI Feedback state
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        // Prevent default browser form refresh on Enter/Submit
        e.preventDefault();

        // Reset state before attempt
        setError(null);
        setLoading(true);

        try {
            const result = await loginUser(email.trim(), password.trim());

            if (result.AuthenticationResult) {
                const auth = result.AuthenticationResult;

                localStorage.setItem("accessToken", auth.AccessToken);
                localStorage.setItem("idToken", auth.IdToken);
                localStorage.setItem("refreshToken", auth.RefreshToken);

                // Clear login state and move to dashboard
                navigate("/dashboard");
            } else {
                // Display specific error inside the card instead of alert()
                setError("Login failed. Please check your credentials and try again.");
            }
        } catch (err: any) {
            console.error("Login Error:", err);
            setError(err.message || "An unexpected network error occurred.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="instructor-login-container">
            <div className="login-card">
                <h1>ClassBits</h1>
                <h2>Instructor Login</h2>

                {/* In-page error display */}
                {error && <p className="error-message">{error}</p>}

                {/* Wrapping in <form> enables 'Enter' to submit via the type="submit" button */}
                <form onSubmit={handleLogin}>
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
                        className="login-btn"
                        type="submit"
                        disabled={loading}
                    >
                        {loading ? "Logging in..." : "Login"}
                    </button>
                </form>

                <div className="register-group">
                    <label htmlFor="register">Don't have an account?</label>
                    <span
                        className="register"
                        onClick={() => navigate("/register")}
                    >
                        Register
                    </span>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;