import React, { useState } from "react";
import { loginUser } from "../../api/auth";
import "./StudentLoginForm.css";

interface StudentLoginFormProps {
    onLogin: (studentName: string, studentEmail: string, idToken: string) => void;
}

const StudentLoginForm: React.FC<StudentLoginFormProps> = ({ onLogin }) => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!email.trim() || !email.includes("@")) {
            setError("Please enter a valid email address");
            return;
        }
        
        if (!password.trim()) {
            setError("Please enter your password");
            return;
        }
        
        setLoading(true);
        setError("");

        try {
            // Authenticate with AWS Cognito using direct API
            const result = await loginUser(email.trim(), password.trim());

            if (result.AuthenticationResult) {
                const idToken = result.AuthenticationResult.IdToken;
                
                // Extract name from email (or you can decode the token to get attributes)
                const name = email.split("@")[0].replace(/[._]/g, " ");
                
                onLogin(name, email.trim(), idToken);
            } else {
                setError("Authentication failed. Please check your credentials.");
            }
        } catch (err: any) {
            console.error("Login error:", err);
            
            if (err.message?.includes("NotAuthorizedException") || err.__type === "NotAuthorizedException") {
                setError("Incorrect email or password");
            } else if (err.message?.includes("UserNotFoundException") || err.__type === "UserNotFoundException") {
                setError("User not found. Please check your email.");
            } else if (err.message?.includes("InvalidParameterException") || err.__type === "InvalidParameterException") {
                setError("Invalid email or password format");
            } else {
                setError(err.message || "Login failed. Please try again.");
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
                <p className="instruction">
                    Sign in to mark your attendance
                </p>
                
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="email">Email Address</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => {
                                setEmail(e.target.value);
                                setError("");
                            }}
                            placeholder="student1@example.com"
                            required
                            disabled={loading}
                        />
                    </div>
                    
                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => {
                                setPassword(e.target.value);
                                setError("");
                            }}
                            placeholder="Enter your password"
                            required
                            disabled={loading}
                        />
                    </div>
                    
                    {error && <div className="error-message">{error}</div>}
                    
                    <button type="submit" className="submit-btn" disabled={loading}>
                        {loading ? "Signing in..." : "Sign In"}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default StudentLoginForm;
