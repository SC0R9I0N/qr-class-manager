import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerUser } from "../../api/auth";
import "./RegisterPage.css"

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
        <div className="instructor-register-container">

            <div className="register-card">
            <h1>ClassBits</h1>
            <h2>Instructor Account Creation</h2>

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
                    className="register-btn"
                    onClick={handleRegister}
                >
                    Register
                </button>
            </div>
        </div>
    );
};

export default RegisterPage;