import React from "react";
import { Link } from "react-router-dom";
import "./LandingPage.css";

const LandingPage: React.FC = () => {
  return (
    <div className="landing-container">
      <div className="landing-card">
        <h1>ClassBits</h1>
        <p>Select your role to continue:</p>
        <Link to="/student">
          <button className="landing-btn">Login as Student</button>
        </Link>
        <Link to="/instructor/login">
          <button className="landing-btn">Login as Instructor</button>
        </Link>
      </div>
    </div>
  );
};

export default LandingPage;