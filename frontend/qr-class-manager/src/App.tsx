import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Landing Page (determine route to Instructor or Student login)
import LandingPage from "./pages/LandingPage.tsx";

// Instructor Pages (Authenticated with Cognito)
import LoginPage from "./pages/instructor/LoginPage";
import RegisterPage from "./pages/instructor/RegisterPage";
import ConfirmPage from "./pages/instructor/ConfirmPage";
import LogoutPage from "./pages/instructor/LogoutPage";
import InstructorDashboard from "./pages/instructor/InstructorDashboard";
import ClassPage from "./pages/instructor/ClassPage";
import SessionPage from "./pages/instructor/SessionPage";
import UploadResourcePage from "./pages/instructor/UploadResourcePage";

// Student Pages (Pseudo-authentication only)
import StudentAttendancePage from "./pages/student/StudentAttendancePage";
import StudentRegisterPage from "./pages/student/StudentRegisterPage";
import StudentConfirmPage from "./pages/student/StudentConfirmPage";

const App: React.FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                {/* Student Routes - No Cognito Auth Required */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/student" element={<StudentAttendancePage />} />
                <Route path="/attendance" element={<StudentAttendancePage />} />
                <Route path="/student/register" element={<StudentRegisterPage />} />
                <Route path="/student/confirm" element={<StudentConfirmPage />} />

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