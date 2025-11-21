import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import InstructorDashboard from "./pages/InstructorDashboard";
//import ClassPage from "./pages/ClassPage";
//import SessionPage from "./pages/SessionPage";
import UploadResourcePage from "./pages/UploadResourcePage";

const App: React.FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<InstructorDashboard />} />


                <Route path="/upload" element={<UploadResourcePage />} />
            </Routes>
        </BrowserRouter>
    );
};

export default App;