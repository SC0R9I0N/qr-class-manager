import React from "react";
import { useNavigate } from "react-router-dom";
import { logoutUser } from "../api/auth";

const LogoutPage: React.FC = () => {
    const navigate = useNavigate();

    const handleLogout = () => {
        logoutUser();
        navigate("/login");
    };

    return (
        <div style={{ padding: 20 }}>
            <h1>Logout</h1>
            <button onClick={handleLogout} style={{ padding: "10px 20px" }}>
                Confirm Logout
            </button>
        </div>
    );
};

export default LogoutPage;