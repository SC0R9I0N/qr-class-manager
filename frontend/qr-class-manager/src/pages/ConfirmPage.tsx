import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CognitoConfirmSignUpResponse } from "../api/auth";
import { confirmUser } from "../api/auth";

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
        <div style={{ padding: 20 }}>
            <h1>Confirm Your Account</h1>
            <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ padding: 8, width: 250, marginBottom: 10 }}
            /><br />
            <input
                type="text"
                placeholder="Verification Code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                style={{ padding: 8, width: 250, marginBottom: 10 }}
            /><br />
            <button onClick={handleConfirm} style={{ padding: "8px 16px" }}>
                Confirm
            </button>
        </div>
    );
};

export default ConfirmPage;