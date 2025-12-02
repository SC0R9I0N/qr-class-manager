import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CognitoConfirmSignUpResponse } from "../../api/auth";
import { confirmUser } from "../../api/auth";
import "./ConfirmPage.css"

const ConfirmPage: React.FC = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [code, setCode] = useState("");

    const handleConfirm = async () => {
        const result: CognitoConfirmSignUpResponse = await confirmUser(email, code);

        // success response has NO "message"
        if (!result.message) {
            alert("Account confirmed! You may now log in.");
            navigate("/login");
        } else {
            alert("Error: " + result.message);
        }
    };

    return (
        <div className="instructor-confirm-container">
            <div className="intsructor-confirm-card">
                <h1>ClassBits</h1>
                <h2>Confirm Your Account</h2>
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
                    <label htmlFor="verification">Verification Code</label>
                    <input
                        id="verification"
                        type="text"
                        placeholder="Verification Code"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                    />
                </div>

                <button 
                    className="confirm-verification-btn" 
                    onClick={handleConfirm}
                >
                    Confirm
                </button>
            </div>
        </div>
    );
};

export default ConfirmPage;