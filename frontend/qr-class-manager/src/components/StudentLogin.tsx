import React, { useState } from "react";
import "./StudentLogin.css";

interface StudentLoginProps {
    onLogin: (studentName: string, studentEmail: string) => void;
}

const StudentLogin: React.FC<StudentLoginProps> = ({ onLogin }) => {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [error, setError] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!name.trim()) {
            setError("Please enter your full name");
            return;
        }
        
        if (!email.trim() || !email.includes("@")) {
            setError("Please enter a valid email address");
            return;
        }
        
        onLogin(name.trim(), email.trim());
    };

    return (
        <div className="student-login-container">
            <div className="login-card">
                <h1>ClassBits</h1>
                <h2>Student Attendance</h2>
                <p className="instruction">
                    Please enter your information to mark attendance
                </p>
                
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="name">Full Name</label>
                        <input
                            id="name"
                            type="text"
                            value={name}
                            onChange={(e) => {
                                setName(e.target.value);
                                setError("");
                            }}
                            placeholder="John Doe"
                            required
                        />
                    </div>
                    
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
                            placeholder="john.doe@university.edu"
                            required
                        />
                    </div>
                    
                    {error && <div className="error-message">{error}</div>}
                    
                    <button type="submit" className="submit-btn">
                        Continue
                    </button>
                </form>
            </div>
        </div>
    );
};

export default StudentLogin;
