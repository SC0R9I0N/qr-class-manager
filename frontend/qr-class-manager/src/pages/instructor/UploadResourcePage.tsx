import React, { useState, useEffect } from "react";
import { fetchSessions, type Session } from "../../api/sessions";
import { uploadMaterialsZip } from "../../api/materials";
import "./UploadResourcePage.css"

const UploadResourcePage: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [status, setStatus] = useState<string | null>(null);
    const [isError, setIsError] = useState<boolean>(false);

    const [sessions, setSessions] = useState<Session[]>([]);
    const [selectedSessionId, setSelectedSessionId] = useState<string>("");

    const currentClassId = "CS100";

    useEffect(() => {
        const loadSessions = async () => {
            try {
                const data = await fetchSessions(currentClassId);
                setSessions(data);
            } catch (e) {
                setStatus("Failed to load sessions for this class.");
                setIsError(true);
            }
        };
        loadSessions();
    }, [currentClassId]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selected = e.target.files?.[0] || null;
        setFile(selected);
        setStatus(null); // Clear status when new file is chosen
        setIsError(false);
    };

    const handleUpload = async () => {
        if (!file || !selectedSessionId) {
            setStatus("Please select a session and a .zip file.");
            setIsError(true);
            return;
        }

        try {
            setStatus("Uploading...");
            setIsError(false);

            await uploadMaterialsZip(file, selectedSessionId);

            setStatus("Upload successful!");
            setFile(null);
            // Optionally clear file input field manually via ref if needed
        } catch (e) {
            setStatus(`Upload failed: ${(e as Error).message}`);
            setIsError(true);
        }
    };

    return (
        <div className="upload-container">
            <div className="upload-card">
                <h1>Upload Course Materials</h1>

                <select
                    className="session-select"
                    value={selectedSessionId}
                    onChange={(e) => setSelectedSessionId(e.target.value)}
                >
                    <option value="">-- Select Target Session --</option>
                    {sessions.map((s) => (
                        <option key={s.session_id} value={s.session_id}>
                            {s.title || `${s.date}`}
                        </option>
                    ))}
                </select>

                <input
                    className="file-input"
                    type="file"
                    accept=".zip"
                    onChange={handleFileChange}
                />

                <button
                    className="upload-class-btn"
                    onClick={handleUpload}
                    disabled={!selectedSessionId || !file || status === "Uploading..."}
                >
                    {status === "Uploading..." ? "Uploading..." : "Upload ZIP"}
                </button>

                {/* Renders the success or error message here */}
                {status && (
                    <p className={`status-msg ${isError ? "error" : "success"}`}>
                        {status}
                    </p>
                )}
            </div>
        </div>
    );
};

export default UploadResourcePage;