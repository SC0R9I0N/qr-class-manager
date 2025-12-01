import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../../api/auth";
import "./LoginPage.css";

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleLogin = async () => {
        const result = await loginUser(email, password);

        if (result.AuthenticationResult) {
            const auth = result.AuthenticationResult;

            localStorage.setItem("accessToken", auth.AccessToken);
            localStorage.setItem("idToken", auth.IdToken);
            localStorage.setItem("refreshToken", auth.RefreshToken);

            alert("Logged in!");
            navigate("/dashboard");
        } else {
            alert("Login error: " + JSON.stringify(result));
        }
    };

    return (
        <div className="instructor-login-container">
            

            <div className="login-card">
                <h1>ClassBits</h1>
                <h2>Instructor Login</h2>
                <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <input
                    id="email"
                    type="email"
                    placeholder="instructor1@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                </div>

                <div className="form-group">
                    <label htmlFor="password">Enter Password</label>
                <input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
                </div>

                <button
                    onClick={handleLogin}
                    className="login-btn"
                >
                    Login
                </button>

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