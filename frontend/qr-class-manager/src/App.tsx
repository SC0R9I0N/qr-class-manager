import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ConfirmPage from "./pages/ConfirmPage";
import LogoutPage from "./pages/LogoutPage";

import InstructorDashboard from "./pages/InstructorDashboard";
import ClassPage from "./pages/ClassPage";
import SessionPage from "./pages/SessionPage";
import UploadResourcePage from "./pages/UploadResourcePage";

const App: React.FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                
                <Route path="/" element={<LoginPage />} />

                
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/confirm" element={<ConfirmPage />} />
                <Route path="/logout" element={<LogoutPage />} />

                
                <Route path="/dashboard" element={<InstructorDashboard />} />
                <Route path="/class/:id" element={<ClassPage />} />
                <Route path="/session/:id" element={<SessionPage />} />
                <Route path="/upload" element={<UploadResourcePage />} />
            </Routes>
        </BrowserRouter>
    );
};

export default App;