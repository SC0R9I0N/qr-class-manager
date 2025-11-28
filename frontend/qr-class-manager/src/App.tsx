import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Instructor Pages (Authenticated with Cognito)
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ConfirmPage from "./pages/ConfirmPage";
import LogoutPage from "./pages/LogoutPage";
import InstructorDashboard from "./pages/InstructorDashboard";
import ClassPage from "./pages/ClassPage";
import SessionPage from "./pages/SessionPage";
import UploadResourcePage from "./pages/UploadResourcePage";

// Student Pages (Pseudo-authentication only)
import StudentAttendancePage from "./pages/student/StudentAttendancePage";

const App: React.FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                {/* Student Routes - No Cognito Auth Required */}
                <Route path="/" element={<StudentAttendancePage />} />
                <Route path="/student" element={<StudentAttendancePage />} />
                <Route path="/attendance" element={<StudentAttendancePage />} />

                {/* Instructor Routes - Cognito Auth Required */}
                <Route path="/instructor/login" element={<LoginPage />} />
                <Route path="/instructor/register" element={<RegisterPage />} />
                <Route path="/instructor/confirm" element={<ConfirmPage />} />
                <Route path="/instructor/logout" element={<LogoutPage />} />
                <Route path="/instructor/dashboard" element={<InstructorDashboard />} />
                <Route path="/instructor/class/:id" element={<ClassPage />} />
                <Route path="/instructor/session/:id" element={<SessionPage />} />
                <Route path="/instructor/upload" element={<UploadResourcePage />} />

                {/* Legacy Routes (backward compatibility) */}
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