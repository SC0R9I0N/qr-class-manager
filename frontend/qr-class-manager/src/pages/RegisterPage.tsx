import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerUser } from "../api/auth";

const RegisterPage: React.FC = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleRegister = async () => {
        const result = await registerUser(email, password);

        if (result.UserConfirmed === false) {
            alert("Account created! Check your email for verification.");
            navigate("/confirm");
        } else {
            alert("Registration error: " + JSON.stringify(result));
        }
    };

    return (
        <div style={{ padding: 20 }}>
            <h1>Create Account</h1>

            <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ padding: 8, width: 250, marginBottom: 10 }}
            /><br />

            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ padding: 8, width: 250, marginBottom: 10 }}
            /><br />

            <button onClick={handleRegister} style={{ padding: "8px 16px" }}>
                Register
            </button>
        </div>
    );
};

export default RegisterPage;