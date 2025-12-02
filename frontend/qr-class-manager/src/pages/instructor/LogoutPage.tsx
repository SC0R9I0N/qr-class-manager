import React from "react";
import { useNavigate } from "react-router-dom";
import { logoutUser } from "../../api/auth";
import "./LogoutPage.css"

const LogoutPage: React.FC = () => {
    const navigate = useNavigate();

    const handleLogout = () => {
        logoutUser();
        navigate("/login");
    };

    return (
        <div className="logout-container">
            <div className="logout-card">
                <h1>Logout</h1>
                <button 
                    className="confirm-logout-btn"
                    onClick={handleLogout}
                >
                    Confirm Logout
                </button>
            </div>
        </div>
    );
};

export default LogoutPage;