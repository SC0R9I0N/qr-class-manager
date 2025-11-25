import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../api/auth";

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
        <div style={{ padding: 20 }}>
            <h1>Login</h1>

            <div style={{ marginTop: 20 }}>
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    style={{ padding: 8, width: 250, marginBottom: 10 }}
                />
                <br />

                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{ padding: 8, width: 250, marginBottom: 10 }}
                />
                <br />

                <button
                    onClick={handleLogin}
                    style={{ padding: "8px 16px", cursor: "pointer" }}
                >
                    Login
                </button>

                
                <p style={{ marginTop: 15 }}>
                    Don't have an account?{" "}
                    <span
                        onClick={() => navigate("/register")}
                        style={{ color: "blue", cursor: "pointer", textDecoration: "underline" }}
                    >
                        Register
                    </span>
                </p>
            </div>
        </div>
    );
};

export default LoginPage;